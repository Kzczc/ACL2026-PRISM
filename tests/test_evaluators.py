import pytest

from prism.data import data_dir, read_jsonl
from prism.evaluators import needs_judge, score_item
from prism.tasks import get_task


class StubJudge:
    """Judge replacement that records calls and returns fixed verdicts."""

    def __init__(self, correct=True, rate=0.25, total=4):
        self.correct, self.rate, self.total, self.calls = correct, rate, total, 0

    def equivalent(self, response, reference):
        self.calls += 1
        return {"correct": self.correct}

    def math_equivalent(self, question, reference, response):
        self.calls += 1
        return {"correct": self.correct}

    def code_score(self, question, test_input, test_output, response):
        self.calls += 1
        return {"total": self.total}

    def claim_hallucination(self, task_id, question, response):
        self.calls += 1
        return {"hallucination_rate": self.rate}


def test_failed_responses_score_zero():
    task = get_task("KE-IMC-Numeric")
    for response in ("", None, "ERROR: timeout"):
        result = score_item(task, {"answer": "144", "question": "q"}, response)
        assert result.score == 0.0 and result.detail["failed_response"]


def test_rule_based_evaluators():
    assert score_item(get_task("KE-IMC-Numeric"), {"answer": "144", "question": "q"}, " 144 ").score == 1.0
    assert score_item(get_task("RE-PF-Triplet_Hopping"), {"answer": "India", "question": "q"}, "India.").score == 1.0
    choice = score_item(get_task("RE-LF-Cognitive_Traps"), {"answer": "B", "options": ["a", "b", "c", "d"], "question": "q"}, "The answer is B")
    assert choice.score == 1.0 and choice.detail["extracted"] == "B"
    assert score_item(get_task("KM-FK-Awards"), {"answer": "[NO_INFO]", "question": "q"}, "[NO_INFO]").score == 1.0
    assert score_item(get_task("KM-FK-Awards"), {"answer": "[NO_INFO]", "question": "q"}, "The winner was John").score == 0.0
    assert score_item(get_task("KM-DSK-PubMedQA"), {"answer": "[TRUE]", "question": "q"}, "[TRUE]").score == 1.0
    assert score_item(get_task("KM-DSK-PubMedQA"), {"answer": "[TRUE]", "question": "q"}, "[NO_INFO]").score == 0.0
    assert score_item(get_task("IFE-LC-Upper_Bound"), {"word_range": [1, 3], "question": "q"}, "one two").score == 1.0
    assert score_item(get_task("IFE-LC-Upper_Bound"), {"word_range": [1, 3], "question": "q"}, "one two three four").score == 0.0
    assert score_item(get_task("IFE-EF-Data_Schema"), {"format": "JSON", "question": "q"}, '{"a": 1}').score == 1.0
    assert score_item(get_task("IFE-EF-Data_Schema"), {"format": "JSON", "question": "q"}, "not json").score == 0.0
    assert score_item(get_task("IFE-LgC-German"), {"language": "de", "question": "q"},
                      "Die Hauptstadt von Japan ist Tokio.").score == 1.0
    ife = score_item(get_task("IFE-CCL-No_Comma"), {"instruction_id": "punctuation:no_comma", "kwargs": [], "question": "q"}, "no commas here")
    assert ife.score == 1.0


def test_judge_based_evaluators():
    judge = StubJudge()
    assert score_item(get_task("KE-FD-TruthfulQA"), {"answer": "Yes, less than 1%", "question": "q"}, "Yes, about 1%", judge).score == 1.0
    assert judge.calls == 0  # the yes/no rule settles it without the judge
    assert score_item(get_task("KE-FD-TruthfulQA"), {"answer": "It was 1979", "question": "q"}, "In 1979", judge).score == 1.0
    assert judge.calls == 1
    assert score_item(get_task("KM-DSK-SciQ"), {"answer": "oxidants", "question": "q"}, "They are oxidants.", judge).score == 1.0
    abstain = score_item(get_task("KM-DSK-SciQ"), {"answer": "oxidants", "question": "q"}, "[NO_INFO]", judge)
    assert abstain.score == 0.0 and abstain.detail["abstained"]
    assert score_item(get_task("RE-MRF-Mathematics"), {"answer": "2", "question": "q"}, "two", judge).score == 1.0
    assert score_item(get_task("RE-MRF-Code_Generation"), {"question": "q", "test_input": "", "test_output": ""}, "code", judge).score == pytest.approx(0.8)
    assert score_item(get_task("RE-IIF-Summarize"), {"question": "q"}, "summary", judge).score == pytest.approx(0.75)


def test_missing_judge_is_reported():
    assert needs_judge(get_task("RE-IIF-Summarize"))
    assert not needs_judge(get_task("IFE-LgC-Chinese"))
    with pytest.raises(RuntimeError):
        score_item(get_task("RE-IIF-Summarize"), {"question": "q"}, "summary")


@pytest.mark.skipif(not (data_dir() / "IFE/EF/Data_Schema.jsonl").exists(), reason="data files not present")
def test_real_records_score_without_errors():
    for task_id in ("IFE-EF-Data_Schema", "IFE-CCL-Length_Format_Mixed", "IFE-LC-Approximate", "RE-LF-Critical_Reasoning"):
        task = get_task(task_id)
        for record in list(read_jsonl(data_dir() / task.data_file))[:20]:
            result = score_item(task, record, "A plain response without any special formatting.")
            assert 0.0 <= result.score <= 1.0
