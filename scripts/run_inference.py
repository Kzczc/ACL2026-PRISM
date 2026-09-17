#!/usr/bin/env python3
"""Query a model on PRISM tasks and store its responses.

Each request contains the task prompt followed by the question, with the sampling parameters of
Section 3.1. Responses are written to ``<output-dir>/<model>/responses/<task id>.jsonl`` and an
interrupted run resumes from that file.

Example:
    python scripts/run_inference.py --model gpt-4o --tasks KE RE-LF
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prism.client import ChatClient, is_failed  # noqa: E402
from prism.config import load_model_config  # noqa: E402
from prism.data import load_task, read_jsonl, write_jsonl  # noqa: E402
from prism.prompts import build_prompt  # noqa: E402
from prism.sampling import sampling_params  # noqa: E402
from prism.tasks import select_tasks  # noqa: E402

logger = logging.getLogger("inference")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, help="model key in configs/models.yaml")
    parser.add_argument("--tasks", nargs="*", default=None, help="task ids or prefixes (default: all 65)")
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--model-config", default=None)
    parser.add_argument("--limit", type=int, default=None, help="first N items per task (smoke test)")
    parser.add_argument("--batch-size", type=int, default=200)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    config = load_model_config(args.model, args.model_config)
    client = ChatClient(config)
    for task in select_tasks(args.tasks):
        records = load_task(task, args.data_dir)
        if args.limit:
            records = records[: args.limit]
        path = Path(args.output_dir) / args.model / "responses" / f"{task.task_id}.jsonl"
        done = {r["id"] for r in read_jsonl(path) if not is_failed(r.get("response"))} if path.exists() else set()
        todo = [r for r in records if r["id"] not in done]
        logger.info("%s | %s: %d items, %d cached, %d to run", args.model, task.task_id, len(records), len(done), len(todo))
        params = sampling_params(task)
        for start in range(0, len(todo), args.batch_size):
            batch = todo[start: start + args.batch_size]
            responses = client.complete_many([build_prompt(r, task) for r in batch], **params)
            write_jsonl(path, ({"id": r["id"], "task": task.task_id, "response": text}
                               for r, text in zip(batch, responses)), append=True)
            failed = sum(1 for text in responses if is_failed(text))
            logger.info("%s: %d/%d written (%d failed)", task.task_id,
                        min(start + len(batch), len(todo)), len(todo), failed)


if __name__ == "__main__":
    main()
