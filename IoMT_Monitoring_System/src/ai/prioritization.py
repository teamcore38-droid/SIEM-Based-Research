from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from src.common.models import AlertDecision


FEATURES = [
    "criticality_tier",
    "life_support_int",
    "is_attack_int",
    "dst_port",
    "device_type_enc",
    "ward_enc",
    "protocol_enc",
    "attack_type_enc",
    "sensor_source_enc",
    "is_icu",
    "is_port_anomaly",
    "is_unknown_device",
    "is_protocol_anomaly",
]


class PriorityModelBundle:
    def __init__(self, model, encoders, feature_names):
        self.model = model
        self.encoders = encoders
        self.feature_names = feature_names

    @classmethod
    def load(cls, models_dir: Path):
        with (models_dir / "alert_prioritization_model.pkl").open("rb") as handle:
            model = pickle.load(handle)
        with (models_dir / "label_encoders.pkl").open("rb") as handle:
            encoders = pickle.load(handle)
        with (models_dir / "feature_names.pkl").open("rb") as handle:
            feature_names = pickle.load(handle)
        return cls(model, encoders, feature_names)

    def _encode(self, column: str, value: Any) -> int:
        encoder = self.encoders.get(column)
        if encoder is None:
            return 0
        value = str(value)
        return int(encoder.transform([value])[0]) if value in encoder.classes_ else 0

    def _infer_sensor_source(self, document: Dict[str, Any]) -> str:
        if document.get("sensor_source"):
            return str(document["sensor_source"])
        device_type = str(document.get("device_type", "")).lower()
        if "pulse" in device_type:
            return "pulse"
        if "ecg" in device_type:
            return "ecg"
        if "temperature" in device_type:
            return "temperature"
        if "motion" in device_type or "fall" in device_type:
            return "motion"
        source_file = str(document.get("source_file", "")).lower()
        if "pulse" in source_file:
            return "pulse"
        if "ecg" in source_file:
            return "ecg"
        if "temperature" in source_file:
            return "temperature"
        if "motion" in source_file:
            return "motion"
        return "pulse"

    def _is_attack(self, document: Dict[str, Any]) -> bool:
        raw_flag = str(document.get("is_attack", "")).lower()
        if raw_flag in {"true", "1"}:
            return True
        attack_type = str(document.get("attack_type", "normal")).lower()
        return attack_type not in {"", "normal", "none", "0", "-1"}

    def build_features(self, document: Dict[str, Any]) -> pd.DataFrame:
        source_value = self._infer_sensor_source(document)
        is_attack = self._is_attack(document)
        row = {
            "criticality_tier": int(document.get("criticality_tier", 0) or 0),
            "life_support_int": 1 if str(document.get("life_support", "")).lower() in {"true", "1"} else 0,
            "is_attack_int": 1 if is_attack else 0,
            "dst_port": int(document.get("dst_port", 0) or 0),
            "device_type_enc": self._encode("device_type", document.get("device_type", "")),
            "ward_enc": self._encode("ward", document.get("ward", "")),
            "protocol_enc": self._encode("protocol", document.get("protocol", "")),
            "attack_type_enc": self._encode("attack_type", document.get("attack_type", "")),
            "sensor_source_enc": self._encode("sensor_source", source_value),
            "is_icu": 1 if document.get("ward") == "ICU" else 0,
            "is_port_anomaly": 1 if int(document.get("dst_port", 1883) or 1883) != 1883 else 0,
            "is_unknown_device": 1 if any(token in str(document.get("device_id", "")).upper() for token in ["UNKNOWN", "ROGUE", "FAKE", "GHOST", "CLONE"]) else 0,
            "is_protocol_anomaly": 0 if document.get("protocol") in {"MQTT", "BLE_MQTT"} else 1,
        }
        return pd.DataFrame([row])[self.feature_names]

    def predict(self, document: Dict[str, Any]) -> AlertDecision:
        features = self.build_features(document)
        priority = self.model.predict(features)[0]
        confidence = 0.0
        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(features)[0]
            classes = list(self.model.classes_)
            confidence = float(probabilities[classes.index(priority)])
        reason = f"Predicted {priority} from trained Random Forest priority model."
        return AlertDecision(
            device_id=str(document.get("device_id", "")),
            priority=str(priority),
            confidence=confidence,
            reason=reason,
            should_escalate=str(priority) in {"CRITICAL", "HIGH"},
            should_quarantine=str(priority) == "CRITICAL",
            should_shutdown=False,
            source_timestamp=document.get("timestamp"),
            metadata={"priority": priority},
        )
