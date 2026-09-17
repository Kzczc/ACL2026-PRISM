"""String matching utilities shared by the evaluators."""

from __future__ import annotations

import re
from typing import Optional, Sequence

_SPACES = re.compile(r"\s+")
_PUNCT = re.compile(r"[.,;:!?'\"()\[\]{}]")
_YES_NO = re.compile(r"\b(yes|no)\b", re.IGNORECASE)


def normalize(text: object) -> str:
    """Lower-case and collapse whitespace."""
    return _SPACES.sub(" ", str(text if text is not None else "")).strip().lower()


def normalize_loose(text: object) -> str:
    """``normalize`` plus removal of common punctuation."""
    return _SPACES.sub(" ", _PUNCT.sub("", normalize(text))).strip()


def exact_match(response: str, reference: object) -> bool:
    return normalize(response) == normalize(reference)


def fuzzy_match(response: str, reference: object) -> bool:
    """Exact match after normalization, containment in either direction, or identical digit sequences."""
    pred, ref = normalize_loose(response), normalize_loose(reference)
    if not pred or not ref:
        return False
    if pred == ref or ref in pred or pred in ref:
        return True
    pred_digits, ref_digits = re.findall(r"\d+", pred), re.findall(r"\d+", ref)
    return bool(ref_digits) and pred_digits == ref_digits


def contains_reference(response: str, reference: object) -> bool:
    pred, ref = normalize_loose(response), normalize_loose(reference)
    return bool(ref) and (pred == ref or ref in pred)


def yes_no(text: object) -> Optional[str]:
    """Return ``"yes"`` or ``"no"`` when the text commits to exactly one of them, otherwise None.

    Texts that use both words (``"Yes and no"``) are ambiguous and left to the judge.
    """
    found = {w.lower() for w in _YES_NO.findall(str(text or ""))}
    return found.pop() if len(found) == 1 else None


def extract_choice(response: str, letters: Sequence[str] = "ABCD") -> str:
    """Extract the selected option letter from a response (last explicit choice wins)."""
    if not response:
        return ""
    set_ = "".join(letters)
    lines = response.strip().split("\n")
    tail = "\n".join(lines[-5:])
    patterns = [
        rf"^\s*([{set_}])\s*$",
        rf"^\s*\*\*([{set_}])\*\*\s*$",
        rf"\*\*([{set_}])\*\*",
        rf"[Tt]he answer is[:\s]*\**([{set_}])\**",
        rf"[Aa]nswer[:\s]*\**([{set_}])\**",
    ]
    for pattern in patterns:
        match = re.search(pattern, tail, re.MULTILINE)
        if match:
            return match.group(1).upper()
    for line in reversed(lines):
        line = line.strip()
        match = re.match(rf"^\**([{set_}])\**[\.\):]?$", line)
        if match:
            return match.group(1).upper()
    for line in reversed(lines[-10:]):
        match = re.search(rf"\b([{set_}])\b[\.。]?\s*$", line.strip())
        if match:
            return match.group(1).upper()
    matches = re.findall(rf"\b([{set_}])\b", response)
    return matches[-1].upper() if matches else ""


TRUTH_LABELS = ("[TRUE]", "[FALSE]", "[NO_INFO]")


def truth_label(text: object) -> Optional[str]:
    """Return the single label among [TRUE], [FALSE], [NO_INFO] used in a response, otherwise None."""
    upper = str(text or "").upper()
    found = [label for label in TRUTH_LABELS if label in upper]
    if len(found) == 1:
        return found[0]
    if not found:
        match = re.match(r"\W*(TRUE|FALSE|NO_INFO)\W*$", upper)
        return f"[{match.group(1)}]" if match else None
    return None


def abstained(text: object) -> bool:
    """The response declares missing knowledge with the [NO_INFO] token."""
    upper = str(text or "").upper()
    return "[NO_INFO]" in upper or re.fullmatch(r"\W*NO_INFO\W*", upper) is not None
