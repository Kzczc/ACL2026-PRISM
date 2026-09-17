#!/usr/bin/env python3
"""Render Markdown tables from the summaries of one or more evaluated models.

Example:
    python scripts/make_tables.py --models gpt-4o deepseek-v3.2 --report reports/results.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prism.tasks import DIMENSIONS, SUBCATEGORIES, TASKS  # noqa: E402


def markdown_table(header, rows) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--report", default=None)
    args = parser.parse_args()

    summaries = {}
    for model in args.models:
        path = Path(args.output_dir) / model / "summary.json"
        if not path.exists():
            raise FileNotFoundError(f"{path} not found; run scripts/run_evaluation.py first")
        summaries[model] = json.loads(path.read_text(encoding="utf-8"))

    main_rows = []
    for model, summary in summaries.items():
        rates = summary["dimension_hallucination_rates"]
        row = [model] + [f"{rates[d]:.2f}%" if d in rates else "-" for d in DIMENSIONS]
        row.append(f"{summary['h_score']:.2f}%" if "h_score" in summary else "-")
        main_rows.append(row)
    sections = ["## Hallucination rates (lower is better)\n",
                markdown_table(["Model", *DIMENSIONS, "H-Score"], main_rows)]

    for dim, name in DIMENSIONS.items():
        tasks = [t for t in TASKS if t.dimension == dim]
        header = ["Model"] + [f"{t.subcategory}_{t.name}" for t in tasks]
        rows = []
        for model, summary in summaries.items():
            scores = summary["task_scores"]
            rows.append([model] + [f"{scores[t.task_id]:.2f}" if t.task_id in scores else "-" for t in tasks])
        sections.append(f"\n## {name} ({dim}) sub-task scores S\n")
        sections.append(markdown_table(header, rows))

    text = "\n".join(sections)
    print(text)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(text + "\n", encoding="utf-8")
        json_path = Path(args.report).with_suffix(".json")
        json_path.write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
