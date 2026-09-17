"""LLM judge used by the open-ended and semantic-matching evaluators (Appendix J of the paper)."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from .client import ChatClient, is_failed
from .prompts import fill_template, read_prompt

CLAIM_PROMPTS = {
    "RE-IIF-Summarize": "judges/RE-IIF-Summarize.md",
    "RE-IIF-Simplification": "judges/RE-IIF-Simplification.md",
    "RE-IIF-Dialogue_Extraction": "judges/RE-IIF-Dialogue_Extraction.md",
}
CODE_DIMENSIONS = ("correctness", "completeness", "efficiency", "readability")


def parse_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Parse the first JSON object in a judge response."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    for candidate in (text, *re.findall(r"\{.*?\}", text, flags=re.DOTALL)):
        try:
            value = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    return None


class Judge:
    """Wraps a chat model with the judging prompts. The paper uses GPT-4o as the judge."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.client = ChatClient(config)
        self.name = self.client.name
        self.attempts = int(config.get("parse_attempts", 3))

    def _ask(self, prompt: str, temperature: float, max_tokens: int = 512) -> str:
        return self.client.complete(prompt, temperature=temperature, top_p=None, max_tokens=max_tokens)

    def _ask_json(self, prompt: str, temperature: float, required: tuple) -> Optional[Dict[str, Any]]:
        for _ in range(self.attempts):
            reply = self._ask(prompt, temperature)
            if is_failed(reply):
                continue
            value = parse_json_object(reply)
            if value is not None and all(k in value for k in required):
                return value
        return None

    def equivalent(self, response: str, reference: str) -> Dict[str, Any]:
        prompt = fill_template(read_prompt("judges/semantic_equivalence.md"), model_answer=response, reference=reference)
        for _ in range(self.attempts):
            reply = self._ask(prompt, temperature=0.0, max_tokens=16)
            if not is_failed(reply):
                return {"correct": "YES" in reply.upper(), "judge_reply": reply}
        return {"correct": False, "judge_error": True}

    def math_equivalent(self, question: str, reference: str, response: str) -> Dict[str, Any]:
        prompt = fill_template(read_prompt("judges/math_equivalence.md"),
                               question=question, reference=reference, model_answer=response)
        value = self._ask_json(prompt, temperature=0.1, required=("correct",))
        if value is None:
            return {"correct": False, "judge_error": True}
        return {"correct": str(value["correct"]).strip() in ("1", "True", "true")}

    def code_score(self, question: str, test_input: str, test_output: str, response: str) -> Dict[str, Any]:
        prompt = fill_template(read_prompt("judges/RE-MRF-Code_Generation.md"), question=question,
                               test_input=test_input, test_output=test_output, model_answer=response)
        value = self._ask_json(prompt, temperature=0.1, required=CODE_DIMENSIONS)
        if value is None:
            return {"total": 0, "judge_error": True}
        dims = {k: max(0.0, min(10.0, float(value[k]))) for k in CODE_DIMENSIONS}
        # Total follows Appendix J.2: round((sum of the four scores) / 40 x 5).
        total = int(round(sum(dims.values()) / 40 * 5))
        return {**dims, "total": total}

    def claim_hallucination(self, task_id: str, question: str, response: str) -> Dict[str, Any]:
        prompt = fill_template(read_prompt(CLAIM_PROMPTS[task_id]), question=question, model_answer=response)
        value = self._ask_json(prompt, temperature=0.1, required=("total_claims", "hallucinated_claims"))
        if value is None:
            return {"hallucination_rate": 1.0, "judge_error": True}
        total = max(0, int(value["total_claims"]))
        wrong = max(0, int(value["hallucinated_claims"]))
        rate = min(1.0, wrong / total) if total else float(value.get("hallucination_rate", 0.0) or 0.0)
        return {"total_claims": total, "hallucinated_claims": wrong, "hallucination_rate": rate}
