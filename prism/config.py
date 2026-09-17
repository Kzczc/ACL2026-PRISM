"""Model registry loaded from ``configs/models.yaml``.

Values of the form ``${NAME}`` or ``${NAME:-default}`` are read from environment variables, so no
API key, endpoint, or local model path is stored in the repository.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .data import REPO_ROOT

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")
DEFAULT_MODEL_CONFIG = REPO_ROOT / "configs" / "models.yaml"


def _expand(value: Any) -> Any:
    if isinstance(value, str):
        return _ENV_PATTERN.sub(lambda m: os.environ.get(m.group(1), m.group(2) or ""), value)
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v) for v in value]
    return value


def load_registry(path: Optional[Union[str, os.PathLike]] = None) -> Dict[str, Any]:
    import yaml

    config_path = Path(path or DEFAULT_MODEL_CONFIG)
    with config_path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_model_config(name: str, path: Optional[Union[str, os.PathLike]] = None) -> Dict[str, Any]:
    registry = load_registry(path)
    models = registry.get("models", {})
    if name not in models:
        raise KeyError(f"model {name!r} is not defined in the model registry; available: {sorted(models)}")
    config = dict(registry.get("defaults", {}))
    config.update(models[name] or {})
    config = _expand(config)
    config.setdefault("name", name)
    return config


def load_judge_config(path: Optional[Union[str, os.PathLike]] = None) -> Dict[str, Any]:
    registry = load_registry(path)
    if "judge" not in registry:
        raise KeyError("the model registry has no `judge` entry")
    config = _expand(dict(registry["judge"]))
    config.setdefault("name", "judge")
    return config
