from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SensorEvent:
    timestamp: Any
    device_id: str
    device_type: str
    ward: str
    life_support: bool
    criticality_tier: int
    protocol: str
    src_ip: str
    dst_port: int
    attack_type: str = "normal"
    is_attack: bool = False
    source: str = "simulated"
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_document(self) -> Dict[str, Any]:
        document = asdict(self)
        document.update(self.payload)
        return document


@dataclass
class AlertDecision:
    device_id: str
    priority: str
    confidence: float
    reason: str
    should_escalate: bool
    should_quarantine: bool
    should_shutdown: bool
    source_timestamp: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttackPrediction:
    device_id: str
    predicted_label: str
    predicted_attack: bool
    confidence: float
    anomaly_flag: str
    anomaly_score: float
    risk_score: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CorrelationDecision:
    device_id: str
    confirmed_critical: bool
    confirmed_real_attack: bool
    final_action: str
    reason: str
    related_alert_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LiveCorrelationContext:
    device_id: str
    window_seconds: int
    events_considered: int
    related_alert_count: int
    attack_alert_count: int
    high_risk_attack_count: int
    attack_types: List[str] = field(default_factory=list)
    protocols: List[str] = field(default_factory=list)
    source_ips: List[str] = field(default_factory=list)
    life_support_seen: bool = False
    max_criticality_tier: int = 0
    correlation_score: float = 0.0
    recommended_verdict: str = "monitor"
    reason: str = ""


@dataclass
class ARSResponsePrediction:
    action_label: str
    mapped_action: str
    confidence: float
    reason: str
    features: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PHIRedactionResult:
    phi_detected: bool
    original_text: str
    redacted_text: str
    redaction_count: int
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ControlCommand:
    command_id: str
    device_id: str
    action: str
    status: str = "queued"
    requested_by: str = "system"
    created_at: str = field(default_factory=utc_now_iso)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportSummary:
    generated_at: str
    total_logs: int
    attack_logs: int
    total_responses: int
    active_devices: int
    model_accuracy: str
    alert_reduction: str
    notes: List[str] = field(default_factory=list)
