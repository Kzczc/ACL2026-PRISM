"""Hallucination rates and the H-Score (Section 3.1 of the paper).

Each sub-task receives a score S in [0, 100] (100 x accuracy for closed-ended tasks, 100 x s / 5 for
LLM-Eval tasks), its hallucination rate is H = 100 - S, the rate of a dimension is the macro average
over its sub-tasks, and the H-Score is the mean of the four dimension rates.
"""

from __future__ import annotations

from typing import Dict, Iterable, Mapping

from .tasks import DIMENSIONS, TASKS


def task_score(item_scores: Iterable[float]) -> float:
    values = list(item_scores)
    if not values:
        raise ValueError("no item scores")
    return 100.0 * sum(values) / len(values)


def dimension_rates(task_scores: Mapping[str, float], require_complete: bool = True) -> Dict[str, float]:
    """Macro-averaged hallucination rate per dimension from sub-task scores S (keyed by task id)."""
    rates: Dict[str, float] = {}
    for dim in DIMENSIONS:
        ids = [t.task_id for t in TASKS if t.dimension == dim]
        present = [task_scores[i] for i in ids if i in task_scores]
        if not present:
            continue
        if require_complete and len(present) != len(ids):
            continue
        rates[dim] = 100.0 - sum(present) / len(present)
    return rates


def h_score(rates: Mapping[str, float]) -> float:
    if set(rates) != set(DIMENSIONS):
        raise ValueError(f"H-Score needs all four dimensions, got {sorted(rates)}")
    return sum(rates[d] for d in DIMENSIONS) / len(DIMENSIONS)
