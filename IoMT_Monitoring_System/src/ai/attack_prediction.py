from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable

import joblib
import numpy as np
import pandas as pd

from src.common.models import AttackPrediction


LABEL_MAP = {
    0: "BENIGN",
    1: "ATTACK",
    2: "UNKNOWN_OR_NO_SIGNAL",
}


class AttackPredictionBundle:
    """
    Wrapper around the latest AI Threat Intel artifacts.

    The new bundle includes the saved categorical encoders, so the live backend
    now uses those encoders directly instead of the older manual mapping shim.
    """

    def __init__(
        self,
        rf_model,
        rf_features: Iterable[str],
        iso_model,
        iso_features: Iterable[str],
        encoders: Dict[str, Any],
    ):
        self.rf_model = rf_model
        self.rf_features = list(rf_features)
        self.iso_model = iso_model
        self.iso_features = list(iso_features)
        self.encoders = encoders or {}

    @classmethod
    def load(cls, threat_intel_dir: Path):
        rf_model = joblib.load(threat_intel_dir / "random_forest_model.pkl")
        rf_features = joblib.load(threat_intel_dir / "rf_features.pkl")
        iso_model = joblib.load(threat_intel_dir / "isolation_forest_model.pkl")
        iso_features = joblib.load(threat_intel_dir / "iso_features.pkl")
        encoders = joblib.load(threat_intel_dir / "encoders.pkl")
        if not isinstance(encoders, dict):
            raise TypeError("AI Threat Intel encoders.pkl must contain a dictionary of encoders")
        return cls(rf_model, rf_features, iso_model, iso_features, encoders)

    def _is_missing(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and value.strip().lower() in {"", "nan", "none", "null"}:
            return True
        try:
            return bool(pd.isna(value))
        except Exception:
            return False

    def _numeric(self, value: Any, default: float = 0.0) -> float:
        if self._is_missing(value):
            return default
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, (int, float, np.integer, np.floating)):
            try:
                if pd.isna(value):
                    return default
            except Exception:
                pass
            return float(value)
        try:
            return float(str(value).replace("xxx", "0"))
        except ValueError:
            return default

    def _integer(self, value: Any, default: int = 0) -> int:
        numeric = self._numeric(value, default=float(default))
        try:
            return int(round(numeric))
        except (TypeError, ValueError):
            return default

    def _timestamp(self, value: Any) -> float:
        if self._is_missing(value):
            return 0.0
        if isinstance(value, (int, float, np.integer, np.floating)):
            return float(value)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000
            except ValueError:
                return self._numeric(value)
        if hasattr(value, "timestamp"):
            return float(value.timestamp()) * 1000
        return self._numeric(value)

    def _missing_encoded_value(self, encoder) -> int:
        try:
            return int(encoder.transform([np.nan])[0])
        except Exception:
            return 0

    def _encode_categorical(self, feature: str, value: Any) -> int:
        encoder = self.encoders.get(feature)
        if encoder is None:
            return self._integer(value)

        if self._is_missing(value):
            return self._missing_encoded_value(encoder)

        if isinstance(value, (int, float, np.integer, np.floating)) and not pd.isna(value):
            numeric_value = int(value)
            if float(value).is_integer() and 0 <= numeric_value < len(encoder.classes_):
                return numeric_value

        if isinstance(value, bool):
            normalized = "True" if value else "False"
            if normalized in encoder.classes_:
                return int(encoder.transform([normalized])[0])

        text_candidates = [
            str(value),
            str(value).strip(),
            str(value).strip().upper(),
            str(value).strip().title(),
        ]

        if feature == "posture_event" and str(value).strip().upper() == "FALL":
            text_candidates.insert(0, "FALL_DETECTED")

        for candidate in text_candidates:
            if candidate in encoder.classes_:
                return int(encoder.transform([candidate])[0])

        return 0

    def _feature_value(self, feature: str, document: Dict[str, Any]) -> float:
        if feature == "timestamp":
            return self._timestamp(document.get(feature))
        if feature == "device_type":
            return self._encode_categorical(feature, document.get(feature))
        if feature == "ward":
            return self._encode_categorical(feature, document.get(feature))
        if feature == "life_support":
            return 1 if str(document.get(feature, "")).lower() in {"true", "1", "yes"} else 0
        if feature == "criticality_tier":
            return self._integer(document.get(feature))
        if feature == "protocol":
            return self._encode_categorical(feature, document.get(feature))
        if feature == "dst_port":
            return self._integer(document.get(feature, 1883))
        if feature == "ecg_raw_value":
            return self._numeric(document.get("ecg_raw_value", document.get("ppg_raw_value", 0)))
        if feature == "heart_rate_bpm":
            return self._numeric(document.get("heart_rate_bpm", document.get("heart_rate_bpm_pulse", 0)))
        if feature == "r_peak_detected":
            return self._encode_categorical(feature, document.get(feature))
        if feature == "rhythm_label":
            return self._encode_categorical(feature, document.get(feature))
        if feature == "accel_x":
            return self._numeric(document.get("accel_x"))
        if feature == "accel_y":
            return self._numeric(document.get("accel_y"))
        if feature == "accel_z":
            return self._numeric(document.get("accel_z"))
        if feature == "gyro_x":
            return self._numeric(document.get("gyro_x"))
        if feature == "gyro_y":
            return self._numeric(document.get("gyro_y"))
        if feature == "gyro_z":
            return self._numeric(document.get("gyro_z"))
        if feature == "fall_detected":
            return self._encode_categorical(feature, document.get(feature))
        if feature == "posture_event":
            return self._encode_categorical(feature, document.get(feature))
        if feature == "temperature_celsius":
            return self._numeric(document.get("temperature_celsius", document.get("body_temp_celsius", 0)))
        return self._numeric(document.get(feature))

    def _frame(self, features: Iterable[str], document: Dict[str, Any]) -> pd.DataFrame:
        row = {feature: self._feature_value(feature, document) for feature in features}
        return pd.DataFrame([row], columns=list(features))

    def predict(self, document: Dict[str, Any]) -> AttackPrediction:
        rf_frame = self._frame(self.rf_features, document)
        iso_frame = self._frame(self.iso_features, document)

        rf_raw = self.rf_model.predict(rf_frame)[0]
        rf_label = int(rf_raw)
        rf_confidence = 0.0
        attack_probability = 0.0
        probability_map: Dict[int, float] = {}

        if hasattr(self.rf_model, "predict_proba"):
            probabilities = self.rf_model.predict_proba(rf_frame)[0]
            classes = [int(item) for item in self.rf_model.classes_]
            probability_map = {cls: float(prob) for cls, prob in zip(classes, probabilities)}
            rf_confidence = float(max(probabilities))
            attack_probability = probability_map.get(1, 0.0)
        else:
            attack_probability = 1.0 if rf_label == 1 else 0.0

        iso_raw = int(self.iso_model.predict(iso_frame)[0])
        anomaly_score = 1.0 if iso_raw == -1 else 0.0
        risk_score = round(min(1.0, (attack_probability * 0.7) + (anomaly_score * 0.3)), 4)
        predicted_attack = rf_label == 1 or risk_score >= 0.65
        readable_label = LABEL_MAP.get(rf_label, str(rf_label))
        anomaly_flag = "ANOMALY" if iso_raw == -1 else "NORMAL"

        return AttackPrediction(
            device_id=str(document.get("device_id", "")),
            predicted_label=readable_label,
            predicted_attack=predicted_attack,
            confidence=round(rf_confidence, 4),
            anomaly_flag=anomaly_flag,
            anomaly_score=anomaly_score,
            risk_score=risk_score,
            reason="Predicted with the latest AI Threat Intel Random Forest, encoder pack, and Isolation Forest models.",
            metadata={
                "rf_raw_class": rf_label,
                "rf_attack_probability": round(attack_probability, 4),
                "rf_class_probabilities": probability_map,
                "isolation_forest_raw": iso_raw,
                "rf_features": self.rf_features,
                "iso_features": self.iso_features,
                "encoders": sorted(self.encoders.keys()),
            },
        )
