from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.mongo.repository import SensorLogRepository
from src.common.settings import get_settings
from src.simulation.replay import load_csv_documents, replay_documents


def main():
    settings = get_settings()
    raw_dir = Path(settings.alert_module_root) / "data" / "raw"
    repo = SensorLogRepository()
    documents = load_csv_documents(sorted(raw_dir.glob("*_sensor_log.csv")))
    inserted = replay_documents(documents, repo.collection, delay_ms=0, dry_run=False)
    print(f"Inserted {inserted} simulated sensor events into MongoDB.")


if __name__ == "__main__":
    main()
