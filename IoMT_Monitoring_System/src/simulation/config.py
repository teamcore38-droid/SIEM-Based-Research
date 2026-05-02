from __future__ import annotations

import threading
from dataclasses import asdict, dataclass
from typing import Any, Dict


VALID_DATA_MODES = {"real", "simulation"}
VALID_SIMULATION_MODES = {"normal", "anomaly"}
DEFAULT_ANOMALY_TYPE = "sensor_spoofing"


@dataclass
class SimulationConfig:
    data_mode: str = "simulation"
    simulation_mode: str = "normal"
    anomaly_device_id: str = ""
    anomaly_type: str = DEFAULT_ANOMALY_TYPE

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SimulationConfigStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._config = SimulationConfig()

    def get(self) -> SimulationConfig:
        with self._lock:
            return SimulationConfig(**self._config.to_dict())

    def update(self, **changes: Any) -> SimulationConfig:
        with self._lock:
            next_config = SimulationConfig(**self._config.to_dict())
            data_mode_value = changes.get("data_mode")
            simulation_mode_value = changes.get("simulation_mode")
            anomaly_device_id_value = changes.get("anomaly_device_id")
            anomaly_type_value = changes.get("anomaly_type")

            data_mode = str(data_mode_value if data_mode_value is not None else next_config.data_mode).lower()
            simulation_mode = str(
                simulation_mode_value if simulation_mode_value is not None else next_config.simulation_mode
            ).lower()
            next_config.data_mode = data_mode if data_mode in VALID_DATA_MODES else "simulation"
            next_config.simulation_mode = simulation_mode if simulation_mode in VALID_SIMULATION_MODES else "normal"
            if anomaly_device_id_value is not None:
                next_config.anomaly_device_id = str(anomaly_device_id_value or "")
            if anomaly_type_value is not None:
                next_config.anomaly_type = str(anomaly_type_value or DEFAULT_ANOMALY_TYPE)
            self._config = next_config
            return SimulationConfig(**self._config.to_dict())


_STORE = SimulationConfigStore()


def simulation_config_store() -> SimulationConfigStore:
    return _STORE
