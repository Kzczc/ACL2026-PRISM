"""OpenAI-compatible chat client with retries and concurrent requests."""

from __future__ import annotations

import logging
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

ERROR_PREFIX = "ERROR:"
_THINK = re.compile(r"<think>.*?</think>", flags=re.DOTALL)


def strip_reasoning(text: str) -> str:
    """Remove ``<think>...</think>`` blocks emitted by some reasoning models."""
    text = _THINK.sub("", text)
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    return text.strip()


class ChatClient:
    """Sends single-turn chat requests to an OpenAI-compatible endpoint.

    Config keys: ``model`` (served model name), ``base_url`` (endpoint; empty for api.openai.com),
    ``api_key_env`` (environment variable holding the key), ``max_tokens``, ``supports_top_p``,
    ``strip_reasoning``, ``extra_body`` (provider-specific fields), ``max_workers``, ``max_retries``,
    ``timeout``.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        from openai import OpenAI

        key_env = config.get("api_key_env", "OPENAI_API_KEY")
        api_key = os.environ.get(key_env)
        if not api_key:
            raise RuntimeError(f"environment variable {key_env} is not set (see .env.example)")
        if not config.get("model"):
            raise ValueError(f"model {config.get('name')!r} has no served model name; check configs/models.yaml")
        self.name = config.get("name", config["model"])
        self.model = config["model"]
        self.max_tokens = int(config.get("max_tokens", 16384))
        self.supports_top_p = bool(config.get("supports_top_p", True))
        self.strip = bool(config.get("strip_reasoning", True))
        self.extra_body = config.get("extra_body") or None
        self.max_workers = int(config.get("max_workers", 20))
        self.max_retries = int(config.get("max_retries", 3))
        self.client = OpenAI(api_key=api_key, base_url=config.get("base_url") or None,
                             timeout=float(config.get("timeout", 300)), max_retries=0)

    def complete(self, prompt: str, temperature: float, top_p: Optional[float] = None,
                 max_tokens: Optional[int] = None) -> str:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        if top_p is not None and self.supports_top_p:
            kwargs["top_p"] = top_p
        if self.extra_body:
            kwargs["extra_body"] = self.extra_body
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(**kwargs)
                text = response.choices[0].message.content or ""
                return strip_reasoning(text) if self.strip else text.strip()
            except Exception as exc:  # network errors, rate limits, server errors
                last_error = exc
                if attempt < self.max_retries - 1:
                    delay = min(60.0, 5.0 * 2 ** attempt) + random.random()
                    logger.warning("%s: request failed (%s); retrying in %.0f s", self.name, exc, delay)
                    time.sleep(delay)
        return f"{ERROR_PREFIX} {last_error}"

    def complete_many(self, prompts: Sequence[str], temperature: float, top_p: Optional[float] = None,
                      max_tokens: Optional[int] = None) -> List[str]:
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            return list(pool.map(lambda p: self.complete(p, temperature, top_p, max_tokens), prompts))


def is_failed(response: Optional[str]) -> bool:
    """A response is failed when it is missing, empty, or an API error."""
    return response is None or not str(response).strip() or str(response).startswith(ERROR_PREFIX)
