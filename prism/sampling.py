"""Sampling parameters of the evaluated models (Section 3.1 and Appendix G of the paper).

Closed-ended KM, KE, and IFE tasks use temperature 0.8 and top-p 0.8; closed-ended RE tasks use
temperature 0.4 and top-p 0.95; open-ended tasks (LLM-Eval) use temperature 0.8 and top-p 0.8.
"""

from __future__ import annotations

from typing import Dict

from .tasks import Task

CLOSED_ENDED = {"temperature": 0.8, "top_p": 0.8}
CLOSED_ENDED_RE = {"temperature": 0.4, "top_p": 0.95}
OPEN_ENDED = {"temperature": 0.8, "top_p": 0.8}


def sampling_params(task: Task) -> Dict[str, float]:
    if task.open_ended:
        return dict(OPEN_ENDED)
    if task.dimension == "RE":
        return dict(CLOSED_ENDED_RE)
    return dict(CLOSED_ENDED)
