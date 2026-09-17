from prism.evaluators.matching import (abstained, contains_reference, exact_match, extract_choice, fuzzy_match,
                                       normalize, normalize_loose, truth_label, yes_no)


def test_normalization():
    assert normalize("  The   Answer ") == "the answer"
    assert normalize_loose("Paris, France.") == "paris france"


def test_exact_and_fuzzy():
    assert exact_match(" Oxidants ", "oxidants")
    assert not exact_match("oxidant", "oxidants")
    assert fuzzy_match("The answer is India.", "India")
    assert fuzzy_match("19,213", "19213") is False or fuzzy_match("19213", "19,213")
    assert fuzzy_match("It happened in 1979", "1979")
    assert not fuzzy_match("Berlin", "Paris")
    assert contains_reference("The capital is Jakarta.", "Jakarta")
    assert not contains_reference("Jakarta", "The capital is Jakarta")


def test_yes_no():
    assert yes_no("Yes, less than 1% of the budget") == "yes"
    assert yes_no("No. The red-suited Santa image existed before") == "no"
    assert yes_no("It is not known whether this holds") is None
    assert yes_no("Yes and no, depending on the context") is None


def test_extract_choice():
    assert extract_choice("The answer is **B**") == "B"
    assert extract_choice("A") == "A"
    assert extract_choice("Reasoning...\nAnswer: C") == "C"
    assert extract_choice("first D then finally B.") == "B"
    assert extract_choice("") == ""


def test_truth_and_abstention():
    assert truth_label("[TRUE]") == "[TRUE]"
    assert truth_label("Answer: [NO_INFO]") == "[NO_INFO]"
    assert truth_label("[TRUE] or [FALSE]") is None
    assert truth_label("TRUE") == "[TRUE]"
    assert abstained("I am not sure: [NO_INFO]")
    assert not abstained("photosynthesis")
