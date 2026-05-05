from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional

from src.common.settings import get_settings
from src.mongo.client import ping_database
from src.mongo.repository import PredictionRepository


BASE_COLUMNS = [
    "created_at",
    "timestamp",
    "device_id",
    "device_type",
    "ward",
    "attack_type",
    "is_attack",
    "priority",
    "priority_confidence",
    "priority_reason",
    "predicted_attack",
    "attack_label",
    "attack_confidence",
    "correlation_verdict",
    "correlation_score",
    "related_alert_count",
    "confirmed_real_attack",
    "confirmed_critical",
    "decision_action",
    "device_state",
    "src_ips",
    "life_support_involved",
    "sensor_log_id",
    "source",
    "mongo_id",
]


def _to_epoch_ms(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        raw = float(value)
        return int(raw if raw > 10_000_000_000 else raw * 1000)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            raw = float(text)
            return int(raw if raw > 10_000_000_000 else raw * 1000)
        except ValueError:
            pass
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return int(parsed.timestamp() * 1000)
        except ValueError:
            return None
    if hasattr(value, "generation_time"):
        return int(value.generation_time.timestamp() * 1000)
    if hasattr(value, "timestamp"):
        try:
            raw = float(value.timestamp())
            return int(raw * 1000 if raw < 10_000_000_000 else raw)
        except (TypeError, ValueError):
            return None
    return None


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on"}:
        return True
    if text in {"false", "0", "no", "n", "off"}:
        return False
    return default


def _flatten_source_ips(document: Dict[str, Any]) -> str:
    analysis = document.get("analysis") or {}
    live_correlation = analysis.get("live_correlation") or {}
    source_ips = live_correlation.get("source_ips") or []
    if isinstance(source_ips, (list, tuple)):
        return ", ".join(str(value) for value in source_ips if str(value).strip())
    return str(source_ips or "")


def _normalized_rows(documents: Iterable[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
    for document in documents:
        timestamp = _to_epoch_ms(document.get("timestamp"))
        if timestamp is None:
            timestamp = _to_epoch_ms(document.get("created_at"))
        if timestamp is None:
            timestamp = _to_epoch_ms(document.get("_id"))
        if timestamp is None:
            continue

        analysis = document.get("analysis") or {}
        attack_prediction = analysis.get("attack_prediction") or {}
        correlation = analysis.get("correlation") or {}
        live_correlation = analysis.get("live_correlation") or {}
        ars_response = analysis.get("ars_response") or {}
        decision = analysis.get("decision") or {}
        alert = analysis.get("alert") or {}

        row = {
            "created_at": str(document.get("created_at", "")),
            "timestamp": timestamp,
            "device_id": str(document.get("device_id", "")),
            "device_type": str(document.get("device_type", "")),
            "ward": str(document.get("ward", "")),
            "attack_type": str(document.get("attack_type", "normal") or "normal"),
            "is_attack": _as_bool(document.get("is_attack", False), False),
            "priority": str(document.get("priority", alert.get("priority", "LOW")) or "LOW"),
            "priority_confidence": document.get("priority_confidence", alert.get("confidence", "")),
            "priority_reason": str(document.get("priority_reason", alert.get("reason", "")) or ""),
            "predicted_attack": _as_bool(document.get("predicted_attack", attack_prediction.get("predicted_attack", False)), False),
            "attack_label": str(document.get("attack_label", attack_prediction.get("predicted_label", "")) or ""),
            "attack_confidence": document.get("attack_confidence", attack_prediction.get("confidence", "")),
            "correlation_verdict": str(document.get("correlation_verdict", live_correlation.get("recommended_verdict", "")) or ""),
            "correlation_score": document.get("correlation_score", live_correlation.get("correlation_score", "")),
            "related_alert_count": document.get("related_alert_count", live_correlation.get("related_alert_count", "")),
            "confirmed_real_attack": _as_bool(document.get("confirmed_real_attack", correlation.get("confirmed_real_attack", False)), False),
            "confirmed_critical": _as_bool(document.get("confirmed_critical", correlation.get("confirmed_critical", False)), False),
            "decision_action": str(document.get("decision_action", decision.get("action", "")) or ""),
            "device_state": str(document.get("device_state", "")),
            "src_ips": _flatten_source_ips(document),
            "life_support_involved": _as_bool(live_correlation.get("life_support_seen", False), False),
            "sensor_log_id": str(document.get("sensor_log_id", "")),
            "source": str(document.get("source", "")),
            "mongo_id": str(document.get("_id", "")),
        }
        yield row


def export_grouping_input(output_path: Path, limit: int = 0) -> int:
    ping_database()
    repo = PredictionRepository()
    cursor = repo.collection.find({}).sort("created_at", 1)
    if limit > 0:
        cursor = cursor.limit(limit)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=BASE_COLUMNS)
        writer.writeheader()
        for row in _normalized_rows(cursor):
            writer.writerow(row)
            row_count += 1

    return row_count


def main() -> None:
    settings = get_settings()
    output_path = Path(settings.alert_module_root) / "data" / "raw" / "master_dataset.csv"
    row_count = export_grouping_input(output_path)
    print(f"Exported {row_count} prediction rows to {output_path}")


if __name__ == "__main__":
    main()
