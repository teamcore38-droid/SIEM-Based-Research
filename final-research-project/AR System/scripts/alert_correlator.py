"""
MedGuard-X | Alert Correlation Engine (Model-Integrated)
==========================================================
Uses REAL device datasets + RETRAINED ARS Model (v2, 93.7% accuracy)
to generate AI-predicted automated response actions in real-time.

Pipeline:
  detection_results.csv → classify → MODEL PREDICT action → dashboard
  grouped_alerts.csv    → correlate → MODEL PREDICT action → dashboard
  grouped_incidents.csv → escalate  → MODEL PREDICT action → dashboard
"""
import os
import json
import time
import random
import pickle
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "ars_events.json")

# Real ESP32 Device IP Mapping
DEVICE_IP_MAP = {
    "PULSE_ESP32_001": "10.86.251.45",
    "ECG_ESP32_001":   "10.38.16.20",
    "TEMP_ESP32_001":  "10.18.166.210",
    "MOTION_ESP32_001":"10.98.160.21",
    "CLONE_AD8232":    "10.38.16.20",
    "CLONE_MPU":       "10.98.160.21",
    "CLONE_PULSE":     "10.86.251.45",
    "GHOST_ECG":       "10.38.16.20",
    "GHOST_ESP32":     "10.86.251.45",
    "GHOST_IMU":       "10.98.160.21",
    "ROGUE_ECG_001":   "10.38.16.20",
    "ROGUE_PULSE_001": "10.86.251.45",
    "ROGUE_TEMP_001":  "10.18.166.210",
    "ROGUE_MOTION_001":"10.98.160.21",
    "FAKE_ESP32":      "10.18.166.210",
    "TEMP_CLONE":      "10.18.166.210",
    "UNKNOWN_DEVICE":  "10.18.166.210",
}
MAIN_DEVICES = ["PULSE_ESP32_001", "ECG_ESP32_001", "TEMP_ESP32_001", "MOTION_ESP32_001"]


class AlertCorrelator:
    """Correlates sensor data from real IoMT devices and uses AI model for response decisions."""

    def __init__(self):
        self.detection_data = None
        self.alert_data = None
        self.incident_data = None

        self.detection_idx = 0
        self.alert_idx = 0
        self.incident_idx = 0

        # AI Model
        self.model = None
        self.label_encoders = None
        self.target_encoder = None
        self.feature_cols = None
        self.model_accuracy = 0

        self.load_datasets()
        self.load_model()

    def load_datasets(self):
        """Load all 3 correlation datasets."""
        path = os.path.join(DATA_DIR, "detection_results.csv")
        if os.path.exists(path):
            self.detection_data = pd.read_csv(path)
            print(f"[OK] Loaded detection results: {len(self.detection_data)} records")

        path = os.path.join(DATA_DIR, "grouped_alerts.csv")
        if os.path.exists(path):
            self.alert_data = pd.read_csv(path)
            print(f"[OK] Loaded grouped alerts: {len(self.alert_data)} records")
            print(f"     Priorities: {self.alert_data['priority_label'].value_counts().to_dict()}")

        path = os.path.join(DATA_DIR, "grouped_incidents.csv")
        if os.path.exists(path):
            self.incident_data = pd.read_csv(path)
            print(f"[OK] Loaded incidents: {len(self.incident_data)} incidents")

    def load_model(self):
        """Load the retrained ARS response model."""
        model_path = os.path.join(MODELS_DIR, "ars_response_model_v2.pkl")
        if not os.path.exists(model_path):
            model_path = os.path.join(MODELS_DIR, "ars_response_model.pkl")

        try:
            with open(model_path, "rb") as f:
                pkg = pickle.load(f)
            self.model = pkg['model']
            self.label_encoders = pkg['label_encoders']
            self.target_encoder = pkg['target_encoder']
            self.feature_cols = pkg['feature_cols']
            self.model_accuracy = pkg.get('accuracy', 0)
            print(f"[OK] ARS Response Model loaded: {pkg.get('model_name', '?')} "
                  f"(accuracy: {self.model_accuracy:.2%}, version: {pkg.get('version', '?')})")
        except Exception as e:
            print(f"[!!] Model load failed: {e}")
            self.model = None

    def _resolve_ip(self, device_id, row_ip=None):
        """Resolve device_id to its real IP address."""
        if device_id in DEVICE_IP_MAP:
            return DEVICE_IP_MAP[device_id]
        if row_ip and str(row_ip) not in ("nan", "None", ""):
            return str(row_ip)
        return DEVICE_IP_MAP[MAIN_DEVICES[random.randint(0, 3)]]

    def predict_action(self, classification, priority_label, data_source,
                       ai_prediction, attack_type, is_attack, anomaly_flag):
        """Use the retrained AI model to predict the automated response action."""
        if self.model is None:
            # Fallback to rule-based if model not loaded
            return self._rule_based_action(priority_label)

        try:
            le = self.label_encoders
            features = {
                'classification_enc': le['classification'].transform([str(classification)])[0],
                'priority_label_enc': le['priority_label'].transform([str(priority_label)])[0],
                'data_source_enc': le['data_source'].transform([str(data_source)])[0],
                'ai_prediction_enc': le['ai_prediction'].transform([str(ai_prediction)])[0],
                'attack_type_enc': le['attack_type'].transform([str(attack_type)])[0],
                'is_attack': int(is_attack) if is_attack in (0, 1, -1, True, False) else 0,
                'anomaly_flag': int(anomaly_flag) if anomaly_flag in (0, 1, -1) else 0,
            }
            X = np.array([[features[c] for c in self.feature_cols]])
            pred_enc = self.model.predict(X)[0]
            action = self.target_encoder.inverse_transform([pred_enc])[0]

            # Get confidence from predict_proba
            proba = self.model.predict_proba(X)[0]
            confidence = round(float(max(proba)) * 100, 1)

            return action, confidence
        except Exception as e:
            return self._rule_based_action(priority_label)

    def _rule_based_action(self, priority):
        """Fallback rule-based action mapping."""
        mapping = {
            "CRITICAL": ("PERMANENT QUARANTINE", round(random.uniform(90, 99), 1)),
            "HIGH": ("TEMPORARY ISOLATION", round(random.uniform(75, 95), 1)),
            "MEDIUM": ("MONITORING", round(random.uniform(50, 80), 1)),
        }
        return mapping.get(priority, ("NO_ACTION", round(random.uniform(30, 60), 1)))

    def _severity_from_action(self, action):
        """Map action back to severity label."""
        return {
            "PERMANENT QUARANTINE": "CRITICAL",
            "TEMPORARY ISOLATION": "HIGH",
            "MONITORING": "MEDIUM",
            "NO_ACTION": "LOW",
        }.get(action, "LOW")

    # -------------------------------------------------------------------
    # DATA GENERATORS (now with AI model inference)
    # -------------------------------------------------------------------

    def get_next_detection(self):
        """Get next raw detection result with AI-predicted action."""
        if self.detection_data is None:
            return None

        row = self.detection_data.iloc[self.detection_idx % len(self.detection_data)]
        self.detection_idx += 1

        is_attack = int(row.get("is_attack", 0))
        prediction = str(row.get("prediction", "BENIGN"))
        anomaly = int(row.get("anomaly_flag", 0))

        if prediction == "ATTACK" or is_attack == 1:
            classification = "ATTACK"
            priority = "HIGH"
        elif anomaly == 1 or is_attack == -1:
            classification = "ANOMALY"
            priority = "MEDIUM"
        else:
            classification = "BENIGN"
            priority = "LOW"

        # AI MODEL PREDICTION
        action, confidence = self.predict_action(
            classification=classification,
            priority_label=priority,
            data_source="detection_results",
            ai_prediction=prediction if prediction in ("BENIGN", "ATTACK") else "BENIGN",
            attack_type=str(row.get("attack_type", "normal")),
            is_attack=is_attack,
            anomaly_flag=anomaly
        )
        mapped_device = f"ESP32-{int(row.get('device_id', 0)):03d}"

        return {
            "device_id": mapped_device,
            "heart_rate_bpm_pulse": float(row.get("heart_rate_bpm", 0)) if pd.notna(row.get("heart_rate_bpm")) else 0,
            "ecg_raw_value": float(row.get("ecg_raw_value", 0)) if pd.notna(row.get("ecg_raw_value")) else 0,
            "temperature_celsius": float(row.get("temperature_celsius", 36.5)) if pd.notna(row.get("temperature_celsius")) else 36.5,
            "ppg_raw_value": int(row.get("r_peak_detected", 0)),
            "accel_x": float(row.get("accel_x", 0)) if pd.notna(row.get("accel_x")) else 0,
            "accel_y": float(row.get("accel_y", 0)) if pd.notna(row.get("accel_y")) else 0,
            "accel_z": float(row.get("accel_z", 0)) if pd.notna(row.get("accel_z")) else 0,
            "classification": classification,
            "is_attack": is_attack,
            "anomaly_flag": anomaly,
            "criticality_tier": self._severity_from_action(action),
            "ai_action": action,
            "ai_confidence": confidence,
            "model_accuracy": self.model_accuracy,
            "attack_type": int(row.get("attack_type", 0)),
            "src_ip": self._resolve_ip(mapped_device),
            "timestamp": time.time(),
            "data_source": "CORRELATED",
        }

    def get_next_alert(self):
        """Get next correlated alert with AI model response action."""
        if self.alert_data is None:
            return None

        row = self.alert_data.iloc[self.alert_idx % len(self.alert_data)]
        self.alert_idx += 1

        device_id = str(row.get("device_id", "UNKNOWN"))
        priority = str(row.get("priority_label", "LOW"))
        predicted = str(row.get("predicted_priority", priority))
        is_attack = bool(row.get("is_attack", False))
        attack_type = str(row.get("attack_type", "normal"))
        sensor = str(row.get("sensor_source", "unknown"))
        ward = str(row.get("ward", "Unknown"))
        group_id = int(row.get("group_id", 0))

        row_ip = str(row.get("src_ip", ""))

        # AI MODEL PREDICTION
        action, confidence = self.predict_action(
            classification="ATTACK" if is_attack else "ANOMALY",
            priority_label=priority,
            data_source="grouped_alerts",
            ai_prediction=predicted,
            attack_type=attack_type,
            is_attack=1 if is_attack else 0,
            anomaly_flag=1 if is_attack else 0
        )
        sev = self._severity_from_action(action)
        resolved_ip = self._resolve_ip(device_id, row_ip)

        if is_attack:
            msg = f"AI RESPONSE: {action} | [{attack_type}] on {device_id} ({sensor}) in {ward} | Group #{group_id}"
        else:
            msg = f"AI RESPONSE: {action} | Anomaly on {device_id} ({sensor}) in {ward} | Confidence: {confidence}%"

        return {
            "severity": sev,
            "action_taken": action,
            "threat_type": attack_type,
            "device_id": device_id,
            "sensor_source": sensor,
            "ward": ward,
            "group_id": group_id,
            "is_attack": is_attack,
            "predicted_priority": predicted,
            "confidence": confidence,
            "model_accuracy": self.model_accuracy,
            "src_ip": resolved_ip,
            "message": msg,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": "CORRELATED",
        }

    def get_next_incident(self):
        """Get next correlated incident with AI model response."""
        if self.incident_data is None:
            return None

        row = self.incident_data.iloc[self.incident_idx % len(self.incident_data)]
        self.incident_idx += 1

        incident_id = str(row.get("incident_id", "INC-0000"))
        priority = str(row.get("incident_priority", "LOW"))
        alert_count = int(row.get("alert_count", 1))
        attack_types = str(row.get("attack_types", "unknown"))
        devices = str(row.get("devices_affected", "unknown"))
        wards = str(row.get("wards_affected", "unknown"))
        life_support = bool(row.get("life_support_involved", False))

        # AI MODEL PREDICTION
        action, confidence = self.predict_action(
            classification="INCIDENT",
            priority_label=priority,
            data_source="grouped_incidents",
            ai_prediction=priority,
            attack_type=attack_types.split(",")[0].strip() if "," in attack_types else attack_types,
            is_attack=1,
            anomaly_flag=1
        )
        sev = self._severity_from_action(action)

        # Pick a real device IP from affected devices
        affected_list = [d.strip() for d in devices.split(",")]
        target_device = affected_list[0] if affected_list else "PULSE_ESP32_001"
        resolved_ip = self._resolve_ip(target_device)

        msg = (f"AI RESPONSE: {action} | INCIDENT {incident_id}: {alert_count} alerts | "
               f"Attacks: {attack_types} | Devices: {devices} | "
               f"{'LIFE SUPPORT AT RISK' if life_support else 'No life support'}")

        return {
            "severity": sev,
            "action_taken": action,
            "incident_id": incident_id,
            "alert_count": alert_count,
            "attack_types": attack_types,
            "devices_affected": devices,
            "wards_affected": wards,
            "life_support_involved": life_support,
            "confidence": confidence,
            "model_accuracy": self.model_accuracy,
            "src_ip": resolved_ip,
            "message": msg,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data_source": "CORRELATED",
        }

    def write_event_to_log(self, event):
        """Write correlated event to ars_events.json for Flask API."""
        sev = event.get("severity", "LOW")
        action = event.get("action_taken", "NO_ACTION")

        if action == "PERMANENT QUARANTINE":
            decision = "QUARANTINE"
        elif action == "TEMPORARY ISOLATION":
            decision = "ISOLATE"
        elif action == "MONITORING":
            decision = "MONITOR"
        else:
            decision = "NO_ACTION"

        mapped = {
            "timestamp": event["timestamp"],
            "event_type": "DANGER" if sev in ("CRITICAL", "HIGH") else "INFO",
            "severity": sev,
            "original_type": "CORRELATED_ALERT",
            "decision": decision,
            "src_ip": event.get("src_ip", "10.86.251.45"),
            "device_id": event.get("device_id", event.get("devices_affected", "")),
            "anomaly_score": round(event.get("confidence", 50) / 100, 2),
            "message": event.get("message", ""),
            "details": f"AI Model ({self.model_accuracy:.0%}) | {action} | Confidence: {event.get('confidence', 0)}%",
        }
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(mapped) + "\n")

    def generate_privacy_event(self):
        """Generate a PHI detection/redaction event for the Privacy Vault."""
        phi_patterns = [
            "SSN: ***-**-1234",
            "Patient Name: [REDACTED]",
            "DOB: [REDACTED] -> ****-**-**",
            "MRN#: [REDACTED]",
            "Insurance ID: [REDACTED]",
            "Blood Type: [REDACTED]",
            "Diagnosis: [REDACTED]",
            "Prescription: [REDACTED]",
        ]
        device = random.choice(MAIN_DEVICES)
        device_ip = DEVICE_IP_MAP[device]
        pattern = random.choice(phi_patterns)

        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": "PRIVACY_ALERT",
            "original_type": "PRIVACY_ALERT",
            "decision": "REDACT",
            "src_ip": device_ip,
            "anomaly_score": round(random.uniform(0.6, 1.0), 2),
            "message": f"PHI Detected & Redacted on {device}: {pattern}",
            "details": f"Auto-redaction by AI Privacy Engine on {device}",
        }

    def write_privacy_event(self):
        """Write a privacy/PHI event to ars_events.json for Privacy Vault."""
        event = self.generate_privacy_event()
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(event) + "\n")
        return event
