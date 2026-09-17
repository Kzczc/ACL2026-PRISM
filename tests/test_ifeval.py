import json

import pytest

from prism.data import data_dir, read_jsonl
from prism.evaluators import ifeval
from prism.tasks import TASKS


def test_basic_checks():
    assert ifeval.check("punctuation:no_comma", "a b c", {})
    assert not ifeval.check("punctuation:no_comma", "a, b", {})
    assert ifeval.check("keywords:forbidden_words", "I am wealthy", {"forbidden_words": ["rich", "money"]})
    assert not ifeval.check("keywords:forbidden_words", "I am rich", {"forbidden_words": ["rich"]})
    assert ifeval.check("keywords:existence", "sky and mountain at evening", {"keywords": ["sky", "evening"]})
    assert ifeval.check("keywords:frequency", "dog dog dog", {"keyword": "dog", "frequency": 3, "relation": "at least"})
    assert not ifeval.check("keywords:frequency", "dog", {"keyword": "dog", "frequency": 3, "relation": "at least"})
    assert ifeval.check("keywords:letter_frequency", "banana", {"letter": "a", "let_frequency": 3, "let_relation": "at least"})
    assert ifeval.check("length_constraints:number_words", "one two three", {"num_words": 5, "relation": "less than"})
    assert ifeval.check("length_constraints:number_sentences", "One. Two! Three?", {"num_sentences": 3})
    assert ifeval.check("length_constraints:number_paragraphs", "a *** b *** c", {"num_paragraphs": 3})
    assert ifeval.check("detectable_format:number_highlighted_sections", "*one* and *two*", {"num_highlights": 2})
    assert ifeval.check("detectable_format:title", "<<A Title>>\nbody", {})
    assert not ifeval.check("detectable_format:title", "# A Title", {})
    assert ifeval.check("detectable_format:json_format", '```json\n{"a": 1}\n```', {})
    assert ifeval.check("detectable_format:constrained_response", "My answer is maybe.", {})
    assert ifeval.check("detectable_content:number_placeholders", "[name] wrote to [place]", {"num_placeholders": 2})
    assert ifeval.check("startend:quotation", '"quoted"', {})
    assert ifeval.check("startend:end_checker", "text ending here", {"end_phrase": "ending here"})
    assert ifeval.check("combination:two_responses", "first answer\n******\nsecond answer", {})
    assert not ifeval.check("combination:two_responses", "only one answer", {})
    assert ifeval.check("combination:repeat_prompt", "Repeat me. Then the answer.", {"prompt_to_repeat": "Repeat me."})
    assert ifeval.check("change_case:capital_word_frequency", "THIS IS loud", {"capital_frequency": 2, "capital_relation": "at least"})


def test_language_checks():
    assert ifeval.check("language:response_language", "Die Hauptstadt von Japan ist Tokio.", {"language": "de"})
    assert not ifeval.check("language:response_language", "The capital of Japan is Tokyo.", {"language": "de"})
    assert ifeval.normalize_language("zh-cn") == "zh"


def test_instruction_recovery():
    instructions = ifeval.item_instructions(
        "ifeval_script:keywords:forbidden_words",
        [{"forbidden_words": ["rich"], "relation": None}, {"num_sentences": 40, "relation": "at least"}])
    assert ("keywords:forbidden_words", {"forbidden_words": ["rich"]}) in instructions
    assert ("length_constraints:number_sentences", {"num_sentences": 40, "relation": "at least"}) in instructions
    ok, failed = ifeval.follows_all("Short answer.", instructions)
    assert not ok and "length_constraints:number_sentences" in failed


def test_alias_and_constraint_string():
    name, kwargs = ifeval.parse_constraint_string("language:reasoning_language: {'language': 'fr'}")
    assert (name, kwargs) == ("language:reasoning_language", {"language": "fr"})
    instructions = ifeval.item_instructions("language:reasoning_language", [{"language": "fr"}])
    assert instructions == [("language:response_language", {"language": "fr"})]


@pytest.mark.skipif(not (data_dir() / "IFE/CCL/No_Comma.jsonl").exists(), reason="data files not present")
def test_every_instruction_in_the_data_is_supported():
    for task in TASKS:
        if task.evaluator != "ifeval":
            continue
        for record in read_jsonl(data_dir() / task.data_file):
            for name, kwargs in ifeval.item_instructions(record["instruction_id"], record["kwargs"]):
                assert name in ifeval.CHECKS, (record["id"], name)
                ifeval.check(name, "A sample response, with commas and *highlights*.\n***\nSecond part.", kwargs)
