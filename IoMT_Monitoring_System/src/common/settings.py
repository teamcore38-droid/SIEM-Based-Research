from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


COMPONENT_ROOT = Path(__file__).resolve().parents[2]


def _workspace_root() -> Path:
    return COMPONENT_ROOT.parent


WORKSPACE_ROOT = _workspace_root()
DEFAULT_RESEARCH_ROOT = WORKSPACE_ROOT / "final-research-project"
DEFAULT_ALERT_MODULE_ROOT = COMPONENT_ROOT


def _find_mongo_uri_file() -> str:
    search_roots = []
    current = Path.cwd().resolve()
    search_roots.extend([current, *current.parents])
    module_root = Path(__file__).resolve()
    search_roots.extend([module_root.parent, *module_root.parents])
    seen = set()
    for root in search_roots:
        if root in seen:
            continue
        seen.add(root)
        candidate = root / "mongoURI.txt"
        if candidate.exists():
            return candidate.read_text(encoding="utf-8").strip()
    return ""


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else default


def _env_int(name: str, default: int) -> int:
    raw = _env(name, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def _env_path(name: str, default: Path) -> str:
    raw = _env(name)
    return str(Path(raw).expanduser()) if raw else str(default)


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str = _env("MONGODB_URI", _find_mongo_uri_file())
    mongodb_db: str = _env("MONGODB_DB", "siem_db")
    sensor_collection: str = _env("MONGODB_SENSOR_COLLECTION", "sensor_logs")
    response_collection: str = _env("MONGODB_RESPONSE_COLLECTION", "responses")
    device_state_collection: str = _env("MONGODB_DEVICE_STATE_COLLECTION", "device_states")
    prediction_collection: str = _env("MONGODB_PREDICTION_COLLECTION", "predictions")
    replay_delay_ms: int = _env_int("REPLAY_DELAY_MS", 0)
    dry_run: bool = _env("DRY_RUN", "1") not in {"0", "false", "False"}
    device_control_transport: str = _env("DEVICE_CONTROL_TRANSPORT", "auto").lower()
    device_control_endpoint: str = _env("DEVICE_CONTROL_ENDPOINT")
    device_control_mqtt_broker: str = _env("DEVICE_CONTROL_MQTT_BROKER")
    device_control_mqtt_port: int = _env_int("DEVICE_CONTROL_MQTT_PORT", 1883)
    device_control_mqtt_username: str = _env("DEVICE_CONTROL_MQTT_USERNAME")
    device_control_mqtt_password: str = _env("DEVICE_CONTROL_MQTT_PASSWORD")
    device_control_mqtt_client_id: str = _env("DEVICE_CONTROL_MQTT_CLIENT_ID")
    device_control_mqtt_keepalive: int = _env_int("DEVICE_CONTROL_MQTT_KEEPALIVE", 60)
    device_control_mqtt_qos: int = _env_int("DEVICE_CONTROL_MQTT_QOS", 1)
    cors_origins: str = _env("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001")
    component_root: str = str(COMPONENT_ROOT)
    research_root: str = _env_path("RESEARCH_PROJECT_ROOT", DEFAULT_RESEARCH_ROOT)
    alert_module_root: str = _env_path("ALERT_MODULE_ROOT", DEFAULT_ALERT_MODULE_ROOT)


def get_settings() -> Settings:
    return Settings()
