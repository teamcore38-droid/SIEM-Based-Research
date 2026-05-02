from __future__ import annotations

from dataclasses import dataclass

from src.common.models import ARSResponsePrediction, AlertDecision, CorrelationDecision


@dataclass(frozen=True)
class ResponseDecision:
    action: str
    should_quarantine: bool
    should_shutdown: bool
    should_rollback: bool
    reason: str


def decide_response(alert: AlertDecision, correlation: CorrelationDecision) -> ResponseDecision:
    return decide_response_with_model(alert, correlation, None)


def decide_response_with_model(
    alert: AlertDecision,
    correlation: CorrelationDecision,
    ars_prediction: ARSResponsePrediction | None,
) -> ResponseDecision:
    if ars_prediction is not None:
        model_action = ars_prediction.mapped_action

        if not correlation.confirmed_real_attack:
            if correlation.final_action in {"temporary_isolate", "quarantine", "shutdown"}:
                return ResponseDecision(
                    action="rollback",
                    should_quarantine=False,
                    should_shutdown=False,
                    should_rollback=True,
                    reason=f"Correlation rejected the attack; rollback overrides AR model output {ars_prediction.action_label}.",
                )
            return ResponseDecision(
                action="monitor",
                should_quarantine=False,
                should_shutdown=False,
                should_rollback=False,
                reason=f"Correlation found no confirmed attack; AR model output was {ars_prediction.action_label}.",
            )

        if correlation.confirmed_critical and model_action in {"monitor", "rollback"}:
            return ResponseDecision(
                action="quarantine",
                should_quarantine=True,
                should_shutdown=False,
                should_rollback=False,
                reason=f"Safety override: confirmed critical attack cannot use AR model action {ars_prediction.action_label}; quarantining device.",
            )

        if model_action == "quarantine":
            return ResponseDecision(
                action="quarantine",
                should_quarantine=True,
                should_shutdown=False,
                should_rollback=False,
                reason=ars_prediction.reason,
            )
        if model_action == "rollback":
            return ResponseDecision(
                action="rollback",
                should_quarantine=False,
                should_shutdown=False,
                should_rollback=True,
                reason=ars_prediction.reason,
            )
        return ResponseDecision(
            action="monitor",
            should_quarantine=False,
            should_shutdown=False,
            should_rollback=False,
            reason=ars_prediction.reason,
        )

    if correlation.final_action == "shutdown":
        return ResponseDecision(
            action="shutdown",
            should_quarantine=True,
            should_shutdown=True,
            should_rollback=False,
            reason=correlation.reason,
        )
    if correlation.final_action == "quarantine":
        return ResponseDecision(
            action="quarantine",
            should_quarantine=True,
            should_shutdown=False,
            should_rollback=False,
            reason=correlation.reason,
        )
    if correlation.final_action == "temporary_isolate":
        return ResponseDecision(
            action="temporary_isolate",
            should_quarantine=False,
            should_shutdown=False,
            should_rollback=False,
            reason=correlation.reason,
        )
    if alert.priority.upper() in {"MEDIUM", "LOW"}:
        return ResponseDecision(
            action="monitor",
            should_quarantine=False,
            should_shutdown=False,
            should_rollback=False,
            reason="Monitor only; no immediate control action required.",
        )
    return ResponseDecision(
        action="rollback",
        should_quarantine=False,
        should_shutdown=False,
        should_rollback=True,
        reason="Validate and restore to normal state.",
    )
