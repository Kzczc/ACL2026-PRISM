"""Task prompts and the construction of model inputs.

Every request is a single user message: the task prompt, a blank line, and the formatted question.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict

from .data import REPO_ROOT
from .tasks import Task

PROMPT_DIR = REPO_ROOT / "prompts"


@lru_cache(maxsize=None)
def read_prompt(relative_path: str) -> str:
    path = PROMPT_DIR / relative_path
    if not path.exists():
        raise FileNotFoundError(f"prompt file {path} not found")
    return path.read_text(encoding="utf-8").strip()


def task_prompt(task: Task) -> str:
    return read_prompt(f"tasks/{task.prompt}.md")


def format_question(record: Dict, task: Task) -> str:
    """Render the question text of a record, including options, procedures, or test inputs."""
    question = str(record["question"])
    if task.subcategory == "LF" and record.get("options"):
        options = "\n".join(f"{chr(65 + i)}. {option}" for i, option in enumerate(record["options"]))
        question += f"\n\nOptions:\n{options}\n"
    elif task.subcategory == "PF" and record.get("procedure"):
        steps = record["procedure"]
        if isinstance(steps, list):
            body = "\n".join(str(step) for step in steps) + "\n"
        else:
            body = str(steps)
        question += f"\n\nProcedure:\n{body}"
    elif task.task_id == "RE-MRF-Code_Generation" and record.get("test_input"):
        question += f"\n\nTest Input:\n{record['test_input']}"
    return question


def build_prompt(record: Dict, task: Task) -> str:
    return f"{task_prompt(task)}\n\n{format_question(record, task)}"


def fill_template(template: str, **values: str) -> str:
    """Replace ``{name}`` placeholders without interpreting other braces (judge prompts contain JSON)."""
    for key, value in values.items():
        template = template.replace("{" + key + "}", str(value))
    return template
