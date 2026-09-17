"""IFEval-style instruction checks (strict, prompt-level) for the IFE tasks.

An IFE record stores its main instruction id (``instruction_id``) and a list of keyword-argument
dicts (``kwargs``) in the IFEval format. Instructions with arguments are recovered from the
non-empty keys of each dict; the main instruction is always checked. A response passes when every
instruction is satisfied.
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from langdetect import DetectorFactory, detect

    DetectorFactory.seed = 0
except ImportError:  # pragma: no cover - langdetect is a declared dependency
    detect = None

Instruction = Tuple[str, Dict[str, Any]]

LANGUAGE_ALIASES = {"zh-cn": "zh", "zh-tw": "zh"}


def detect_language(text: str) -> Optional[str]:
    if detect is None:
        raise RuntimeError("langdetect is required for language checks: pip install langdetect")
    try:
        code = detect(text)
    except Exception:
        return None
    return LANGUAGE_ALIASES.get(code, code)


def normalize_language(code: str) -> str:
    code = str(code).lower()
    return LANGUAGE_ALIASES.get(code, code)


def compare(value: int, threshold: int, relation: Optional[str]) -> bool:
    relation = (relation or "at least").lower()
    if relation == "less than":
        return value < threshold
    if relation == "at most":
        return value <= threshold
    if relation == "exactly":
        return value == threshold
    return value >= threshold


def count_words(text: str) -> int:
    return len(re.findall(r"\w+", text))


def count_sentences(text: str) -> int:
    return len([s for s in re.split(r"(?<=[.!?。！？])\s+", text.strip()) if s.strip()])


def count_highlights(text: str) -> int:
    single = [h for h in re.findall(r"\*[^\n\*]*\*", text) if h.strip("*").strip()]
    double = [h for h in re.findall(r"\*\*[^\n\*]*\*\*", text) if h.strip("*").strip()]
    return len(single) + len(double)


def _bullets(text: str) -> int:
    return len(re.findall(r"^\s*\*[^\*].*$", text, re.MULTILINE)) + len(re.findall(r"^\s*-.*$", text, re.MULTILINE))


def _strip_fences(text: str) -> str:
    value = text.strip()
    value = re.sub(r"^```(?:json|JSON|Json)?\s*", "", value)
    value = re.sub(r"\s*```$", "", value)
    return value.strip()


def _json_ok(text: str) -> bool:
    try:
        json.loads(_strip_fences(text))
        return True
    except ValueError:
        return False


def _postscript(text: str, marker: str) -> bool:
    marker = marker.strip().lower()
    if marker == "p.p.s":
        pattern = r"\s*p\.\s?p\.\s?s.*$"
    elif marker == "p.s.":
        pattern = r"\s*p\.\s?s\..*$"
    else:
        pattern = r"\s*" + re.escape(marker) + r".*$"
    return bool(re.findall(pattern, text.lower(), flags=re.MULTILINE))


def _two_responses(text: str) -> bool:
    parts = text.split("******")
    valid = []
    for index, part in enumerate(parts):
        if not part.strip():
            if index not in (0, len(parts) - 1):
                return False
        else:
            valid.append(part.strip())
    return len(valid) == 2 and valid[0] != valid[1]


def _nth_paragraph_first_word(text: str, num_paragraphs: int, nth_paragraph: int, first_word: str) -> bool:
    paragraphs = [p for p in re.split(r"\n\n", text) if p.strip()]
    if len(paragraphs) != num_paragraphs or not 1 <= nth_paragraph <= len(paragraphs):
        return False
    words = paragraphs[nth_paragraph - 1].strip().split()
    if not words:
        return False
    word = re.sub(r"[^\w]", "", words[0]).lower()
    return word == str(first_word).strip().lower()


def _sections(text: str, section_spliter: Optional[str], num_sections: Optional[int]) -> bool:
    if section_spliter and num_sections:
        sections = re.split(r"\s?" + re.escape(section_spliter) + r"\s?\d+\s?", text)
        return len(sections) - 1 >= int(num_sections)
    return len(re.findall(r"\b(section|paragraph)\s*\d+", text, re.IGNORECASE)) >= 1


CONSTRAINED_OPTIONS = ("My answer is yes.", "My answer is no.", "My answer is maybe.")

CHECKS: Dict[str, Callable[..., bool]] = {
    "keywords:forbidden_words": lambda r, forbidden_words, **_: all(
        not re.search(r"\b" + re.escape(w) + r"\b", r, re.IGNORECASE) for w in forbidden_words),
    "keywords:existence": lambda r, keywords, **_: all(re.search(re.escape(k), r, re.IGNORECASE) for k in keywords),
    "keywords:frequency": lambda r, keyword, frequency, relation=None, **_: compare(
        len(re.findall(re.escape(keyword), r, re.IGNORECASE)), int(frequency), relation),
    "keywords:letter_frequency": lambda r, letter, let_frequency, let_relation=None, **_: compare(
        r.lower().count(str(letter).lower()), int(let_frequency), let_relation),
    "language:response_language": lambda r, language, **_: detect_language(r) == normalize_language(language),
    "length_constraints:number_sentences": lambda r, num_sentences, relation=None, **_: compare(
        count_sentences(r), int(num_sentences), relation),
    "length_constraints:number_paragraphs": lambda r, num_paragraphs, **_: len(
        [p for p in re.split(r"\s?\*\*\*\s?", r) if p.strip()]) == int(num_paragraphs),
    "length_constraints:nth_paragraph_first_word": lambda r, num_paragraphs, nth_paragraph, first_word, **_:
        _nth_paragraph_first_word(r, int(num_paragraphs), int(nth_paragraph), first_word),
    "length_constraints:number_words": lambda r, num_words, relation=None, **_: compare(
        count_words(r), int(num_words), relation),
    "detectable_content:number_placeholders": lambda r, num_placeholders, **_: len(
        re.findall(r"\[.*?\]", r)) >= int(num_placeholders),
    "detectable_content:postscript": lambda r, postscript_marker, **_: _postscript(r, postscript_marker),
    "detectable_format:number_bullet_lists": lambda r, num_bullets=None, **_: (
        _bullets(r) == int(num_bullets) if num_bullets else _bullets(r) >= 1),
    "detectable_format:number_highlighted_sections": lambda r, num_highlights=None, **_: count_highlights(r) >= int(num_highlights or 1),
    "detectable_format:multiple_sections": lambda r, section_spliter=None, num_sections=None, **_: _sections(
        r, section_spliter, num_sections),
    "detectable_format:json_format": lambda r, **_: _json_ok(r),
    "detectable_format:title": lambda r, **_: any(t.strip("<>").strip() for t in re.findall(r"<<[^\n]+>>", r)),
    "detectable_format:constrained_response": lambda r, **_: any(o in r for o in CONSTRAINED_OPTIONS),
    "combination:two_responses": lambda r, **_: _two_responses(r),
    "combination:repeat_prompt": lambda r, prompt_to_repeat, **_: r.strip().lower().startswith(
        str(prompt_to_repeat).strip().lower()),
    "startend:end_checker": lambda r, end_phrase, **_: r.strip().strip('"').lower().endswith(
        str(end_phrase).strip().lower()),
    "startend:quotation": lambda r, **_: len(r.strip()) > 1 and r.strip()[0] == '"' and r.strip()[-1] == '"',
    "change_case:capital_word_frequency": lambda r, capital_frequency, capital_relation=None, **_: compare(
        sum(1 for w in re.findall(r"\w+", r) if w.isupper()), int(capital_frequency), capital_relation),
    "change_case:english_capital": lambda r, **_: r.isupper() and detect_language(r) == "en",
    "change_case:english_lowercase": lambda r, **_: r.islower() and detect_language(r) == "en",
    "punctuation:no_comma": lambda r, **_: "," not in r,
}
# Instruction names used by the math-reasoning subset and their IFEval equivalents.
ALIASES = {
    "language:reasoning_language": "language:response_language",
    "length_constraint_checkers:number_words": "length_constraints:number_words",
}

# Instructions that carry arguments, identified by their required keys (IFEval kwargs schema).
KWARG_INSTRUCTIONS: List[Tuple[str, Tuple[str, ...], Tuple[str, ...]]] = [
    ("keywords:forbidden_words", ("forbidden_words",), ()),
    ("keywords:existence", ("keywords",), ()),
    ("keywords:frequency", ("keyword", "frequency"), ("relation",)),
    ("keywords:letter_frequency", ("letter", "let_frequency"), ("let_relation",)),
    ("language:response_language", ("language",), ()),
    ("length_constraints:nth_paragraph_first_word", ("num_paragraphs", "nth_paragraph", "first_word"), ()),
    ("length_constraints:number_sentences", ("num_sentences",), ("relation",)),
    ("length_constraints:number_words", ("num_words",), ("relation",)),
    ("detectable_content:number_placeholders", ("num_placeholders",), ()),
    ("detectable_content:postscript", ("postscript_marker",), ()),
    ("detectable_format:number_bullet_lists", ("num_bullets",), ()),
    ("detectable_format:number_highlighted_sections", ("num_highlights",), ()),
    ("detectable_format:multiple_sections", ("section_spliter", "num_sections"), ()),
    ("change_case:capital_word_frequency", ("capital_frequency",), ("capital_relation",)),
    ("startend:end_checker", ("end_phrase",), ()),
    ("combination:repeat_prompt", ("prompt_to_repeat",), ()),
]


def instructions_from_kwargs(kwargs: Dict[str, Any]) -> List[Instruction]:
    present = {k: v for k, v in kwargs.items() if v is not None}
    found: List[Instruction] = []
    for name, required, optional in KWARG_INSTRUCTIONS:
        if all(k in present for k in required):
            found.append((name, {k: present[k] for k in required + optional if k in present}))
    if "num_paragraphs" in present and "first_word" not in present:
        found.append(("length_constraints:number_paragraphs", {"num_paragraphs": present["num_paragraphs"]}))
    return found


def parse_constraint_string(value: str) -> Instruction:
    """Parse ``"id"`` or ``"id: {kwargs}"`` (format of the math-reasoning subset)."""
    value = value.strip()
    if ": {" in value:
        name, raw = value.split(": {", 1)
        return name.strip(), ast.literal_eval("{" + raw)
    return value, {}


def item_instructions(instruction_id: str, kwargs_list: List[Dict[str, Any]]) -> List[Instruction]:
    """All instructions of an item: the main instruction plus those recovered from its kwargs."""
    main = instruction_id.split("ifeval_script:", 1)[-1]
    main = ALIASES.get(main, main)
    instructions: List[Instruction] = []
    for kwargs in kwargs_list or []:
        instructions.extend(instructions_from_kwargs(kwargs))
    if not any(name == main for name, _ in instructions):
        instructions.insert(0, (main, {}))
    unique: List[Instruction] = []
    for inst in instructions:
        if inst not in unique:
            unique.append(inst)
    return unique


def check(name: str, response: str, kwargs: Dict[str, Any]) -> bool:
    if name not in CHECKS:
        raise KeyError(f"unsupported instruction {name!r}")
    try:
        return bool(CHECKS[name](response, **kwargs))
    except TypeError as exc:
        raise ValueError(f"instruction {name!r} is missing arguments: {kwargs}") from exc


def follows_all(response: str, instructions: List[Instruction]) -> Tuple[bool, List[str]]:
    failed = [name for name, kwargs in instructions if not check(name, response, kwargs)]
    return not failed, failed
