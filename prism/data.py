"""Reading and writing PRISM data files (JSON Lines)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Union

from .tasks import Task

REPO_ROOT = Path(__file__).resolve().parent.parent
PathLike = Union[str, os.PathLike]


def data_dir(path: Optional[PathLike] = None) -> Path:
    """Resolve the data directory: explicit argument, then ``$PRISM_DATA_DIR``, then ``<repo>/data``."""
    return Path(path or os.environ.get("PRISM_DATA_DIR") or REPO_ROOT / "data")


def read_jsonl(path: PathLike) -> Iterator[Dict]:
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: PathLike, records: Iterable[Dict], append: bool = False) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a" if append else "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_task(task: Task, directory: Optional[PathLike] = None) -> List[Dict]:
    path = data_dir(directory) / task.data_file
    if not path.exists():
        raise FileNotFoundError(f"{path} not found; set --data-dir or $PRISM_DATA_DIR")
    records = list(read_jsonl(path))
    for record in records:
        if record.get("task") != task.task_id:
            raise ValueError(f"{path}: record {record.get('id')} belongs to {record.get('task')}, expected {task.task_id}")
    return records
