from __future__ import annotations

from typing import Any, Dict


ACTION_TO_STATE = {
    "temporary_isolate": "Temporarily Isolated",
    "isolate": "Temporarily Isolated",
    "quarantine": "Quarantined",
    "shutdown": "Quarantined",
    "rollback": "Restored",
    "restore": "Restored",
    "false_positive": "Restored",
    "log_and_monitor": "Normal",
    "monitor": "Normal",
}


BLOCKING_STATES = {"Quarantined"}

MANUAL_SHUTDOWN_ACTIONS = {"quarantine", "shutdown"}


def operator_instruction_for_action(action: str) -> str | None:
    if action in MANUAL_SHUTDOWN_ACTIONS:
        return "This sensor is quarantined. Please turn it off."
    if action == "temporary_isolate":
        return "This sensor is temporarily isolated in the backend. Please limit physical use until reviewed."
    return None


def state_for_action(action: str) -> str:
    return ACTION_TO_STATE.get(action, "Suspicious")


def is_blocked_state(state: str | None) -> bool:
    return str(state or "") in BLOCKING_STATES


def state_payload(action: str, reason: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "state": state_for_action(action),
        "last_action": action,
        "reason": reason,
        "metadata": metadata or {},
    }
