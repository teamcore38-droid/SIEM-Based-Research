from __future__ import annotations

import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.api.app import app


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
