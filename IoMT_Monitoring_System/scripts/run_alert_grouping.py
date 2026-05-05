from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.settings import get_settings
from export_grouping_input import export_grouping_input


def main() -> None:
    settings = get_settings()
    output_path = Path(settings.alert_module_root) / "data" / "raw" / "master_dataset.csv"
    grouping_script = Path(settings.alert_module_root) / "src" / "monitoring" / "04_alert_grouping.py"

    print(f"Exporting MongoDB sensor logs to {output_path}...")
    row_count = export_grouping_input(output_path)
    print(f"Exported {row_count} rows.")

    print(f"Running alert grouping script: {grouping_script}")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, str(grouping_script)],
        cwd=str(settings.alert_module_root),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    print("Alert grouping workflow complete.")


if __name__ == "__main__":
    main()
