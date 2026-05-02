from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd


LABEL_MAP = {
    0: "BENIGN",
    1: "ATTACK",
    2: "UNKNOWN_OR_NO_SIGNAL",
}


class AIThreatIntelEngine:
    """
    Local inference helper for the latest AI Threat Intel bundle.

    The new model set includes saved categorical encoders, so this script uses
    those artifacts directly when preparing input rows for prediction.
    """

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent
        self.rf_model = joblib.load(self.base_dir / "random_forest_model.pkl")
        self.iso_model = joblib.load(self.base_dir / "isolation_forest_model.pkl")
        self.rf_features = list(joblib.load(self.base_dir / "rf_features.pkl"))
        self.iso_features = list(joblib.load(self.base_dir / "iso_features.pkl"))
        self.encoders = joblib.load(self.base_dir / "encoders.pkl")

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
        return int(round(self._numeric(value, float(default))))

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
            candidate = "True" if value else "False"
            if candidate in encoder.classes_:
                return int(encoder.transform([candidate])[0])

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

    def _frame(self, features, document: Dict[str, Any]) -> pd.DataFrame:
        row = {feature: self._feature_value(feature, document) for feature in features}
        return pd.DataFrame([row], columns=list(features))

    def predict(self, document: Dict[str, Any]) -> Dict[str, Any]:
        rf_frame = self._frame(self.rf_features, document)
        iso_frame = self._frame(self.iso_features, document)

        rf_prediction = int(self.rf_model.predict(rf_frame)[0])
        rf_confidence = 0.0
        probability_map: Dict[int, float] = {}
        attack_probability = 0.0

        if hasattr(self.rf_model, "predict_proba"):
            probabilities = self.rf_model.predict_proba(rf_frame)[0]
            classes = [int(item) for item in self.rf_model.classes_]
            probability_map = {cls: float(prob) for cls, prob in zip(classes, probabilities)}
            rf_confidence = float(max(probabilities))
            attack_probability = probability_map.get(1, 0.0)
        else:
            attack_probability = 1.0 if rf_prediction == 1 else 0.0

        iso_prediction = int(self.iso_model.predict(iso_frame)[0])
        anomaly_score = 1.0 if iso_prediction == -1 else 0.0
        risk_score = round(min(1.0, (attack_probability * 0.7) + (anomaly_score * 0.3)), 4)

        return {
            "device_id": str(document.get("device_id", "")),
            "predicted_label": LABEL_MAP.get(rf_prediction, str(rf_prediction)),
            "predicted_attack": rf_prediction == 1 or risk_score >= 0.65,
            "confidence": round(rf_confidence, 4),
            "anomaly_flag": "ANOMALY" if iso_prediction == -1 else "NORMAL",
            "anomaly_score": anomaly_score,
            "risk_score": risk_score,
            "rf_raw_class": rf_prediction,
            "rf_class_probabilities": probability_map,
            "isolation_forest_raw": iso_prediction,
            "reason": "Predicted with the latest AI Threat Intel Random Forest, encoder pack, and Isolation Forest models.",
        }

    def predict_dataframe(self, input_file: Path, output_file: Path | None = None) -> pd.DataFrame:
        frame = pd.read_csv(input_file)
        results = [self.predict(row) for row in frame.fillna(np.nan).to_dict(orient="records")]
        result_frame = pd.DataFrame(results)
        if output_file is not None:
            result_frame.to_csv(output_file, index=False)
        return result_frame


def main() -> None:
    engine = AIThreatIntelEngine()
    input_file = engine.base_dir / "detection_results.csv"
    output_file = engine.base_dir / "detection_results_predicted.csv"
    results = engine.predict_dataframe(input_file, output_file)
    print(f"Loaded {len(results)} rows from {input_file.name}")
    print(f"Saved predictions to {output_file.name}")


if __name__ == "__main__":
    main()
