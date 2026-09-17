#!/usr/bin/env python3
"""Print the 65 PRISM sub-tasks with their sizes, prompts, and evaluators."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prism.data import data_dir, read_jsonl  # noqa: E402
from prism.tasks import DIMENSIONS, SUBCATEGORIES, TASKS  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=None)
    args = parser.parse_args()

    print(f"{'#':>3}  {'task id':38} {'sub-category':32} {'prompt':26} {'evaluator':12} {'items':>6}")
    totals = {d: 0 for d in DIMENSIONS}
    for task in TASKS:
        path = data_dir(args.data_dir) / task.data_file
        count = sum(1 for _ in read_jsonl(path)) if path.exists() else 0
        totals[task.dimension] += count
        print(f"{task.index:>3}  {task.task_id:38} {SUBCATEGORIES[task.subcategory][1]:32} "
              f"{task.prompt:26} {task.evaluator:12} {count:>6}")
    print()
    for dim, name in DIMENSIONS.items():
        print(f"{dim:>4} {name:30} {totals[dim]:>6}")
    print(f"{'total':>35} {sum(totals.values()):>6}")


if __name__ == "__main__":
    main()
