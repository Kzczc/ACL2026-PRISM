#!/usr/bin/env python3
"""LoRA supervised fine-tuning on a reasoning dataset, used for the mitigation study of the paper.

The paper fine-tunes on gsm8k-reasoning; the adapter can be merged into the base weights so that the
resulting model is served like any other model in configs/models.yaml.

Example:
    python scripts/train_reasoning_lora.py --base-model $SFT_BASE_MODEL --output-dir runs/llama31-8b-reasoning --merge
    vllm serve runs/llama31-8b-reasoning/merged --served-model-name llama-3.1-8b-reasoning
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

logger = logging.getLogger("train")

PROMPT_FIELDS = (("question", "answer"), ("prompt", "completion"), ("instruction", "output"), ("input", "output"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-model", default=os.environ.get("SFT_BASE_MODEL"),
                        help="Hugging Face id or local path of the base model ($SFT_BASE_MODEL)")
    parser.add_argument("--dataset", default="thesven/gsm8k-reasoning", help="reasoning dataset to fine-tune on")
    parser.add_argument("--split", default="train")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--target-modules", nargs="+",
                        default=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--merge", action="store_true", help="also write the adapter merged into the base weights")
    return parser.parse_args()


def field_names(columns) -> tuple:
    for prompt, answer in PROMPT_FIELDS:
        if prompt in columns and answer in columns:
            return prompt, answer
    raise KeyError(f"cannot find a prompt/answer pair in {sorted(columns)}; adapt PROMPT_FIELDS")


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not args.base_model:
        raise SystemExit("set --base-model or $SFT_BASE_MODEL")

    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model
    from transformers import (AutoModelForCausalLM, AutoTokenizer, DataCollatorForSeq2Seq, Trainer,
                              TrainingArguments, set_seed)

    set_seed(args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    raw = load_dataset(args.dataset, split=args.split)
    prompt_field, answer_field = field_names(raw.column_names)
    logger.info("dataset %s: %d rows, fields %s -> %s", args.dataset, len(raw), prompt_field, answer_field)

    def encode(example):
        messages = [{"role": "user", "content": str(example[prompt_field])}]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True) \
            if tokenizer.chat_template else f"{example[prompt_field]}\n"
        answer = str(example[answer_field]).strip() + (tokenizer.eos_token or "")
        prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
        answer_ids = tokenizer(answer, add_special_tokens=False)["input_ids"]
        input_ids = (prompt_ids + answer_ids)[: args.max_length]
        labels = ([-100] * len(prompt_ids) + answer_ids)[: args.max_length]  # train on the answer only
        return {"input_ids": input_ids, "labels": labels, "attention_mask": [1] * len(input_ids)}

    dataset = raw.map(encode, remove_columns=raw.column_names, desc="tokenizing")

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model, torch_dtype=torch.bfloat16, trust_remote_code=True,
        device_map="auto" if torch.cuda.device_count() > 1 else None)
    model.config.use_cache = False
    model = get_peft_model(model, LoraConfig(
        r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=args.lora_dropout,
        target_modules=args.target_modules, bias="none", task_type="CAUSAL_LM"))
    model.print_trainable_parameters()

    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=args.output_dir, num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size, gradient_accumulation_steps=args.grad_accum,
            learning_rate=args.learning_rate, lr_scheduler_type="cosine", warmup_ratio=args.warmup_ratio,
            logging_steps=10, save_strategy="epoch", bf16=torch.cuda.is_available(),
            gradient_checkpointing=True, report_to=[], seed=args.seed),
        train_dataset=dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer, padding=True, label_pad_token_id=-100),
    )
    trainer.train()
    adapter_dir = Path(args.output_dir) / "adapter"
    trainer.model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    logger.info("adapter written to %s", adapter_dir)

    if args.merge:
        merged = trainer.model.merge_and_unload()
        merged_dir = Path(args.output_dir) / "merged"
        merged.save_pretrained(merged_dir, safe_serialization=True)
        tokenizer.save_pretrained(merged_dir)
        logger.info("merged model written to %s", merged_dir)


if __name__ == "__main__":
    main()
