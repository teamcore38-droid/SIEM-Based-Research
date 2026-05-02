from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class HardwareDeviceProfile:
    device_id: str
    device_type: str
    ward: str
    life_support: bool
    criticality_tier: int
    protocol: str
    telemetry_topic: str
    command_topic: str
    aliases: tuple[str, ...] = ()
    notes: str = ""


HARDWARE_DEVICE_PROFILES: tuple[HardwareDeviceProfile, ...] = (
    HardwareDeviceProfile(
        device_id="PULSE_ESP32_001",
        device_type="ESP32_Pulse_Oximeter",
        ward="ICU",
        life_support=True,
        criticality_tier=9,
        protocol="MQTT",
        telemetry_topic="hospital/iomt/pulse",
        command_topic="hospital/iomt/command/PULSE_ESP32_001",
        aliases=("890cc34f", "ESP32_Pulse_Oximeter"),
        notes="MAX30105 pulse/heart-rate sensor",
    ),
    HardwareDeviceProfile(
        device_id="ECG_ESP32_001",
        device_type="ESP32_ECG_Monitor",
        ward="Ward 01",
        life_support=False,
        criticality_tier=10,
        protocol="MQTT",
        telemetry_topic="hospital/iomt/ecg",
        command_topic="hospital/iomt/command/ECG_ESP32_001",
        aliases=("ESP32_ECG_Monitor",),
        notes="ECG/lead sensor",
    ),
    HardwareDeviceProfile(
        device_id="TEMP_ESP32_003",
        device_type="ESP32_Temperature_Sensor",
        ward="General Ward",
        life_support=False,
        criticality_tier=5,
        protocol="MQTT",
        telemetry_topic="hospital/iomt/temperature",
        command_topic="hospital/iomt/command/TEMP_ESP32_003",
        aliases=("TEMP_ESP32_001", "ESP32_Temperature_Monitor"),
        notes="Temperature sensor",
    ),
    HardwareDeviceProfile(
        device_id="FALL_ESP32_004",
        device_type="ESP32_Fall_Detector",
        ward="ICU",
        life_support=False,
        criticality_tier=9,
        protocol="MQTT",
        telemetry_topic="hospital/iomt/fall",
        command_topic="hospital/iomt/command/FALL_ESP32_004",
        aliases=("MOTION_ESP32_001", "ESP32_Fall_Detection_Motion"),
        notes="MPU6050 fall detector",
    ),
)

_PROFILES_BY_ID: Dict[str, HardwareDeviceProfile] = {profile.device_id: profile for profile in HARDWARE_DEVICE_PROFILES}
_ALIASES: Dict[str, str] = {
    alias: profile.device_id
    for profile in HARDWARE_DEVICE_PROFILES
    for alias in profile.aliases
}

ACTION_TO_COMMAND: Dict[str, str] = {
    "temporary_isolate": "TEMPORARY_ISOLATE",
    "quarantine": "PERMANENT_QUARANTINE",
    "shutdown": "PERMANENT_QUARANTINE",
    "rollback": "ROLLBACK",
    "restore": "ALL_CLEAR",
    "monitor": "MONITOR",
    "log_and_monitor": "MONITOR",
}


def resolve_hardware_device(device_id: str) -> Optional[HardwareDeviceProfile]:
    canonical_id = _ALIASES.get(device_id, device_id)
    return _PROFILES_BY_ID.get(canonical_id)


def resolve_command_name(action: str) -> str:
    normalized = action.strip().lower()
    if normalized in ACTION_TO_COMMAND:
        return ACTION_TO_COMMAND[normalized]
    upper = action.strip().upper()
    if upper in ACTION_TO_COMMAND.values():
        return upper
    return upper or "MONITOR"


def build_control_message(
    command_id: str,
    device_id: str,
    action: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    target = resolve_hardware_device(device_id)
    command_name = resolve_command_name(action)
    resolved_device_id = target.device_id if target is not None else device_id
    command_topic = target.command_topic if target is not None else f"hospital/iomt/command/{resolved_device_id}"

    payload: Dict[str, Any] = {
        "command": command_name,
        "requested_action": action,
        "command_id": command_id,
        "device_id": resolved_device_id,
        "source_device_id": device_id,
        "command_topic": command_topic,
        "telemetry_topic": target.telemetry_topic if target is not None else None,
    }
    if metadata:
        payload["metadata"] = metadata
    if command_name == "PERMANENT_QUARANTINE" and action.strip().lower() == "shutdown":
        payload["power_state"] = "off"
    return payload


def hardware_device_roster() -> List[Dict[str, Any]]:
    return [asdict(profile) for profile in HARDWARE_DEVICE_PROFILES]

