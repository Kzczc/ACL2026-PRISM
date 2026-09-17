"""Registry of the 65 PRISM sub-tasks.

Indices, dimensions, sub-categories, and task names follow Figure 3 and Table 6 of the paper.
Each task names its data file, its prompt, and the evaluator that scores a model response.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

DIMENSIONS: Dict[str, str] = {
    "KE": "Knowledge Error",
    "KM": "Knowledge Missing",
    "RE": "Reasoning Error",
    "IFE": "Instruction Following Error",
}

SUBCATEGORIES: Dict[str, Tuple[str, str]] = {
    "FD": ("KE", "Factual Distortion"),
    "IMC": ("KE", "Intra-Memory Conflict"),
    "EIC": ("KE", "Entity-Identity Confusion"),
    "DSK": ("KM", "Domain-Specific Knowledge"),
    "FK": ("KM", "Fictional Knowledge"),
    "TK": ("KM", "Timely Knowledge"),
    "NPK": ("KM", "Non-Public Knowledge"),
    "LF": ("RE", "Logical Fallacy"),
    "PF": ("RE", "Procedural Failure"),
    "IIF": ("RE", "Information Integration Failure"),
    "MRF": ("RE", "Mathematical Reasoning Failure"),
    "EF": ("IFE", "Explicit Format"),
    "LC": ("IFE", "Length Constraints"),
    "LgC": ("IFE", "Language Constraints"),
    "CCL": ("IFE", "Complex & Cognitive Load"),
}

# Evaluators (see prism/evaluators):
#   fact_judge     yes/no agreement, otherwise LLM judge of semantic equivalence
#   exact          case-insensitive exact match
#   judge_equiv    LLM judge of semantic equivalence
#   truth_label    [TRUE] / [FALSE] label of the response equals the reference label
#   answer_match   normalized match against the reference answer, otherwise LLM judge
#   abstain        the response is [NO_INFO]
#   choice         extracted option letter equals the reference letter
#   fuzzy          normalized exact or containment match
#   judge_math     LLM judge of mathematical equivalence
#   judge_code     LLM rubric score (0-5) of the generated solution
#   judge_claims   1 - hallucination rate of atomic claims (LLM judge)
#   data_format    output parses as the requested data format
#   ifeval         all IFEval-style instructions of the item are satisfied
#   word_range     word count lies in the required range
#   language       detected response language equals the required language
OPEN_ENDED_EVALUATORS = frozenset({"judge_code", "judge_claims"})


@dataclass(frozen=True)
class Task:
    index: int
    task_id: str
    dimension: str
    subcategory: str
    name: str
    prompt: str
    evaluator: str

    @property
    def data_file(self) -> str:
        return f"{self.dimension}/{self.subcategory}/{self.name}.jsonl"

    @property
    def display_name(self) -> str:
        return f"{self.subcategory}_{self.name.replace('_', ' ')}"

    @property
    def open_ended(self) -> bool:
        return self.evaluator in OPEN_ENDED_EVALUATORS


def _t(index: int, dimension: str, subcategory: str, name: str, prompt: str, evaluator: str) -> Task:
    assert SUBCATEGORIES[subcategory][0] == dimension
    return Task(index, f"{dimension}-{subcategory}-{name}", dimension, subcategory, name, prompt, evaluator)


TASKS: List[Task] = [
    # Knowledge Missing (1-22)
    _t(1, "KM", "NPK", "Private", "KM-NPK", "abstain"),
    _t(2, "KM", "DSK", "SciQ", "KM-DSK-Open", "answer_match"),
    _t(3, "KM", "NPK", "Organizational", "KM-NPK", "abstain"),
    _t(4, "KM", "DSK", "PubMedQA", "KM-DSK", "truth_label"),
    _t(5, "KM", "DSK", "Chinese_SafetyQA", "KM-DSK-Open", "answer_match"),
    _t(6, "KM", "TK", "Numeric", "KM-TK", "abstain"),
    _t(7, "KM", "TK", "Text", "KM-TK", "abstain"),
    _t(8, "KM", "FK", "Biology", "KM-FK", "abstain"),
    _t(9, "KM", "DSK", "RAG-QA-Leaderboard", "KM-DSK", "truth_label"),
    _t(10, "KM", "DSK", "RAG-QA-Leaderboard_Fill", "KM-DSK-Open", "answer_match"),
    _t(11, "KM", "FK", "Literature", "KM-FK", "abstain"),
    _t(12, "KM", "DSK", "StrategyQA", "KM-DSK", "truth_label"),
    _t(13, "KM", "FK", "Awards", "KM-FK", "abstain"),
    _t(14, "KM", "FK", "University", "KM-FK", "abstain"),
    _t(15, "KM", "FK", "Large_Language_Model", "KM-FK", "abstain"),
    _t(16, "KM", "FK", "Competition", "KM-FK", "abstain"),
    _t(17, "KM", "FK", "Festival", "KM-FK", "abstain"),
    _t(18, "KM", "FK", "Country", "KM-FK", "abstain"),
    _t(19, "KM", "FK", "Military", "KM-FK", "abstain"),
    _t(20, "KM", "FK", "Time", "KM-FK", "abstain"),
    _t(21, "KM", "FK", "Phone", "KM-FK", "abstain"),
    _t(22, "KM", "FK", "Dynasty", "KM-FK", "abstain"),
    # Knowledge Error (23-37)
    _t(23, "KE", "FD", "TruthfulQA", "KE-FD", "fact_judge"),
    _t(24, "KE", "EIC", "WhoQA_Entity", "KE-EIC-WhoQA_Entity", "exact"),
    _t(25, "KE", "EIC", "SelfBuilt", "KE-EIC-SelfBuilt", "judge_equiv"),
    _t(26, "KE", "FD", "DefAn", "KE-FD", "exact"),
    _t(27, "KE", "EIC", "WiC", "KE-EIC-WiC", "exact"),
    _t(28, "KE", "IMC", "Text", "KE-IMC", "exact"),
    _t(29, "KE", "IMC", "Numeric", "KE-IMC", "exact"),
    _t(30, "KE", "FD", "Religion", "KE-FD", "fact_judge"),
    _t(31, "KE", "FD", "Sports", "KE-FD", "fact_judge"),
    _t(32, "KE", "FD", "ArtCulture", "KE-FD", "fact_judge"),
    _t(33, "KE", "FD", "LawCrimeMilitary", "KE-FD", "fact_judge"),
    _t(34, "KE", "FD", "FoodCooking", "KE-FD", "fact_judge"),
    _t(35, "KE", "FD", "Business", "KE-FD", "fact_judge"),
    _t(36, "KE", "FD", "Science", "KE-FD", "fact_judge"),
    _t(37, "KE", "FD", "Language", "KE-FD", "fact_judge"),
    # Instruction Following Error (38-55)
    _t(38, "IFE", "LC", "Approximate", "IFE-LC", "word_range"),
    _t(39, "IFE", "CCL", "Math_Reasoning", "IFE-CCL", "ifeval"),
    _t(40, "IFE", "EF", "Data_Schema", "IFE-EF", "data_format"),
    _t(41, "IFE", "EF", "Text_Structure", "IFE-EF", "ifeval"),
    _t(42, "IFE", "CCL", "Length_Format_Mixed", "IFE-CCL", "ifeval"),
    _t(43, "IFE", "LC", "Lower_Bound", "IFE-LC", "word_range"),
    _t(44, "IFE", "LC", "Upper_Bound", "IFE-LC", "word_range"),
    _t(45, "IFE", "CCL", "Keyword_Inclusion", "IFE-CCL", "ifeval"),
    _t(46, "IFE", "LgC", "Chinese", "IFE-LgC", "language"),
    _t(47, "IFE", "LgC", "German", "IFE-LgC", "language"),
    _t(48, "IFE", "LgC", "French", "IFE-LgC", "language"),
    _t(49, "IFE", "LgC", "Russian", "IFE-LgC", "language"),
    _t(50, "IFE", "LgC", "Japanese", "IFE-LgC", "language"),
    _t(51, "IFE", "LgC", "Spanish", "IFE-LgC", "language"),
    _t(52, "IFE", "CCL", "Start_End_Phrase", "IFE-CCL", "ifeval"),
    _t(53, "IFE", "CCL", "No_Comma", "IFE-CCL", "ifeval"),
    _t(54, "IFE", "CCL", "Two_Responses", "IFE-CCL", "ifeval"),
    _t(55, "IFE", "CCL", "Forbidden_Words", "IFE-CCL", "ifeval"),
    # Reasoning Error (56-65)
    _t(56, "RE", "IIF", "Summarize", "RE-IIF-Summarize", "judge_claims"),
    _t(57, "RE", "MRF", "Mathematics", "RE-MRF-Mathematics", "judge_math"),
    _t(58, "RE", "PF", "Subquestion", "RE-PF-Subquestion", "fuzzy"),
    _t(59, "RE", "LF", "Contextual_Inference", "RE-LF-Contextual_Inference", "choice"),
    _t(60, "RE", "IIF", "Simplification", "RE-IIF-Simplification", "judge_claims"),
    _t(61, "RE", "LF", "Critical_Reasoning", "RE-LF-Critical_Reasoning", "choice"),
    _t(62, "RE", "MRF", "Code_Generation", "RE-MRF-Code_Generation", "judge_code"),
    _t(63, "RE", "IIF", "Dialogue_Extraction", "RE-IIF-Dialogue_Extraction", "judge_claims"),
    _t(64, "RE", "LF", "Cognitive_Traps", "RE-LF-Cognitive_Traps", "choice"),
    _t(65, "RE", "PF", "Triplet_Hopping", "RE-PF-Triplet_Hopping", "fuzzy"),
]

TASK_BY_ID: Dict[str, Task] = {t.task_id: t for t in TASKS}


def get_task(task_id: str) -> Task:
    try:
        return TASK_BY_ID[task_id]
    except KeyError as exc:
        raise KeyError(f"unknown task {task_id!r}; run `python scripts/list_tasks.py` for the list") from exc


def select_tasks(patterns: List[str] | None = None) -> List[Task]:
    """Select tasks whose id starts with any of the patterns (e.g. ``KE``, ``RE-LF``); all tasks if empty."""
    if not patterns:
        return list(TASKS)
    selected = [t for t in TASKS if any(t.task_id == p or t.task_id.startswith(p.rstrip("-") + "-") for p in patterns)]
    if not selected:
        raise KeyError(f"no task matches {patterns}")
    return selected
