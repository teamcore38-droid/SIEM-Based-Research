from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.settings import get_settings
from src.mongo.client import ping_database
from src.mongo.repository import SensorLogRepository


BASE_COLUMNS = [
    "timestamp",
    "device_id",
    "device_type",
    "ward",
    "life_support",
    "criticality_tier",
    "protocol",
    "src_ip",
    "dst_port",
    "attack_type",
    "is_attack",
    "sensor_source",
    "device_state",
    "network_blocked",
    "network_isolated",
    "simulation_mode",
    "simulation_note",
    "sensor_available",
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


def _infer_sensor_source(document: Dict[str, Any]) -> str:
    if str(document.get("sensor_source", "")).strip():
        return str(document["sensor_source"])
    if str(document.get("source", "")).strip() and document.get("source") not in {"simulated_live_generator", "simulated"}:
        return str(document["source"])

    device_type = str(document.get("device_type", "")).lower()
    if "pulse" in device_type:
        return "pulse"
    if "ecg" in device_type:
        return "ecg"
    if "temperature" in device_type:
        return "temperature"
    if "motion" in device_type or "fall" in device_type:
        return "motion"
    return "unknown"


def _normalized_rows(documents: Iterable[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
    for document in documents:
        timestamp = _to_epoch_ms(document.get("timestamp"))
        if timestamp is None:
            timestamp = _to_epoch_ms(document.get("created_at"))
        if timestamp is None:
            timestamp = _to_epoch_ms(document.get("_id"))
        if timestamp is None:
            continue

        attack_type = str(document.get("attack_type", "normal") or "normal")
        is_attack = document.get("is_attack")
        if is_attack is None or is_attack == "":
            is_attack = attack_type.lower() != "normal"

        row = {
            "timestamp": timestamp,
            "device_id": str(document.get("device_id", "")),
            "device_type": str(document.get("device_type", "")),
            "ward": str(document.get("ward", "")),
            "life_support": _as_bool(document.get("life_support", False)),
            "criticality_tier": document.get("criticality_tier", 0),
            "protocol": str(document.get("protocol", "")),
            "src_ip": str(document.get("src_ip", "")),
            "dst_port": document.get("dst_port", 0),
            "attack_type": attack_type,
            "is_attack": _as_bool(is_attack, attack_type.lower() != "normal"),
            "sensor_source": _infer_sensor_source(document),
            "device_state": str(document.get("device_state", "")),
            "network_blocked": _as_bool(document.get("network_blocked", False)),
            "network_isolated": _as_bool(document.get("network_isolated", False)),
            "simulation_mode": str(document.get("simulation_mode", "")),
            "simulation_note": str(document.get("simulation_note", "")),
            "sensor_available": _as_bool(document.get("sensor_available", True), True),
            "source": str(document.get("source", "")),
            "mongo_id": str(document.get("_id", "")),
        }
        yield row


def export_grouping_input(output_path: Path, limit: int = 0) -> int:
    ping_database()
    repo = SensorLogRepository()
    cursor = repo.collection.find({}).sort("_id", 1)
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
    parser = argparse.ArgumentParser(
        description="Export MongoDB sensor logs to the alert-grouping master_dataset.csv input."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(settings.alert_module_root) / "data" / "raw" / "master_dataset.csv",
        help="Destination CSV file for the grouping module.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional maximum number of sensor log documents to export.",
    )
    args = parser.parse_args()

    try:
        row_count = export_grouping_input(args.output, limit=args.limit)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Failed to export grouping input: {exc}") from exc

    print(f"Exported {row_count} sensor log rows to {args.output}")
    print("Next step: run src/monitoring/04_alert_grouping.py to regenerate grouped_incidents.csv")


if __name__ == "__main__":
    main()
