from __future__ import annotations

from typing import Any, Dict, Optional

from src.common.models import AlertDecision, AttackPrediction, CorrelationDecision, LiveCorrelationContext


class CorrelationValidator:
    """
    Rule-based second-stage validator for the planned correlation layer.

    This is intentionally conservative:
    - Critical results are confirmed only when the device context supports them.
    - Suspicious-but-low-priority results can be escalated if the device is life-supporting.
    """

    def validate(
        self,
        alert: AlertDecision,
        document: Dict[str, Any],
        attack_prediction: Optional[AttackPrediction] = None,
        live_context: Optional[LiveCorrelationContext] = None,
    ) -> CorrelationDecision:
        life_support = str(document.get("life_support", "")).lower() in {"true", "1"}
        tier = int(document.get("criticality_tier", 0) or 0)
        attack_type = str(document.get("attack_type", "normal"))
        predicted = alert.priority.upper()
        is_attack = str(document.get("is_attack", "")).lower() in {"true", "1"}
        model_confirms_attack = bool(attack_prediction and attack_prediction.predicted_attack)
        model_risk = float(attack_prediction.risk_score) if attack_prediction else 0.0
        live_score = float(live_context.correlation_score) if live_context else 0.0
        live_confirms_attack = bool(live_context and live_context.recommended_verdict == "confirmed_attack")
        live_suspicious = bool(live_context and live_context.recommended_verdict in {"confirmed_attack", "suspicious"})
        related_count = live_context.related_alert_count if live_context else 1

        critical_context = life_support or tier >= 7
        attack_is_high_risk = attack_type in {"ddos", "data_tampering", "device_identity_spoofing", "sensor_spoofing"}
        confirmed_attack = is_attack or model_confirms_attack or live_confirms_attack

        metadata = {
            "validated_priority": predicted,
            "attack_model_risk": model_risk,
            "live_correlation_score": live_score,
            "live_correlation_verdict": live_context.recommended_verdict if live_context else "single_event",
        }

        if predicted == "CRITICAL" and critical_context and confirmed_attack and (live_confirms_attack or is_attack):
            return CorrelationDecision(
                device_id=alert.device_id,
                confirmed_critical=True,
                confirmed_real_attack=True,
                final_action="shutdown",
                reason="Priority, attack prediction, medical-device context, and live AICE correlation confirm a critical event.",
                related_alert_count=related_count,
                metadata=metadata,
            )

        if predicted in {"CRITICAL", "HIGH"} and (critical_context or attack_is_high_risk or model_confirms_attack or live_suspicious):
            return CorrelationDecision(
                device_id=alert.device_id,
                confirmed_critical=predicted == "CRITICAL" or critical_context,
                confirmed_real_attack=confirmed_attack,
                final_action="temporary_isolate",
                reason="High-risk context and live correlation support temporary isolation while the event is reviewed.",
                related_alert_count=related_count,
                metadata=metadata,
            )

        if predicted in {"MEDIUM", "LOW"} and critical_context and (confirmed_attack or live_suspicious):
            return CorrelationDecision(
                device_id=alert.device_id,
                confirmed_critical=True,
                confirmed_real_attack=confirmed_attack,
                final_action="temporary_isolate",
                reason="A low-looking alert became critical after contextual, attack-model, and live AICE validation.",
                related_alert_count=related_count,
                metadata=metadata,
            )

        return CorrelationDecision(
            device_id=alert.device_id,
            confirmed_critical=False,
            confirmed_real_attack=confirmed_attack,
            final_action="monitor",
            reason="No live AICE, attack-model, or priority signal was strong enough for isolation.",
            related_alert_count=related_count,
            metadata=metadata,
        )
