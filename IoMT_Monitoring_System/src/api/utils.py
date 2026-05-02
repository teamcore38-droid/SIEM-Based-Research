from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if value.__class__.__name__ == "ObjectId":
        return str(value)
    return value


def read_csv_records(path: Path, limit: int = 100) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    frame = pd.read_csv(path)
    if limit > 0:
        frame = frame.tail(limit)
    return [json_safe(row) for row in frame.fillna("").to_dict(orient="records")]


def read_text(path: Path, fallback: str = "") -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else fallback
