from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from src.common.models import AlertDecision, AttackPrediction, LiveCorrelationContext


HIGH_RISK_ATTACKS = {"ddos", "data_tampering", "device_identity_spoofing", "sensor_spoofing", "firmware_exploit"}


class LiveAICECorrelationEngine:
    """
    Lightweight live AICE-style correlation over recent telemetry.

    It groups events from the same device inside a time window and summarizes
    repeated attacks, high-risk attack types, source spread, and asset context.
    """

    def __init__(self, window_seconds: int = 300):
        self.window_seconds = window_seconds

    def _parse_timestamp(self, value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            raw = float(value)
            return raw / 1000 if raw > 10_000_000_000 else raw
        if isinstance(value, str):
            try:
                return float(value) / 1000 if float(value) > 10_000_000_000 else float(value)
            except ValueError:
                pass
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
            except ValueError:
                return None
        if hasattr(value, "timestamp"):
            return float(value.timestamp())
        return None

    def _is_attack_event(self, event: Dict[str, Any]) -> bool:
        raw = str(event.get("is_attack", "")).lower()
        if raw in {"true", "1"}:
            return True
        attack_type = str(event.get("attack_type", "normal")).lower()
        return attack_type not in {"", "normal", "none", "0", "-1"}

    def _window_events(self, document: Dict[str, Any], history: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        current_ts = self._parse_timestamp(document.get("timestamp"))
        events = [document, *list(history)]
        same_device = [event for event in events if str(event.get("device_id", "")) == str(document.get("device_id", ""))]
        if current_ts is None:
            return same_device[:50]

        windowed = []
        for event in same_device:
            ts = self._parse_timestamp(event.get("timestamp"))
            if ts is None or abs(current_ts - ts) <= self.window_seconds:
                windowed.append(event)
        return windowed[:200]

    def build(
        self,
        document: Dict[str, Any],
        history: Iterable[Dict[str, Any]],
        alert: AlertDecision,
        attack_prediction: AttackPrediction,
    ) -> LiveCorrelationContext:
        events = self._window_events(document, history)
        attack_events = [event for event in events if self._is_attack_event(event)]

        attack_types = sorted({
            str(event.get("attack_type", "")).lower()
            for event in attack_events
            if str(event.get("attack_type", "")).lower() not in {"", "normal", "none", "0", "-1"}
        })
        protocols = sorted({str(event.get("protocol", "")) for event in events if event.get("protocol")})
        source_ips = sorted({str(event.get("src_ip", "")) for event in events if event.get("src_ip")})
        high_risk_count = sum(1 for event in attack_events if str(event.get("attack_type", "")).lower() in HIGH_RISK_ATTACKS)
        life_support_seen = any(str(event.get("life_support", "")).lower() in {"true", "1"} for event in events)
        tiers = []
        for event in events:
            try:
                tiers.append(int(event.get("criticality_tier", 0) or 0))
            except (TypeError, ValueError):
                pass
        max_tier = max(tiers) if tiers else 0

        score = 0.0
        score += min(len(attack_events), 6) * 0.8
        score += min(high_risk_count, 4) * 1.2
        score += 1.5 if life_support_seen or max_tier >= 8 else 0.0
        score += 1.0 if alert.priority.upper() in {"CRITICAL", "HIGH"} else 0.0
        score += 1.0 if attack_prediction.predicted_attack else 0.0
        score += min(len(source_ips), 4) * 0.25
        score = round(score, 2)

        if score >= 6:
            verdict = "confirmed_attack"
        elif score >= 3:
            verdict = "suspicious"
        else:
            verdict = "monitor"

        return LiveCorrelationContext(
            device_id=str(document.get("device_id", "")),
            window_seconds=self.window_seconds,
            events_considered=len(events),
            related_alert_count=len(events),
            attack_alert_count=len(attack_events),
            high_risk_attack_count=high_risk_count,
            attack_types=attack_types,
            protocols=protocols,
            source_ips=source_ips[:10],
            life_support_seen=life_support_seen,
            max_criticality_tier=max_tier,
            correlation_score=score,
            recommended_verdict=verdict,
            reason=(
                f"AICE live window found {len(attack_events)} attack-like events "
                f"and {high_risk_count} high-risk attacks in {self.window_seconds}s."
            ),
        )
