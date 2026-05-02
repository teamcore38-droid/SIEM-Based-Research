import json
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Optional

class Alert:
    """
    Represents a normalized alert from the ML Engine.
    """
    def __init__(self, device_id: str, timestamp: str, prediction: str, 
                 confidence_score: float, device_type: str, src_ip: str = None):
        self.device_id = device_id
        self.timestamp = datetime.fromisoformat(timestamp)
        self.prediction = prediction
        self.confidence_score = float(confidence_score)
        self.device_type = device_type
        self.src_ip = src_ip
        self.id = str(uuid.uuid4())

    def to_dict(self):
        return {
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat(),
            "prediction": self.prediction,
            "confidence_score": self.confidence_score,
            "device_type": self.device_type
        }

class Incident:
    """
    Represents a correlated security incident.
    """
    def __init__(self, device_id: str, device_type: str, start_time: datetime):
        self.incident_id = f"INC-{datetime.now().year}-{str(uuid.uuid4())[:8].upper()}"
        self.device_id = device_id
        self.device_type = device_type
        self.start_time = start_time
        self.end_time = start_time
        self.alerts: List[Alert] = []
        self.severity = "Low"
        self.confidence_summary = 0.0
        self.compliance_tags = []
        self.recommended_action = ""
        self.status = "Open"

    def add_alert(self, alert: Alert):
        self.alerts.append(alert)
        if alert.timestamp > self.end_time:
            self.end_time = alert.timestamp
        # Update confidence summary (Simple average for now, could be max or weighted)
        total_conf = sum(a.confidence_score for a in self.alerts)
        self.confidence_summary = round(total_conf / len(self.alerts), 4)

    def duration_seconds(self):
        return (self.end_time - self.start_time).total_seconds()

    def to_dict(self):
        return {
            "incident_id": self.incident_id,
            "affected_device": self.device_id,
            "device_type": self.device_type,
            "severity": self.severity,
            "confidence_summary": self.confidence_summary,
            "number_of_correlated_alerts": len(self.alerts),
            "time_window": f"{self.duration_seconds()} seconds",
            "compliance_tags": self.compliance_tags,
            "recommended_action": self.recommended_action,
            "timestamp": self.end_time.isoformat(),
            "alerts": [a.to_dict() for a in self.alerts] # Optional: include alerts for debug
        }

class SeverityScorer:
    """
    Assigns severity levels based on device criticality and confidence.
    """
    CRITICAL_DEVICES = ["ventilator", "infusion_pump", "cardiac_monitor", "icu_monitor", "esp32_pulse_oximeter", "esp32_ecg_monitor"]
    HIGH_RISK_ATTACKS = ["ransomware", "ddos", "mitm", "injection", "buffer_overflow", "firmware_exploit"]

    @staticmethod
    def calculate(incident: Incident) -> str:
        score = 0.0
        
        # 1. Base Score from Confidence
        score += incident.confidence_summary * 5  # Max 5

        # 2. Device Criticality Weight
        normalized_type = incident.device_type.lower().replace(" ", "_")
        is_critical = any(cd in normalized_type for cd in SeverityScorer.CRITICAL_DEVICES)
        if is_critical:
            score *= 1.5
        elif "admin" in normalized_type or "server" in normalized_type:
             score *= 1.2

        # 3. Frequency Weight
        if len(incident.alerts) > 5:
            score += 2
        elif len(incident.alerts) > 2:
            score += 1

        # 4. Attack Type Weight (Check if any alert is high risk)
        has_high_risk = any(any(at in a.prediction.lower() for at in SeverityScorer.HIGH_RISK_ATTACKS) 
                            for a in incident.alerts)
        if has_high_risk:
            score += 2

        # Mapping to Levels
        if score >= 8:
            return "Critical"
        elif score >= 6:
            return "High"
        elif score >= 3:
            return "Medium"
        else:
            return "Low"

class ComplianceTagger:
    """
    Applies compliance tags based on context.
    """
    @staticmethod
    def tag(incident: Incident) -> List[str]:
        tags = []
        # HIPAA: Medical devices imply patient data
        # SL-DPA: Personal data protection
        
        normalized_type = incident.device_type.lower()
        medical_devices = ["ventilator", "monitor", "pump", "pacemaker", "ecg", "pulse", "temperature"]
        
        is_medical = any(md in normalized_type for md in medical_devices)
        
        if is_medical:
            tags.append("HIPAA")
            tags.append("SL-DPA") # Assuming all medical data is personal data in this context
            
        return tags

class AICEngine:
    """
    The main Adaptive Incident Correlation Engine.
    """
    def __init__(self, time_window_seconds: int = 300):
        self.time_window = timedelta(seconds=time_window_seconds)
        self.active_incidents: Dict[str, Incident] = {} # Key: device_id
        self.closed_incidents: List[Incident] = []

    def ingest_alert(self, alert: Alert):
        """
        Main entry point for processing an alert.
        """
        # 1. False Positive Reduction (Simple Threshold)
        if alert.confidence_score < 0.4:
            return # Ignore low confidence

        # 2. Correlation
        self._correlate_and_group(alert)

    def _correlate_and_group(self, alert: Alert):
        device_id = alert.device_id
        
        # Check if we have an active incident for this device
        if device_id in self.active_incidents:
            incident = self.active_incidents[device_id]
            
            # Check temporal proximity
            if alert.timestamp - incident.end_time <= self.time_window:
                incident.add_alert(alert)
                self._update_incident_properties(incident)
                return
            else:
                # Time window exceeded, close old incident and start new
                self.closed_incidents.append(incident)
                del self.active_incidents[device_id]
        
        # Create new incident
        new_incident = Incident(device_id, alert.device_type, alert.timestamp)
        new_incident.add_alert(alert)
        self._update_incident_properties(new_incident)
        self.active_incidents[device_id] = new_incident

    def _update_incident_properties(self, incident: Incident):
        # 3 & 4. Scoring and Tagging
        incident.severity = SeverityScorer.calculate(incident)
        incident.compliance_tags = ComplianceTagger.tag(incident)
        
        # 5. Recommendation
        if incident.severity == "Critical":
             incident.recommended_action = "IMMEDIATE: Isolate device, Notify SOC, Check Patient Safety."
        elif incident.severity == "High":
             incident.recommended_action = "URGENT: Investigate traffic source, Verify device integrity."
        elif incident.severity == "Medium":
             incident.recommended_action = "Monitor device for further anomalies."
        else:
             incident.recommended_action = "Log for audit review."

    def close_all_incidents(self):
        """
        Force close all active incidents (e.g., at end of batch processing).
        """
        for inc in self.active_incidents.values():
            self.closed_incidents.append(inc)
        self.active_incidents.clear()

    def get_all_incidents(self) -> List[dict]:
        return [i.to_dict() for i in self.closed_incidents + list(self.active_incidents.values())]
