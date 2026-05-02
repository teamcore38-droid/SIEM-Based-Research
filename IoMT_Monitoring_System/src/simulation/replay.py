from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

from src.common.settings import get_settings


def infer_sensor_source(path: Path) -> str:
    stem = path.stem.lower()
    if "pulse" in stem:
        return "pulse"
    if "ecg" in stem:
        return "ecg"
    if "temperature" in stem:
        return "temperature"
    if "motion" in stem:
        return "motion"
    return stem


def _coerce(value: str):
    text = value.strip()
    if text.upper() in {"TRUE", "FALSE"}:
        return text.upper() == "TRUE"
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def load_csv_documents(paths: Iterable[Path]) -> Iterator[Dict]:
    for path in paths:
        if not path.exists():
            continue
        sensor_source = infer_sensor_source(path)
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                document = {key: _coerce(value) for key, value in row.items()}
                document["source_file"] = path.name
                document["sensor_source"] = sensor_source
                yield document


def replay_documents(documents: Iterable[Dict], collection, delay_ms: Optional[int] = None, dry_run: bool = True) -> int:
    settings = get_settings()
    pause_ms = settings.replay_delay_ms if delay_ms is None else delay_ms
    inserted = 0
    for document in documents:
        if dry_run or settings.dry_run:
            print(f"[DRY RUN] {document.get('device_id')} -> {document.get('attack_type')}")
        else:
            collection.insert_one(document)
        inserted += 1
        if pause_ms > 0:
            time.sleep(pause_ms / 1000.0)
    return inserted
