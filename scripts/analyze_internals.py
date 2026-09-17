#!/usr/bin/env python3
"""Measure the internal states behind the discussion section of the paper.

For a locally loaded model the script runs the PRISM prompts, then computes per response:
the number of MLP neurons that fire, the concentration of the attention distributions, and the
floating-point operations of the forward pass. Results are grouped into refusals and non-refusals.
With ``--attention-map`` it also stores the layer-averaged attention matrix of single items and
renders it as a heat map.

Examples:
    python scripts/analyze_internals.py --model-path $LOCAL_MODEL_PATH --tasks IFE --limit 50 \
        --report reports/internals_qwen3-4b.json
    python scripts/analyze_internals.py --model-path $LOCAL_MODEL_PATH --attention-map KE-EIC-SelfBuilt-0001 \
        KM-TK-Numeric-0001 --output-dir reports/attention
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prism.data import load_task  # noqa: E402
from prism.internals import active_neurons, attention_sparsity, forward_flops, is_refusal, summarize  # noqa: E402
from prism.prompts import build_prompt  # noqa: E402
from prism.tasks import TASKS, select_tasks  # noqa: E402

logger = logging.getLogger("internals")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model-path", required=True, help="Hugging Face id or local path of the model")
    parser.add_argument("--tasks", nargs="*", default=["IFE"], help="task ids or prefixes to analyse")
    parser.add_argument("--limit", type=int, default=50, help="items per task")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-p", type=float, default=0.8)
    parser.add_argument("--activation-threshold", type=float, default=0.0)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--report", default=None, help="write the grouped means to this JSON file")
    parser.add_argument("--attention-map", nargs="*", default=None, help="item ids whose attention map to store")
    parser.add_argument("--output-dir", default="reports/attention")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


class Recorder:
    """Loads the model and records activations and attention of one forward pass."""

    def __init__(self, model_path: str, seed: int) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

        set_seed(seed)
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path, torch_dtype=torch.bfloat16, trust_remote_code=True,
            attn_implementation="eager",  # required to return the attention weights
            device_map="auto" if torch.cuda.is_available() else None)
        self.model.eval()
        config = self.model.config
        self.layers = int(getattr(config, "num_hidden_layers"))
        self.hidden = int(getattr(config, "hidden_size"))
        embedding = self.model.get_input_embeddings().weight.numel()
        self.non_embedding_parameters = sum(p.numel() for p in self.model.parameters()) - embedding

    def chat_prompt(self, prompt: str) -> str:
        if self.tokenizer.chat_template:
            return self.tokenizer.apply_chat_template([{"role": "user", "content": prompt}],
                                                      tokenize=False, add_generation_prompt=True)
        return prompt

    def generate(self, prompt: str, max_new_tokens: int, temperature: float, top_p: float) -> str:
        inputs = self.tokenizer(self.chat_prompt(prompt), return_tensors="pt").to(self.model.device)
        with self.torch.no_grad():
            output = self.model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=temperature > 0,
                                         temperature=temperature, top_p=top_p,
                                         pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id)
        return self.tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    def record(self, text: str):
        """Return (activations per layer, attention per layer, number of tokens) for one forward pass."""
        activations = []
        handles = []

        def hook(_module, _inputs, output):
            activations.append(output.detach().float().cpu().numpy()[0])

        for layer in self.model.model.layers:
            handles.append(layer.mlp.act_fn.register_forward_hook(hook))
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
        try:
            with self.torch.no_grad():
                out = self.model(**inputs, output_attentions=True, use_cache=False)
        finally:
            for handle in handles:
                handle.remove()
        attentions = [a.detach().float().cpu().numpy()[0] for a in out.attentions]
        return activations, attentions, int(inputs["input_ids"].shape[1])


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    recorder = Recorder(args.model_path, args.seed)

    if args.attention_map:
        wanted = set(args.attention_map)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for task in TASKS:
            records = [r for r in load_task(task, args.data_dir) if r["id"] in wanted]
            for record in records:
                prompt = build_prompt(record, task)
                response = recorder.generate(prompt, args.max_new_tokens, args.temperature, args.top_p)
                _, attentions, tokens = recorder.record(recorder.chat_prompt(prompt) + response)
                averaged = np.mean([a.mean(axis=0) for a in attentions], axis=0)
                np.save(output_dir / f"{record['id']}.npy", averaged)
                try:
                    import matplotlib

                    matplotlib.use("Agg")
                    import matplotlib.pyplot as plt

                    figure, axis = plt.subplots(figsize=(4.5, 4))
                    image = axis.imshow(averaged, cmap="viridis")
                    axis.set_xlabel("key position")
                    axis.set_ylabel("query position")
                    axis.set_title(record["id"], fontsize=9)
                    figure.colorbar(image, ax=axis, shrink=0.8)
                    figure.tight_layout()
                    figure.savefig(output_dir / f"{record['id']}.png", dpi=200)
                    plt.close(figure)
                except ImportError:
                    pass
                logger.info("%s: attention map over %d tokens", record["id"], tokens)
        return

    measurements = []
    for task in select_tasks(args.tasks):
        for record in load_task(task, args.data_dir)[: args.limit]:
            prompt = build_prompt(record, task)
            response = recorder.generate(prompt, args.max_new_tokens, args.temperature, args.top_p)
            activations, attentions, tokens = recorder.record(recorder.chat_prompt(prompt) + response)
            measurements.append({
                "id": record["id"], "task": task.task_id, "refusal": is_refusal(response), "tokens": tokens,
                "active_neurons_m": active_neurons(activations, args.activation_threshold),
                "attention_sparsity": attention_sparsity(attentions),
                "gflops": forward_flops(recorder.non_embedding_parameters, tokens, recorder.layers, recorder.hidden),
            })
            logger.info("%s: tokens=%d refusal=%s", record["id"], tokens, measurements[-1]["refusal"])

    groups = {"non_refusal": summarize([m for m in measurements if not m["refusal"]]),
              "refusal": summarize([m for m in measurements if m["refusal"]])}
    report = {"model": args.model_path, "items": len(measurements), "groups": groups}
    print(json.dumps(report, indent=2))
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps({**report, "measurements": measurements}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
