from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import joblib
import pandas as pd

from src.common.models import ARSResponsePrediction, AttackPrediction


ACTION_MAP = {
    "MONITOR": "monitor",
    "NO_ACTION": "monitor",
    "QUARANTINE": "quarantine",
    "ROLLBACK": "rollback",
}


class ARSResponseModel:
    """
    Adapter for the AR System response model.

    The saved model expects operational/vital features, so this wrapper derives
    those fields from the current telemetry event and attack-prediction context.
    """

    columns = ["heart_rate", "spo2", "sys_bp", "network_latency", "packet_size", "anomaly_score"]

    def __init__(self, model):
        self.model = model

    @classmethod
    def load(cls, models_dir: Path):
        return cls(joblib.load(models_dir / "ars_decision_model_final.pkl"))

    def _number(self, value: Any, default: float) -> float:
        if value is None or value == "":
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def build_features(self, document: Dict[str, Any], attack_prediction: AttackPrediction) -> Dict[str, float]:
        attack_type = str(document.get("attack_type", "normal")).lower()
        protocol = str(document.get("protocol", "MQTT")).upper()
        dst_port = int(self._number(document.get("dst_port"), 1883))
        is_attack = str(document.get("is_attack", "")).lower() in {"true", "1"}

        heart_rate = self._number(document.get("heart_rate_bpm", document.get("heart_rate_bpm_pulse")), 75)
        spo2 = self._number(document.get("spo2_percentage", document.get("spo2")), 98)
        sys_bp = self._number(document.get("sys_bp", document.get("bp_sys")), 120)
        anomaly_score = max(float(attack_prediction.risk_score), float(attack_prediction.anomaly_score))

        network_latency = self._number(document.get("network_latency"), 20)
        packet_size = self._number(document.get("packet_size"), 500)

        if is_attack:
            network_latency += 120
            packet_size += 1200
        if attack_type in {"ddos", "flooding"}:
            network_latency += 900
            packet_size += 60000
        if attack_type in {"data_tampering", "sensor_spoofing"}:
            anomaly_score = max(anomaly_score, 0.75)
        if protocol not in {"MQTT", "BLE_MQTT"} or dst_port != 1883:
            network_latency += 250
            anomaly_score = max(anomaly_score, 0.65)

        return {
            "heart_rate": heart_rate,
            "spo2": spo2,
            "sys_bp": sys_bp,
            "network_latency": network_latency,
            "packet_size": packet_size,
            "anomaly_score": round(anomaly_score, 4),
        }

    def predict(self, document: Dict[str, Any], attack_prediction: AttackPrediction) -> ARSResponsePrediction:
        features = self.build_features(document, attack_prediction)
        frame = pd.DataFrame([features], columns=self.columns)
        action_label = str(self.model.predict(frame)[0])
        confidence = 0.0
        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba(frame)[0]
            classes = [str(item) for item in self.model.classes_]
            if action_label in classes:
                confidence = float(probabilities[classes.index(action_label)])
        mapped_action = ACTION_MAP.get(action_label, "monitor")
        return ARSResponsePrediction(
            action_label=action_label,
            mapped_action=mapped_action,
            confidence=round(confidence, 4),
            reason=f"AR System model predicted {action_label}; mapped to backend action {mapped_action}.",
            features=features,
            metadata={"model": "ars_decision_model_final.pkl", "classes": [str(item) for item in self.model.classes_]},
        )
