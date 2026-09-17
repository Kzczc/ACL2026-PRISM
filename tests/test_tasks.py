import json
from pathlib import Path

import pytest

from prism.data import data_dir, read_jsonl
from prism.tasks import DIMENSIONS, SUBCATEGORIES, TASKS, get_task, select_tasks

# Section 2.3 of the paper: 9,448 instances over 65 sub-tasks.
DIMENSION_ITEMS = {"KE": 1933, "KM": 2078, "RE": 2995, "IFE": 2442}
DIMENSION_TASKS = {"KE": 15, "KM": 22, "RE": 10, "IFE": 18}

REQUIRED_FIELDS = {
    "exact": ("answer",), "fuzzy": ("answer",), "fact_judge": ("answer",), "judge_equiv": ("answer",),
    "answer_match": ("answer",), "judge_math": ("answer",), "truth_label": ("answer",), "abstain": ("answer",),
    "choice": ("answer", "options"), "judge_code": ("test_input", "test_output"), "judge_claims": (),
    "data_format": ("format",), "word_range": ("word_range",), "language": ("language",),
    "ifeval": ("instruction_id", "kwargs"),
}


def test_registry_shape():
    assert len(TASKS) == 65
    assert sorted(t.index for t in TASKS) == list(range(1, 66))
    assert len({t.task_id for t in TASKS}) == 65
    for dim, count in DIMENSION_TASKS.items():
        assert len([t for t in TASKS if t.dimension == dim]) == count
    for task in TASKS:
        assert SUBCATEGORIES[task.subcategory][0] == task.dimension
        assert task.evaluator in REQUIRED_FIELDS


def test_lookup():
    assert get_task("KE-FD-TruthfulQA").index == 23
    assert {t.task_id for t in select_tasks(["RE-LF"])} == {
        "RE-LF-Critical_Reasoning", "RE-LF-Contextual_Inference", "RE-LF-Cognitive_Traps"}
    assert len(select_tasks(None)) == 65
    with pytest.raises(KeyError):
        get_task("KE-FD-Nothing")


def _data_available() -> bool:
    return (data_dir() / TASKS[0].data_file).exists()


@pytest.mark.skipif(not _data_available(), reason="data files not present")
def test_data_files_match_the_paper():
    totals = dict.fromkeys(DIMENSIONS, 0)
    for task in TASKS:
        records = list(read_jsonl(data_dir() / task.data_file))
        assert records, task.task_id
        assert len({r["id"] for r in records}) == len(records)
        totals[task.dimension] += len(records)
        for record in records:
            assert record["task"] == task.task_id
            assert str(record["question"]).strip()
            for field in REQUIRED_FIELDS[task.evaluator]:
                assert field in record, (task.task_id, record["id"], field)
    assert totals == DIMENSION_ITEMS
    assert sum(totals.values()) == 9448


@pytest.mark.skipif(not _data_available(), reason="data files not present")
def test_task_registry_file():
    registry = json.loads((data_dir() / "tasks.json").read_text(encoding="utf-8"))
    assert [row["task_id"] for row in registry] == [t.task_id for t in TASKS]
    assert sum(row["items"] for row in registry) == 9448
