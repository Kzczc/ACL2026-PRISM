import pytest

from prism.data import data_dir, read_jsonl
from prism.judge import CLAIM_PROMPTS
from prism.prompts import PROMPT_DIR, build_prompt, fill_template, format_question, read_prompt, task_prompt
from prism.sampling import sampling_params
from prism.tasks import TASKS, get_task


def test_every_task_prompt_exists():
    for task in TASKS:
        assert task_prompt(task).strip()


def test_judge_prompts_exist():
    for name in ("semantic_equivalence", "math_equivalence", "RE-MRF-Code_Generation", *CLAIM_PROMPTS.values()):
        relative = name if name.endswith(".md") else f"judges/{name}.md"
        assert read_prompt(relative).strip()
    for name in ("schema_normalizer", "evidence_retriever", "type_classifier", "quality_scoring"):
        assert read_prompt(f"construction/{name}.md").strip()


def test_question_formatting():
    task = get_task("RE-LF-Critical_Reasoning")
    record = {"question": "Which holds?", "options": ["first", "second"], "answer": "A"}
    text = format_question(record, task)
    assert "Options:\nA. first\nB. second" in text
    procedure_task = get_task("RE-PF-Subquestion")
    text = format_question({"question": "Who?", "procedure": ["step one", "step two"]}, procedure_task)
    assert text.endswith("Procedure:\nstep one\nstep two\n")
    code_task = get_task("RE-MRF-Code_Generation")
    assert "Test Input:\n1 2" in format_question({"question": "Add them", "test_input": "1 2"}, code_task)


def test_build_prompt_is_prompt_then_question():
    task = get_task("KE-FD-TruthfulQA")
    prompt = build_prompt({"question": "Is the sky green?"}, task)
    assert prompt.startswith(task_prompt(task))
    assert prompt.endswith("Is the sky green?")


def test_fill_template_keeps_json_braces():
    template = 'Return {"correct": 0 or 1} for {model_answer}'
    assert fill_template(template, model_answer="x") == 'Return {"correct": 0 or 1} for x'


def test_sampling_parameters_follow_the_paper():
    assert sampling_params(get_task("KE-FD-TruthfulQA")) == {"temperature": 0.8, "top_p": 0.8}
    assert sampling_params(get_task("RE-LF-Critical_Reasoning")) == {"temperature": 0.4, "top_p": 0.95}
    assert sampling_params(get_task("RE-IIF-Summarize")) == {"temperature": 0.8, "top_p": 0.8}
    assert sampling_params(get_task("IFE-CCL-No_Comma")) == {"temperature": 0.8, "top_p": 0.8}


@pytest.mark.skipif(not (data_dir() / "KE/FD/TruthfulQA.jsonl").exists(), reason="data files not present")
def test_prompt_and_data_agree_on_answer_tokens():
    prompt = read_prompt("tasks/KM-DSK.md")
    assert "[TRUE]" in prompt and "[FALSE]" in prompt and "[NO_INFO]" in prompt
    labels = {r["answer"] for r in read_jsonl(data_dir() / "KM/DSK/PubMedQA.jsonl")}
    assert labels <= {"[TRUE]", "[FALSE]"}
    assert "[NO_INFO]" in read_prompt("tasks/KM-DSK-Open.md")
