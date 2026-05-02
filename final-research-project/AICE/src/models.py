from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class Alert:
    """
    Represents a single ML-generated alert.
    """
    device_id: str
    timestamp: datetime
    prediction: str  # e.g., "Anomaly", "DDoS", "Ransomware"
    confidence_score: float
    device_type: str = "unknown"
    raw_data: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "device_id": self.device_id,
            "timestamp": self.timestamp.isoformat(),
            "prediction": self.prediction,
            "confidence_score": self.confidence_score,
            "device_type": self.device_type
        }

@dataclass
class Incident:
    """
    Represents a correlated security incident.
    """
    incident_id: str
    affected_device: str
    device_type: str
    severity: str
    confidence_summary: float
    number_of_correlated_alerts: int
    time_window: str
    compliance_tags: List[str]
    recommended_action: str
    timestamp: datetime
    start_time: datetime
    end_time: datetime
    alerts: List[Alert] = field(default_factory=list) # Keep track of constituent alerts
    representative_metrics: dict = field(default_factory=dict) # Aggregated metrics for output

    def to_dict(self):
        res = {
            "incident_id": self.incident_id,
            "affected_device": self.affected_device,
            "device_type": self.device_type,
            "severity": self.severity,
            "confidence_summary": self.confidence_summary,
            "number_of_correlated_alerts": self.number_of_correlated_alerts,
            "time_window": self.time_window,
            "compliance_tags": self.compliance_tags,
            "recommended_action": self.recommended_action,
            "timestamp": self.timestamp.isoformat(),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat()
        }
        # Flatten metrics into the top-level dict for CSV compatibility
        res.update(self.representative_metrics)
        return res
