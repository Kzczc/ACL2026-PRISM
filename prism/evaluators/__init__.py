"""Item-level scoring for all PRISM tasks.

``score_item`` returns a score in [0, 1]: 1/0 for closed-ended tasks, the rubric total divided by 5
for code generation, and one minus the claim-level hallucination rate for information integration.
Empty or failed responses score 0.
"""

from __future__ import annotations

import csv
import io
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..client import is_failed
from ..prompts import format_question
from ..tasks import Task
from . import ifeval
from .matching import (abstained, contains_reference, exact_match, extract_choice, fuzzy_match, truth_label,
                       yes_no)

JUDGE_EVALUATORS = frozenset({"fact_judge", "judge_equiv", "answer_match", "judge_math", "judge_code", "judge_claims"})


@dataclass
class ItemScore:
    score: float
    detail: Dict[str, Any] = field(default_factory=dict)


def needs_judge(task: Task) -> bool:
    return task.evaluator in JUDGE_EVALUATORS


def _data_format_ok(response: str, fmt: str) -> bool:
    text = response.strip()
    fmt = fmt.upper()
    try:
        if fmt == "JSON":
            json.loads(text)
            return True
        if fmt == "XML":
            ET.fromstring(text)
            return True
        if fmt == "CSV":
            rows = list(csv.reader(io.StringIO(text)))
            rows = [r for r in rows if r]
            return len(rows) >= 2 and len(rows[0]) >= 2 and all(len(r) == len(rows[0]) for r in rows)
        if fmt in ("YAML", "GENERAL"):
            import yaml

            return isinstance(yaml.safe_load(text), (dict, list))
        if fmt == "MARKDOWN":
            return bool(re.search(r"^#+\s+\S", text, re.MULTILINE)
                        or re.search(r"^\s*[-*]\s+\S", text, re.MULTILINE)
                        or ifeval.count_highlights(text) > 0)
    except Exception:
        return False
    raise ValueError(f"unknown data format {fmt!r}")


def score_item(task: Task, record: Dict[str, Any], response: Optional[str], judge=None) -> ItemScore:
    if is_failed(response):
        return ItemScore(0.0, {"failed_response": True})
    response = str(response)
    kind = task.evaluator
    if needs_judge(task) and judge is None and kind not in ("fact_judge", "answer_match"):
        raise RuntimeError(f"task {task.task_id} requires an LLM judge")

    if kind == "exact":
        return ItemScore(float(exact_match(response, record["answer"])))
    if kind == "fuzzy":
        return ItemScore(float(fuzzy_match(response, record["answer"])))
    if kind == "choice":
        letters = "ABCDEFGH"[: max(4, len(record.get("options") or []))]
        chosen = extract_choice(response, letters)
        return ItemScore(float(chosen == str(record["answer"]).strip().upper()), {"extracted": chosen})
    if kind == "abstain":
        return ItemScore(float(abstained(response)))
    if kind == "truth_label":
        label = truth_label(response)
        return ItemScore(float(label == record["answer"]), {"label": label})
    if kind == "fact_judge":
        ref, pred = yes_no(record["answer"]), yes_no(response)
        if ref is not None and ref == pred:
            return ItemScore(1.0, {"rule": "yes_no"})
        if judge is None:
            raise RuntimeError(f"task {task.task_id} requires an LLM judge")
        result = judge.equivalent(response, str(record["answer"]))
        return ItemScore(float(result["correct"]), result)
    if kind == "judge_equiv":
        result = judge.equivalent(response, str(record["answer"]))
        return ItemScore(float(result["correct"]), result)
    if kind == "answer_match":
        if abstained(response):
            return ItemScore(0.0, {"abstained": True})
        if contains_reference(response, record["answer"]):
            return ItemScore(1.0, {"rule": "match"})
        if judge is None:
            raise RuntimeError(f"task {task.task_id} requires an LLM judge")
        result = judge.equivalent(response, str(record["answer"]))
        return ItemScore(float(result["correct"]), result)
    if kind == "judge_math":
        result = judge.math_equivalent(record["question"], str(record["answer"]), response)
        return ItemScore(float(result["correct"]), result)
    if kind == "judge_code":
        result = judge.code_score(record["question"], record.get("test_input", ""), record.get("test_output", ""), response)
        return ItemScore(result["total"] / 5.0, result)
    if kind == "judge_claims":
        result = judge.claim_hallucination(task.task_id, format_question(record, task), response)
        return ItemScore(1.0 - result["hallucination_rate"], result)
    if kind == "data_format":
        return ItemScore(float(_data_format_ok(response, record["format"])))
    if kind == "word_range":
        low, high = record["word_range"]
        words = len(response.split())
        return ItemScore(float(low <= words <= high), {"words": words})
    if kind == "language":
        detected = ifeval.detect_language(response)
        return ItemScore(float(detected == ifeval.normalize_language(record["language"])), {"detected": detected})
    if kind == "ifeval":
        instructions = ifeval.item_instructions(record["instruction_id"], record.get("kwargs") or [])
        ok, failed = ifeval.follows_all(response, instructions)
        return ItemScore(float(ok), {"failed_instructions": failed} if failed else {})
    raise ValueError(f"unknown evaluator {kind!r}")
