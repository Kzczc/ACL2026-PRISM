import pytest

from prism.metrics import dimension_rates, h_score, task_score
from prism.tasks import TASKS

# Sub-task scores S of GPT-5.2 reported in Tables 9-12 of the paper, in the order of prism.tasks.
PAPER_GPT52 = {
    "KE": {"FD-ArtCulture": 100.00, "FD-Business": 96.97, "FD-DefAn": 16.57, "FD-FoodCooking": 100.00,
           "FD-Language": 100.00, "FD-LawCrimeMilitary": 97.50, "FD-Religion": 100.00, "FD-Science": 100.00,
           "FD-Sports": 97.92, "FD-TruthfulQA": 68.15, "IMC-Numeric": 54.22, "IMC-Text": 92.63,
           "EIC-SelfBuilt": 79.87, "EIC-WhoQA_Entity": 54.77, "EIC-WiC": 73.98},
    "KM": {"DSK-Chinese_SafetyQA": 85.11, "DSK-PubMedQA": 74.03, "DSK-RAG-QA-Leaderboard": 64.56,
           "DSK-RAG-QA-Leaderboard_Fill": 88.68, "DSK-StrategyQA": 86.54, "DSK-SciQ": 87.40, "FK-Awards": 100.00,
           "FK-Biology": 100.00, "FK-Competition": 100.00, "FK-Country": 100.00, "FK-Dynasty": 95.24,
           "FK-Festival": 100.00, "FK-Large_Language_Model": 100.00, "FK-Literature": 100.00, "FK-Military": 100.00,
           "FK-Phone": 100.00, "FK-Time": 100.00, "FK-University": 100.00, "TK-Numeric": 100.00, "TK-Text": 99.08,
           "NPK-Organizational": 99.19, "NPK-Private": 97.57},
    "RE": {"LF-Critical_Reasoning": 81.55, "LF-Contextual_Inference": 85.31, "LF-Cognitive_Traps": 88.89,
           "PF-Subquestion": 63.66, "PF-Triplet_Hopping": 97.44, "IIF-Summarize": 89.28, "IIF-Simplification": 93.37,
           "IIF-Dialogue_Extraction": 85.60, "MRF-Mathematics": 37.39, "MRF-Code_Generation": 100 * 1.54 / 5},
    "IFE": {"EF-Data_Schema": 87.04, "EF-Text_Structure": 36.54, "LC-Approximate": 55.95, "LC-Lower_Bound": 75.00,
            "LC-Upper_Bound": 94.26, "LgC-German": 92.79, "LgC-Spanish": 88.89, "LgC-French": 87.74,
            "LgC-Japanese": 93.55, "LgC-Russian": 90.00, "LgC-Chinese": 81.42, "CCL-Forbidden_Words": 93.88,
            "CCL-Keyword_Inclusion": 96.49, "CCL-Length_Format_Mixed": 82.52, "CCL-Math_Reasoning": 83.00,
            "CCL-No_Comma": 93.94, "CCL-Start_End_Phrase": 100.00, "CCL-Two_Responses": 90.77},
}
PAPER_RATES = {"KE": 17.83, "KM": 5.57, "RE": 24.67, "IFE": 15.35}
PAPER_H_SCORE = 15.85


def test_task_score():
    assert task_score([1.0, 0.0, 1.0, 1.0]) == pytest.approx(75.0)
    assert task_score([0.8]) == pytest.approx(80.0)
    with pytest.raises(ValueError):
        task_score([])


def test_paper_scores_cover_every_task():
    keys = {f"{dim}-{name}" for dim, scores in PAPER_GPT52.items() for name in scores}
    assert keys == {f"{t.dimension}-{t.subcategory}-{t.name}" for t in TASKS}


def test_reproduces_the_reported_rates_of_gpt_5_2():
    scores = {f"{dim}-{name}": value for dim, entries in PAPER_GPT52.items() for name, value in entries.items()}
    rates = dimension_rates(scores)
    for dim, expected in PAPER_RATES.items():
        assert rates[dim] == pytest.approx(expected, abs=0.02)
    assert h_score(rates) == pytest.approx(PAPER_H_SCORE, abs=0.02)


def test_incomplete_dimensions():
    assert dimension_rates({"KE-FD-TruthfulQA": 50.0}) == {}
    assert dimension_rates({"KE-FD-TruthfulQA": 50.0}, require_complete=False) == {"KE": pytest.approx(50.0)}
    with pytest.raises(ValueError):
        h_score({"KE": 10.0})
