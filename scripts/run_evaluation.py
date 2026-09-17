#!/usr/bin/env python3
"""Score cached responses and report hallucination rates per dimension and the H-Score.

Item scores are cached in ``<output-dir>/<model>/scores/<task id>.jsonl`` so judge calls are made
once; the summary is written to ``<output-dir>/<model>/summary.json``.

Example:
    python scripts/run_evaluation.py --model gpt-4o
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prism.config import load_judge_config  # noqa: E402
from prism.data import load_task, read_jsonl, write_jsonl  # noqa: E402
from prism.evaluators import needs_judge, score_item  # noqa: E402
from prism.judge import Judge  # noqa: E402
from prism.metrics import dimension_rates, h_score, task_score  # noqa: E402
from prism.tasks import DIMENSIONS, select_tasks  # noqa: E402

logger = logging.getLogger("evaluation")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, help="name of the response directory under --output-dir")
    parser.add_argument("--tasks", nargs="*", default=None)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--model-config", default=None, help="registry holding the `judge` entry")
    parser.add_argument("--workers", type=int, default=20, help="parallel judge requests")
    parser.add_argument("--rescore", action="store_true", help="ignore cached item scores")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    root = Path(args.output_dir) / args.model
    tasks = select_tasks(args.tasks)
    judge = Judge(load_judge_config(args.model_config)) if any(needs_judge(t) for t in tasks) else None
    scores = {}
    for task in tasks:
        response_path = root / "responses" / f"{task.task_id}.jsonl"
        if not response_path.exists():
            logger.warning("%s: no responses at %s", task.task_id, response_path)
            continue
        records = {r["id"]: r for r in load_task(task, args.data_dir)}
        responses = {r["id"]: r.get("response") for r in read_jsonl(response_path)}
        score_path = root / "scores" / f"{task.task_id}.jsonl"
        cached = {r["id"]: r for r in read_jsonl(score_path)} if score_path.exists() and not args.rescore else {}
        todo = [i for i in records if i not in cached]

        def evaluate(item_id):
            result = score_item(task, records[item_id], responses.get(item_id), judge)
            return {"id": item_id, "task": task.task_id, "score": result.score, **result.detail}

        if todo:
            workers = args.workers if needs_judge(task) else 1
            with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
                for row in pool.map(evaluate, todo):
                    cached[row["id"]] = row
        rows = [cached[i] for i in records]
        write_jsonl(score_path, rows)
        scores[task.task_id] = task_score(row["score"] for row in rows)
        logger.info("%s: S = %.2f (n=%d)", task.task_id, scores[task.task_id], len(rows))

    rates = dimension_rates(scores)
    summary = {"model": args.model, "judge": judge.name if judge else None,
               "task_scores": scores, "dimension_hallucination_rates": rates}
    if set(rates) == set(DIMENSIONS):
        summary["h_score"] = h_score(rates)
    (root / "summary.json").parent.mkdir(parents=True, exist_ok=True)
    (root / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{args.model}")
    for dim, name in DIMENSIONS.items():
        if dim in rates:
            print(f"  {dim:4} {name:30} H = {rates[dim]:6.2f}%")
    if "h_score" in summary:
        print(f"  {'H-Score':35} {summary['h_score']:6.2f}%")


if __name__ == "__main__":
    main()
