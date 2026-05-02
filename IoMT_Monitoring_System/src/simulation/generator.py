from __future__ import annotations

import itertools
import random
import threading
import time
from typing import Any, Dict, List

from src.simulation.config import DEFAULT_ANOMALY_TYPE, SimulationConfig


DEVICE_PROFILES = [
    {
        "device_id": "890cc34f",
        "device_type": "ESP32_Pulse_Oximeter",
        "ward": "CRITICAL_CARE",
        "life_support": True,
        "criticality_tier": 9,
        "protocol": "MQTT",
        "src_ip": "10.86.xxx.xxx",
        "sensor_source": "pulse",
    },
    {
        "device_id": "ECG_ESP32_001",
        "device_type": "ESP32_ECG_Monitor",
        "ward": "Ward_02",
        "life_support": False,
        "criticality_tier": 7,
        "protocol": "BLE_MQTT",
        "src_ip": "10.38.16.20",
        "sensor_source": "ecg",
    },
    {
        "device_id": "TEMP_ESP32_001",
        "device_type": "ESP32_Temperature_Monitor",
        "ward": "General_Ward",
        "life_support": False,
        "criticality_tier": 6,
        "protocol": "MQTT",
        "src_ip": "10.18.166.210",
        "sensor_source": "temperature",
    },
    {
        "device_id": "MOTION_ESP32_001",
        "device_type": "ESP32_Fall_Detection_Motion",
        "ward": "Ward_01",
        "life_support": False,
        "criticality_tier": 5,
        "protocol": "BLE_MQTT",
        "src_ip": "10.98.160.21",
        "sensor_source": "motion",
    },
]

_DEVICE_PROFILE_CYCLE = itertools.cycle(DEVICE_PROFILES)
_PROFILE_LOCK = threading.Lock()

ATTACK_TYPES = [
    "normal",
    "normal",
    "normal",
    "sensor_spoofing",
    "mqtt_port_manipulation",
    "device_identity_spoofing",
    "protocol_anomaly",
    "flooding",
    "ip_spoofing",
    "data_tampering",
    "ddos",
]

MODEL_DETECTABLE_DEFAULT_ANOMALIES = {
    "pulse": "sensor_spoofing",
    "ecg": "sensor_spoofing",
    "temperature": "device_identity_spoofing",
    "motion": "device_identity_spoofing",
}


def _normal_document(profile: Dict[str, Any], attack_type: str, is_attack: bool) -> Dict[str, Any]:
    return {
        **profile,
        "timestamp": int(time.time() * 1000),
        "dst_port": 1883,
        "attack_type": attack_type,
        "is_attack": is_attack,
        "source": "simulated_live_generator",
        "sensor_available": True,
    }


def _attack_for_config(profile: Dict[str, Any], config: SimulationConfig | None) -> tuple[str, bool, bool]:
    if config is None:
        attack_type = random.choice(ATTACK_TYPES)
        return attack_type, attack_type != "normal", False

    if config.simulation_mode == "normal":
        return "normal", False, False

    is_target = bool(config.anomaly_device_id) and profile["device_id"] == config.anomaly_device_id
    if not is_target:
        return "normal", False, False
    anomaly_type = config.anomaly_type or DEFAULT_ANOMALY_TYPE
    if anomaly_type == DEFAULT_ANOMALY_TYPE:
        anomaly_type = MODEL_DETECTABLE_DEFAULT_ANOMALIES.get(
            str(profile.get("sensor_source", "")),
            DEFAULT_ANOMALY_TYPE,
        )
    return anomaly_type, True, True


def _profile_for_config(config: SimulationConfig | None) -> Dict[str, Any]:
    if config and config.simulation_mode == "anomaly" and config.anomaly_device_id:
        target = next((profile for profile in DEVICE_PROFILES if profile["device_id"] == config.anomaly_device_id), None)
        if target is not None:
            return dict(target)

    with _PROFILE_LOCK:
        return dict(next(_DEVICE_PROFILE_CYCLE))


def generate_sensor_event_for_profile(
    profile: Dict[str, Any],
    config: SimulationConfig | None = None,
    force_normal: bool = False,
) -> Dict[str, Any]:
    original_config = config
    if force_normal and config is not None:
        config = SimulationConfig(
            data_mode=config.data_mode,
            simulation_mode="normal",
            anomaly_device_id=config.anomaly_device_id,
            anomaly_type=config.anomaly_type,
        )
    attack_type, is_attack, targeted_anomaly = _attack_for_config(profile, config)
    document: Dict[str, Any] = _normal_document(profile, attack_type, is_attack)
    if original_config is not None:
        document["simulation_mode"] = original_config.simulation_mode
        document["simulated_anomaly_target"] = targeted_anomaly

    if attack_type == "mqtt_port_manipulation":
        document["dst_port"] = random.choice([4444, 8883, 1884])
    if targeted_anomaly and attack_type in {"sensor_spoofing", "device_identity_spoofing"}:
        document["dst_port"] = random.choice([4444, 8883, 1884])
        document["controlled_anomaly_evidence"] = "sensor_outlier_with_network_indicator"
    if attack_type == "protocol_anomaly":
        document["protocol"] = random.choice(["HTTP", "UNKNOWN", "CoAP"])
    if attack_type == "ip_spoofing":
        document["src_ip"] = f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"

    device_type = profile["device_type"]
    if "Pulse" in device_type:
        heart_rate = random.randint(58, 105)
        if is_attack:
            heart_rate = random.choice([42, 138, 152])
        document.update({"heart_rate_bpm_pulse": heart_rate, "ppg_raw_value": random.randint(25000, 29000)})
    elif "ECG" in device_type:
        rhythm = "NORMAL_SINUS"
        if is_attack:
            rhythm = random.choice(["AFIB", "VTACH", "BRADYCARDIA"])
        document.update({
            "ecg_raw_value": random.randint(1800, 2300),
            "heart_rate_bpm": random.choice([38, 142, 156]) if is_attack else random.randint(60, 110),
            "r_peak_detected": True,
            "rhythm_label": rhythm,
        })
    elif "Temperature" in device_type:
        temperature = round(random.uniform(35.8, 37.7), 1)
        if is_attack:
            temperature = random.choice([33.5, 40.2, 41.0])
        document["temperature_celsius"] = temperature
    else:
        fall = is_attack
        document.update({
            "accel_x": round(random.uniform(-1.5, 1.5), 4),
            "accel_y": round(random.uniform(-1.5, 1.5), 4),
            "accel_z": round(random.uniform(16.0, 22.0), 4) if is_attack else round(random.uniform(8.0, 10.5), 4),
            "gyro_x": round(random.uniform(-0.3, 0.3), 4),
            "gyro_y": round(random.uniform(-0.3, 0.3), 4),
            "gyro_z": round(random.uniform(-0.3, 0.3), 4),
            "fall_detected": fall,
            "posture_event": "FALL" if fall else random.choice(["SITTING", "STANDING", "LYING"]),
        })

    return document


def generate_sensor_event(config: SimulationConfig | None = None) -> Dict[str, Any]:
    return generate_sensor_event_for_profile(_profile_for_config(config), config)


def generate_sensor_events(config: SimulationConfig | None = None) -> List[Dict[str, Any]]:
    if not config or config.simulation_mode != "anomaly" or not config.anomaly_device_id:
        return [generate_sensor_event(config)]

    target = next((profile for profile in DEVICE_PROFILES if profile["device_id"] == config.anomaly_device_id), None)
    normal_profiles = [profile for profile in DEVICE_PROFILES if profile["device_id"] != config.anomaly_device_id]
    events: List[Dict[str, Any]] = []
    if target is not None:
        events.append(generate_sensor_event_for_profile(dict(target), config))
    events.extend(generate_sensor_event_for_profile(dict(profile), config, force_normal=True) for profile in normal_profiles)
    return events
