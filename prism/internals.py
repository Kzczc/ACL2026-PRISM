"""Metrics over the internal states of a local model (Section 4.2 of the paper).

The functions take plain arrays so they can be used with any runtime:

* :func:`active_neurons` counts the MLP neurons that fire, summed over layers and token positions.
* :func:`attention_sparsity` measures how concentrated the attention distributions are.
* :func:`forward_flops` estimates the floating-point operations of one forward pass.
* :func:`is_refusal` separates refusals from ordinary answers.
"""

from __future__ import annotations

import math
import re
from typing import Iterable, Sequence

import numpy as np

REFUSAL_PATTERNS = (
    r"\bi\s+(?:cannot|can't|can not|won't|will not|am not able to)\b",
    r"\bi'?m\s+sorry\b",
    r"\bi\s+apologi[sz]e\b",
    r"\bas an ai\b",
    r"\b(?:unable|refuse[sd]?)\s+to\s+(?:comply|help|assist|provide|answer)\b",
    r"\bcannot\s+(?:comply|fulfill|provide|assist|help|answer)\b",
    r"\[NO_INFO\]",
    r"(抱歉|无法提供|无法完成|不能提供|我不能)",
)
_REFUSAL = re.compile("|".join(REFUSAL_PATTERNS), re.IGNORECASE)


def is_refusal(response: str) -> bool:
    """True when the response declines the request instead of answering it."""
    return bool(_REFUSAL.search(str(response or "")))


def active_neurons(activations: Iterable[np.ndarray], threshold: float = 0.0) -> float:
    """Number of MLP neurons above ``threshold``, summed over layers and positions, in millions.

    ``activations`` holds one array per layer with shape ``[tokens, intermediate size]``, taken after
    the activation function of the feed-forward block.
    """
    total = 0.0
    for layer in activations:
        total += float(np.count_nonzero(np.asarray(layer) > threshold))
    return total / 1e6


def attention_sparsity(attentions: Iterable[np.ndarray]) -> float:
    """Concentration of the attention distributions: ``1 - H(a) / log n``, averaged.

    Each array has shape ``[heads, queries, keys]`` and holds the causal attention weights of one
    layer, so the query at position ``i`` distributes its weight over ``i + 1`` keys. The value is 0
    when every query attends uniformly and approaches 1 when each query attends to a single key.
    """
    values = []
    for layer in attentions:
        weights = np.asarray(layer, dtype=np.float64)
        if weights.ndim != 3:
            raise ValueError(f"expected [heads, queries, keys], got shape {weights.shape}")
        for query in range(1, weights.shape[1]):  # position 0 has a single key, its entropy is 0
            support = weights[:, query, : query + 1]
            support = support / np.clip(support.sum(axis=-1, keepdims=True), 1e-12, None)
            entropy = -(support * np.log(np.clip(support, 1e-12, None))).sum(axis=-1)
            values.append(1.0 - entropy / math.log(query + 1))
    if not values:
        return 0.0
    return float(np.mean(np.concatenate([np.atleast_1d(v) for v in values])))


def forward_flops(non_embedding_parameters: int, tokens: int, layers: int, hidden_size: int) -> float:
    """Floating-point operations of one forward pass over ``tokens`` tokens, in GFLOPs.

    ``2 * parameters * tokens`` for the linear layers plus ``4 * layers * tokens^2 * hidden`` for the
    attention scores and their application to the values.
    """
    linear = 2.0 * non_embedding_parameters * tokens
    attention = 4.0 * layers * tokens * tokens * hidden_size
    return (linear + attention) / 1e9


def summarize(rows: Sequence[dict]) -> dict:
    """Mean of the per-item measurements of one group."""
    if not rows:
        return {"items": 0}
    keys = ("active_neurons_m", "attention_sparsity", "gflops", "tokens")
    return {"items": len(rows), **{k: float(np.mean([r[k] for r in rows])) for k in keys if k in rows[0]}}
