from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.ai.attack_prediction import AttackPredictionBundle
from src.ai.prioritization import PriorityModelBundle
from src.common.models import ReportSummary, utc_now_iso
from src.common.settings import get_settings
from src.control.device_controller import DeviceController
from src.control.hardware_registry import hardware_device_roster
from src.correlation.live_aice import LiveAICECorrelationEngine
from src.correlation.validator import CorrelationValidator
from src.mongo.client import ping_database
from src.mongo.repository import DeviceStateRepository, PredictionRepository, ResponseRepository, SensorLogRepository
from src.response.ars_model import ARSResponseModel
from src.response.device_state import is_blocked_state, operator_instruction_for_action, state_for_action
from src.response.phi_guard import PHIGuard, build_evidence_text
from src.response.policy import decide_response_with_model
from src.simulation.config import simulation_config_store
from src.simulation.generator import DEVICE_PROFILES, generate_sensor_event, generate_sensor_events
from src.simulation.replay import load_csv_documents, replay_documents
from src.simulation.runner import SimulationRunner
from src.api.utils import json_safe, read_csv_records, read_text

settings = get_settings()
BASE_DIR = Path(settings.component_root)
RESEARCH_ROOT = Path(settings.research_root)
ALERT_MODULE_ROOT = Path(settings.alert_module_root)
MODELS_DIR = ALERT_MODULE_ROOT / "models"
RAW_DIR = ALERT_MODULE_ROOT / "data" / "raw"
PROCESSED_DIR = ALERT_MODULE_ROOT / "data" / "processed"
RESULTS_DIR = ALERT_MODULE_ROOT / "results"
THREAT_INTEL_DIR = RESEARCH_ROOT / "AI Threat Intel"
ARS_MODELS_DIR = RESEARCH_ROOT / "AR System" / "models"

app = FastAPI(title="IoMT SIEM Backend", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResponseActionRequest(BaseModel):
    device_id: str
    action: str
    reason: str = "Dashboard action"
    requested_by: str = "admin-demo"


class RedactionRequest(BaseModel):
    text: str


class SimulationConfigRequest(BaseModel):
    data_mode: Optional[str] = None
    simulation_mode: Optional[str] = None
    anomaly_device_id: Optional[str] = None
    anomaly_type: Optional[str] = None


@lru_cache(maxsize=1)
def predictor() -> PriorityModelBundle:
    return PriorityModelBundle.load(MODELS_DIR)


@lru_cache(maxsize=1)
def attack_predictor() -> AttackPredictionBundle:
    return AttackPredictionBundle.load(THREAT_INTEL_DIR)


@lru_cache(maxsize=1)
def ars_response_model() -> ARSResponseModel:
    return ARSResponseModel.load(ARS_MODELS_DIR)


@lru_cache(maxsize=1)
def phi_guard() -> PHIGuard:
    return PHIGuard.load(ARS_MODELS_DIR)


@lru_cache(maxsize=1)
def validator() -> CorrelationValidator:
    return CorrelationValidator()


@lru_cache(maxsize=1)
def live_correlator() -> LiveAICECorrelationEngine:
    return LiveAICECorrelationEngine()


@lru_cache(maxsize=1)
def simulator() -> SimulationRunner:
    return SimulationRunner()


def sim_config_store():
    return simulation_config_store()


def _repos():
    sensor_repo = SensorLogRepository()
    response_repo = ResponseRepository()
    controller = DeviceController(response_collection=response_repo.collection)
    return sensor_repo, response_repo, controller


def _state_repo() -> DeviceStateRepository:
    return DeviceStateRepository()


def _prediction_repo() -> PredictionRepository:
    return PredictionRepository()


def _mongo_available() -> bool:
    try:
        return ping_database()
    except Exception:
        return False


def _fallback_telemetry(limit: int) -> List[Dict[str, Any]]:
    docs = list(load_csv_documents(sorted(RAW_DIR.glob("*_sensor_log.csv"))))
    return [json_safe(item) for item in docs[-limit:]]


def _record_device_state(
    device_id: str,
    action: str,
    reason: str,
    metadata: Dict[str, Any] | None = None,
    device_type: str = "",
) -> Dict[str, Any] | None:
    if not _mongo_available() or not device_id:
        return None
    return _state_repo().upsert(
        device_id=device_id,
        device_type=device_type,
        state=state_for_action(action),
        action=action,
        reason=reason,
        metadata=metadata,
    )


def _control_metadata(action: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    notice = operator_instruction_for_action(action)
    payload = {
        **(metadata or {}),
        "control_mode": "backend_only",
        "physical_control_enabled": False,
        "manual_shutdown_required": action in {"quarantine", "shutdown"},
    }
    if notice:
        payload["operator_notification"] = notice
    return payload


def _issue_response_action(
    document: Dict[str, Any],
    action: str,
    reason: str,
    controller: DeviceController,
    metadata: Dict[str, Any] | None = None,
) -> tuple[Dict[str, Any], Dict[str, Any] | None]:
    device_id = str(document.get("device_id", "unknown"))
    command = controller.issue(
        device_id,
        action,
        requested_by="system",
        metadata=_control_metadata(action, {
            **(metadata or {}),
            "reason": reason,
        }),
    ).__dict__
    state_update = _record_device_state(
        device_id,
        action,
        reason,
        metadata=_control_metadata(action, {"metadata": metadata or {}, "command": command}),
        device_type=str(document.get("device_type", "")),
    )
    return command, state_update


def _generate_active_sensor_event() -> Dict[str, Any]:
    config = sim_config_store().get()
    if not _mongo_available():
        return generate_sensor_event(config)

    repo = _state_repo()
    for _ in range(20):
        document = generate_sensor_event(config)
        current_state = repo.get(str(document.get("device_id", "")))
        state = str((current_state or {}).get("state", "Normal"))
        if is_blocked_state(state):
            continue
        document["device_state"] = state
        if state == "Temporarily Isolated":
            document["network_isolated"] = True
            document["simulation_note"] = "Device is temporarily isolated; telemetry is marked as restricted."
        return document

    document = generate_sensor_event()
    document.update({
        "device_state": "Quarantined",
        "network_blocked": True,
        "simulation_skipped": True,
        "simulation_note": "No active non-quarantined simulated device was available.",
    })
    return document


def _apply_targeted_anomaly_response(document: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    if (
        document.get("source") == "simulated_live_generator"
        and document.get("simulation_mode") == "anomaly"
        and not document.get("simulated_anomaly_target")
        and not document.get("is_attack")
    ):
        analysis = json_safe(analysis)
        analysis["decision"] = {
            **(analysis.get("decision") or {}),
            "action": "monitor",
            "should_quarantine": False,
            "should_shutdown": False,
            "should_rollback": False,
            "reason": "Controlled anomaly simulation: non-target sensors remain normal and continue monitoring.",
        }
        return analysis

    if not document.get("simulated_anomaly_target") or not document.get("is_attack"):
        return analysis
    action = str((analysis.get("decision") or {}).get("action", "monitor"))
    if action in {"quarantine", "shutdown"}:
        return analysis

    alert = analysis.get("alert") or {}
    attack_prediction = analysis.get("attack_prediction") or {}
    correlation = analysis.get("correlation") or {}
    live_correlation = analysis.get("live_correlation") or {}
    priority = str(alert.get("priority", "LOW")).upper()
    live_verdict = str(live_correlation.get("recommended_verdict", "")).lower()
    predicted_attack = bool(attack_prediction.get("predicted_attack"))
    confirmed_real_attack = bool(correlation.get("confirmed_real_attack"))
    confirmed_critical = bool(correlation.get("confirmed_critical"))
    verified_critical = (
        priority == "CRITICAL"
        and confirmed_real_attack
        and (confirmed_critical or predicted_attack or live_verdict == "confirmed_attack")
    )
    verified_high_risk = (
        priority in {"CRITICAL", "HIGH"}
        and confirmed_real_attack
        and (predicted_attack or live_verdict in {"confirmed_attack", "suspicious"})
    )
    if not (verified_critical or verified_high_risk):
        return analysis

    analysis = json_safe(analysis)
    analysis["decision"] = {
        **(analysis.get("decision") or {}),
        "action": "quarantine",
        "should_quarantine": True,
        "should_shutdown": False,
        "should_rollback": False,
        "reason": "Controlled anomaly simulation: selected sensor anomaly was verified by AI prioritization, threat prediction, and correlation, so only that sensor is quarantined.",
    }
    return analysis


def _apply_staged_validation_outcome(analysis: Dict[str, Any], staged_isolation: bool) -> Dict[str, Any]:
    if not staged_isolation:
        return analysis

    correlation = analysis.get("correlation") or {}
    decision = analysis.get("decision") or {}
    confirmed_real_attack = bool(correlation.get("confirmed_real_attack"))
    confirmed_critical = bool(correlation.get("confirmed_critical"))
    action = str(decision.get("action", "monitor"))

    if confirmed_real_attack and confirmed_critical and action not in {"quarantine", "shutdown"}:
        analysis = json_safe(analysis)
        analysis["decision"] = {
            **(analysis.get("decision") or {}),
            "action": "quarantine",
            "should_quarantine": True,
            "should_shutdown": False,
            "should_rollback": False,
            "reason": "Staged validation: AI Threat Intel isolation was confirmed as a critical real attack, so the device is escalated to quarantine.",
        }
        return analysis

    if not confirmed_real_attack:
        analysis = json_safe(analysis)
        analysis["decision"] = {
            **(analysis.get("decision") or {}),
            "action": "restore",
            "should_quarantine": False,
            "should_shutdown": False,
            "should_rollback": True,
            "reason": "Staged validation: correlation rejected the AI Threat Intel attack prediction, so the device is restored from isolation.",
        }
        return analysis

    if action == "monitor":
        analysis = json_safe(analysis)
        analysis["decision"] = {
            **(analysis.get("decision") or {}),
            "action": "temporary_isolate",
            "should_quarantine": False,
            "should_shutdown": False,
            "should_rollback": False,
            "reason": "Staged validation: attack remains suspicious but not critical, so backend restriction stays in place.",
        }
    return analysis


def _timestamp_seconds(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        raw = float(value)
        return raw / 1000 if raw > 10_000_000_000 else raw
    if isinstance(value, str):
        try:
            raw = float(value)
            return raw / 1000 if raw > 10_000_000_000 else raw
        except ValueError:
            pass
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    if hasattr(value, "generation_time"):
        return value.generation_time.timestamp()
    if hasattr(value, "timestamp"):
        try:
            return float(value.timestamp())
        except (TypeError, ValueError):
            return None
    return None


def _document_timestamp_seconds(document: Dict[str, Any]) -> Optional[float]:
    timestamp = _timestamp_seconds(document.get("timestamp"))
    if timestamp is not None:
        return timestamp
    created_at = _timestamp_seconds(document.get("created_at"))
    if created_at is not None:
        return created_at
    return _timestamp_seconds(document.get("_id"))


def _state_applies_to_document(document: Dict[str, Any], state_document: Dict[str, Any]) -> bool:
    state_timestamp = _timestamp_seconds(state_document.get("updated_at"))
    document_timestamp = _document_timestamp_seconds(document)
    if state_timestamp is None or document_timestamp is None:
        return False
    return document_timestamp >= state_timestamp


def _overlay_device_states(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not documents or not _mongo_available():
        return documents

    states = {
        str(item.get("device_id", "")): item
        for item in _state_repo().list_all(limit=500)
        if item.get("device_id")
    }
    enriched_documents = []
    for document in documents:
        enriched = dict(document)
        state_document = states.get(str(enriched.get("device_id", "")))
        if state_document and _state_applies_to_document(enriched, state_document):
            state = str(state_document.get("state", "Normal"))
            enriched["device_state"] = state
            enriched["last_response_action"] = state_document.get("last_action")
            enriched["device_state_reason"] = state_document.get("reason")
            if state == "Temporarily Isolated":
                enriched["network_isolated"] = True
            if is_blocked_state(state):
                enriched["network_blocked"] = True
        enriched_documents.append(enriched)
    return enriched_documents


def _active_simulation_documents() -> List[Dict[str, Any]]:
    config = sim_config_store().get()
    documents = generate_sensor_events(config)
    if not _mongo_available():
        return documents

    repo = _state_repo()
    active_documents: List[Dict[str, Any]] = []
    skipped_targets = 0
    for document in documents:
        current_state = repo.get(str(document.get("device_id", "")))
        state = str((current_state or {}).get("state", "Normal"))
        if is_blocked_state(state):
            skipped_targets += 1
            continue
        document["device_state"] = state
        if state == "Temporarily Isolated":
            document["network_isolated"] = True
            document["simulation_note"] = "Device is temporarily isolated; telemetry is marked as restricted."
        active_documents.append(document)

    if active_documents:
        return active_documents

    fallback = generate_sensor_event()
    fallback.update({
        "device_state": "Quarantined",
        "network_blocked": True,
        "simulation_skipped": True,
        "simulation_note": "No active non-quarantined simulated device was available.",
        "skipped_blocked_events": skipped_targets,
    })
    return [fallback]


def _history_for_document(document: Dict[str, Any], limit: int = 200) -> List[Dict[str, Any]]:
    device_id = str(document.get("device_id", ""))
    if not device_id:
        return []
    if _mongo_available():
        sensor_repo, _, _ = _repos()
        return sensor_repo.recent_for_device(device_id, limit)
    return [item for item in _fallback_telemetry(limit * 2) if str(item.get("device_id", "")) == device_id][:limit]


def _analyze(
    document: Dict[str, Any],
    attack_detected_hook: Optional[Callable[[Any, Any], None]] = None,
) -> Dict[str, Any]:
    alert = predictor().predict(document)
    attack_prediction = attack_predictor().predict(document)
    if attack_prediction.predicted_attack and attack_detected_hook is not None:
        attack_detected_hook(alert, attack_prediction)
    live_context = live_correlator().build(document, _history_for_document(document), alert, attack_prediction)
    correlation = validator().validate(alert, document, attack_prediction, live_context)
    ars_prediction = ars_response_model().predict(document, attack_prediction)
    decision = decide_response_with_model(alert, correlation, ars_prediction)
    partial_analysis = {
        "alert": json_safe(alert.__dict__),
        "attack_prediction": json_safe(attack_prediction.__dict__),
        "live_correlation": json_safe(live_context.__dict__),
        "correlation": json_safe(correlation.__dict__),
        "ars_response": json_safe(ars_prediction.__dict__),
        "decision": json_safe(decision.__dict__),
    }
    privacy = phi_guard().redact(build_evidence_text(document, partial_analysis))
    return {
        **partial_analysis,
        "privacy": json_safe(privacy.__dict__),
    }


def _prediction_history_document(
    document: Dict[str, Any],
    analysis: Dict[str, Any],
    command: Dict[str, Any] | None = None,
    state_update: Dict[str, Any] | None = None,
    sensor_log_id: Any = None,
) -> Dict[str, Any]:
    alert = analysis.get("alert", {})
    attack = analysis.get("attack_prediction", {})
    correlation = analysis.get("correlation", {})
    live_correlation = analysis.get("live_correlation", {})
    decision = analysis.get("decision", {})
    ars_response = analysis.get("ars_response", {})
    return json_safe({
        "created_at": utc_now_iso(),
        "source": "simulated_live_pipeline",
        "sensor_log_id": str(sensor_log_id) if sensor_log_id else "",
        "timestamp": document.get("timestamp"),
        "device_id": document.get("device_id"),
        "device_type": document.get("device_type"),
        "ward": document.get("ward"),
        "attack_type": document.get("attack_type"),
        "is_attack": document.get("is_attack"),
        "priority": alert.get("priority"),
        "priority_confidence": alert.get("confidence"),
        "priority_reason": alert.get("reason"),
        "attack_label": attack.get("predicted_label"),
        "predicted_attack": attack.get("predicted_attack"),
        "attack_confidence": attack.get("confidence"),
        "anomaly_flag": attack.get("anomaly_flag"),
        "anomaly_score": attack.get("anomaly_score"),
        "risk_score": attack.get("risk_score"),
        "correlation_verdict": live_correlation.get("recommended_verdict"),
        "correlation_score": live_correlation.get("correlation_score"),
        "related_alert_count": live_correlation.get("related_alert_count"),
        "confirmed_real_attack": correlation.get("confirmed_real_attack"),
        "confirmed_critical": correlation.get("confirmed_critical"),
        "correlation_action": correlation.get("final_action"),
        "ars_action": ars_response.get("action_label"),
        "ars_confidence": ars_response.get("confidence"),
        "decision_action": decision.get("action"),
        "device_state": (state_update or {}).get("state"),
        "command_action": (command or {}).get("action"),
        "analysis": analysis,
    })


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mongo": _mongo_available(),
        "mode": "mongodb" if _mongo_available() else "mock",
        "models": {
            "priority_model": (MODELS_DIR / "alert_prioritization_model.pkl").exists(),
            "encoders": (MODELS_DIR / "label_encoders.pkl").exists(),
            "attack_random_forest": (THREAT_INTEL_DIR / "random_forest_model.pkl").exists(),
            "attack_isolation_forest": (THREAT_INTEL_DIR / "isolation_forest_model.pkl").exists(),
            "attack_encoders": (THREAT_INTEL_DIR / "encoders.pkl").exists(),
            "ars_response_model": (ARS_MODELS_DIR / "ars_decision_model_final.pkl").exists(),
            "phi_model": (ARS_MODELS_DIR / "ARS PHI.pkl").exists() or (ARS_MODELS_DIR / "ars_phi_model.pkl").exists(),
        },
        "simulator": simulator().status(),
        "simulation_config": sim_config_store().get().to_dict(),
        "control": {
            "transport": settings.device_control_transport,
            "http_endpoint_configured": bool(settings.device_control_endpoint),
            "mqtt_broker_configured": bool(settings.device_control_mqtt_broker),
            "physical_control_enabled": bool(settings.device_control_endpoint or settings.device_control_mqtt_broker),
            "default_mode": "backend_only_manual_shutdown",
        },
        "simulated_sensors": {
            "count": len(DEVICE_PROFILES),
            "items": json_safe(DEVICE_PROFILES),
        },
        "hardware_devices": {
            "count": len(hardware_device_roster()),
            "items": json_safe(hardware_device_roster()),
        },
        "source_paths": {
            "research_root": str(RESEARCH_ROOT),
            "alert_module_root": str(ALERT_MODULE_ROOT),
        },
    }


@app.get("/dashboard/summary")
def dashboard_summary():
    mongo = _mongo_available()
    total_logs = 0
    attack_logs = 0
    responses = 0
    devices: List[str] = []
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    if mongo:
        sensor_repo, response_repo, _ = _repos()
        total_logs = sensor_repo.count()
        attack_logs = sensor_repo.attack_count()
        responses = response_repo.count()
        devices = sensor_repo.distinct_devices()
        prediction_total = _prediction_repo().count()
        severity_counts = _prediction_repo().priority_counts()
    else:
        data = _fallback_telemetry(5000)
        total_logs = len(data)
        attack_logs = len([row for row in data if row.get("is_attack") or row.get("attack_type") != "normal"])
        devices = sorted({str(row.get("device_id")) for row in data if row.get("device_id")})
        prediction_total = 0

    grouped = read_csv_records(PROCESSED_DIR / "grouped_incidents.csv", limit=1000)
    training_summary = read_text(RESULTS_DIR / "03_model_training_summary.txt")
    grouping_summary = read_text(RESULTS_DIR / "04_alert_grouping_summary.txt")
    alert_reduction = "available"
    if mongo and prediction_total > 0:
        alert_reduction = f"{(1 - (len(grouped) / prediction_total)) * 100:.1f}%"
    return {
        "mode": "mongodb" if mongo else "mock",
        "totalLogs": total_logs,
        "attackLogs": attack_logs,
        "responses": responses,
        "activeDevices": len(devices),
        "incidentGroups": len(grouped),
        "modelAccuracy": "100.00%" if "100.00%" in training_summary else "available",
        "alertReduction": alert_reduction,
        "severityCounts": severity_counts if mongo else _severity_counts(grouped),
        "devices": devices[:20],
    }


def _severity_counts(incidents: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for incident in incidents:
        priority = str(incident.get("incident_priority", "LOW")).upper()
        if priority in counts:
            counts[priority] += 1
    return counts


@app.get("/telemetry")
def telemetry(limit: int = 50):
    if _mongo_available():
        sensor_repo, _, _ = _repos()
        return {"mode": "mongodb", "items": json_safe(_overlay_device_states(sensor_repo.latest(limit)))}
    return {"mode": "mock", "items": _fallback_telemetry(limit)}


@app.get("/sensors")
def sensors():
    return {
        "count": len(DEVICE_PROFILES),
        "items": json_safe(DEVICE_PROFILES),
    }


@app.get("/simulation/config")
def simulation_config():
    return sim_config_store().get().to_dict()


@app.post("/simulation/config")
def update_simulation_config(payload: SimulationConfigRequest):
    config = sim_config_store().update(
        data_mode=payload.data_mode,
        simulation_mode=payload.simulation_mode,
        anomaly_device_id=payload.anomaly_device_id,
        anomaly_type=payload.anomaly_type,
    )
    stopped = None
    if config.data_mode == "real":
        stopped = simulator().stop()
    return {
        "config": config.to_dict(),
        "simulator": stopped or simulator().status(),
    }


@app.get("/hardware/devices")
def hardware_devices():
    roster = hardware_device_roster()
    return {
        "count": len(roster),
        "items": json_safe(roster),
    }


@app.get("/logs")
def logs(limit: int = 80):
    return telemetry(limit)


@app.get("/predictions/recent")
def recent_predictions(limit: int = 10):
    if _mongo_available():
        return {"mode": "mongodb", "items": json_safe(_prediction_repo().latest(limit))}
    return {"mode": "mock", "items": []}


@app.post("/simulate/tick")
def simulate_tick(insert: bool = True):
    config = sim_config_store().get()
    if config.data_mode == "real":
        return {
            "event": {
                "source": "physical_sensor",
                "data_mode": "real",
                "simulation_skipped": True,
                "simulation_note": "Real Data Mode is active; simulator tick is disabled.",
            },
            "analysis": None,
            "command": None,
            "skipped": True,
            "message": "Real Data Mode is active; simulator tick is disabled.",
        }
    return _run_simulation_tick(insert=insert)


def _run_simulation_tick(insert: bool = True):
    documents = _active_simulation_documents()
    if documents[0].get("simulation_skipped"):
        return {
            "event": json_safe(documents[0]),
            "events": json_safe(documents),
            "processed_events": [],
            "analysis": None,
            "command": None,
            "skipped": True,
            "message": documents[0]["simulation_note"],
        }

    processed_events = []
    if _mongo_available() and insert:
        sensor_repo, response_repo, controller = _repos()
    else:
        sensor_repo = response_repo = controller = None

    for document in documents:
        command = None
        state_update = None
        staged_command = None
        staged_state_update = None
        insert_result = None
        if sensor_repo is not None:
            insert_result = sensor_repo.insert_one(document)

        def stage_ai_threat_isolation(alert: Any, attack_prediction: Any) -> None:
            nonlocal staged_command, staged_state_update
            if controller is None or staged_state_update is not None:
                return
            current_state = _state_repo().get(str(document.get("device_id", ""))) if _mongo_available() else None
            state = str((current_state or {}).get("state", "Normal"))
            if is_blocked_state(state) or state == "Temporarily Isolated":
                return
            reason = "AI Threat Intel predicted an attack; device is temporarily isolated while correlation and AR validation continue."
            staged_command, staged_state_update = _issue_response_action(
                document,
                "temporary_isolate",
                reason,
                controller,
                metadata={
                    "stage": "ai_threat_intel_prevalidation",
                    "priority": getattr(alert, "priority", None),
                    "attack_prediction": json_safe(getattr(attack_prediction, "__dict__", {})),
                    "simulated": True,
                },
            )

        analysis = _analyze(document, attack_detected_hook=stage_ai_threat_isolation)
        analysis = _apply_targeted_anomaly_response(document, analysis)
        analysis = _apply_staged_validation_outcome(analysis, staged_state_update is not None)
        action = analysis["decision"]["action"]
        if sensor_repo is not None and action != "monitor":
            if action == "temporary_isolate" and staged_command is not None:
                command = staged_command
                state_update = staged_state_update
            else:
                command, state_update = _issue_response_action(
                    document,
                    action,
                    analysis["decision"]["reason"],
                    controller,
                    metadata={
                        "stage": "post_correlation_validation",
                        "priority": analysis["alert"]["priority"],
                        "ars_response": analysis["ars_response"],
                        "analysis": analysis,
                        "simulated": True,
                    },
                )
        elif sensor_repo is not None:
            current_state = _state_repo().get(str(document.get("device_id", ""))) if _mongo_available() else None
            current_state_name = str((current_state or {}).get("state", "Normal"))
            response_repo.insert_one({
                "device_id": document["device_id"],
                "action": "log_and_monitor",
                "status": "completed",
                "created_at": utc_now_iso(),
                "metadata": analysis,
            })
            if current_state_name == "Temporarily Isolated" or is_blocked_state(current_state_name):
                state_update = current_state
            else:
                state_update = _record_device_state(
                    document["device_id"],
                    "log_and_monitor",
                    analysis["decision"]["reason"],
                    metadata={"analysis": analysis},
                    device_type=str(document.get("device_type", "")),
                )
        if sensor_repo is not None:
            _prediction_repo().insert_one(_prediction_history_document(
                document=document,
                analysis=analysis,
                command=command,
                state_update=state_update,
                sensor_log_id=getattr(insert_result, "inserted_id", ""),
            ))
        processed_events.append({
            "event": json_safe(document),
            "analysis": analysis,
            "command": json_safe(command),
            "state_update": json_safe(state_update),
        })

    primary = processed_events[0]
    return {
        **primary,
        "events": json_safe(documents),
        "processed_events": json_safe(processed_events),
    }


@app.post("/simulate/start")
def simulate_start(interval_seconds: float = 4.5):
    config = sim_config_store().get()
    if config.data_mode == "real":
        return {
            **simulator().stop(),
            "blocked": True,
            "message": "Real Data Mode is active; simulator start is disabled.",
        }
    return simulator().start(lambda: _run_simulation_tick(insert=True), interval_seconds=interval_seconds)


@app.post("/simulate/stop")
def simulate_stop():
    return simulator().stop()


@app.get("/simulate/status")
def simulate_status():
    return simulator().status()


@app.get("/simulate/latest")
def simulate_latest():
    return {"item": json_safe(simulator().latest())}


@app.post("/simulate/replay")
def simulate_replay(delay_ms: int = 0, dry_run: bool = True):
    if not _mongo_available() and not dry_run:
        return {"inserted": 0, "dry_run": dry_run, "message": "MongoDB unavailable; replay skipped."}
    sensor_repo, _, _ = _repos()
    documents = list(load_csv_documents(sorted(RAW_DIR.glob("*_sensor_log.csv"))))
    inserted = replay_documents(documents, sensor_repo.collection, delay_ms=delay_ms, dry_run=dry_run)
    return {"inserted": inserted, "dry_run": dry_run}


@app.post("/alerts/predict")
def predict_alert(document: Dict[str, Any]):
    return _analyze(document)


@app.post("/alerts/analyze")
def analyze_event(document: Dict[str, Any]):
    command = None
    state_update = None
    staged_command = None
    staged_state_update = None

    def stage_ai_threat_isolation(alert: Any, attack_prediction: Any) -> None:
        nonlocal staged_command, staged_state_update
        if not _mongo_available() or staged_state_update is not None:
            return
        _, _, controller = _repos()
        current_state = _state_repo().get(str(document.get("device_id", "")))
        state = str((current_state or {}).get("state", "Normal"))
        if is_blocked_state(state) or state == "Temporarily Isolated":
            return
        reason = "AI Threat Intel predicted an attack; device is temporarily isolated while correlation and AR validation continue."
        staged_command, staged_state_update = _issue_response_action(
            document,
            "temporary_isolate",
            reason,
            controller,
            metadata={
                "stage": "ai_threat_intel_prevalidation",
                "priority": getattr(alert, "priority", None),
                "attack_prediction": json_safe(getattr(attack_prediction, "__dict__", {})),
                "simulated": False,
            },
        )

    analysis = _analyze(document, attack_detected_hook=stage_ai_threat_isolation)
    analysis = _apply_staged_validation_outcome(analysis, staged_state_update is not None)
    if _mongo_available():
        _, _, controller = _repos()
        action = analysis["decision"]["action"]
        if action != "monitor":
            if action == "temporary_isolate" and staged_command is not None:
                command = staged_command
                state_update = staged_state_update
            else:
                command, state_update = _issue_response_action(
                    document,
                    action,
                    analysis["decision"]["reason"],
                    controller,
                    metadata={
                        "stage": "post_correlation_validation",
                        "analysis": analysis,
                        "simulated": False,
                    },
                )
    return {
        **analysis,
        "command": json_safe(command),
        "state_update": json_safe(state_update),
        "staged_isolation": json_safe(staged_state_update),
    }


@app.get("/incidents")
def incidents(limit: int = 50):
    items = read_csv_records(PROCESSED_DIR / "grouped_incidents.csv", limit=limit)
    return {"mode": "precomputed_dbscan", "items": items}


def _refresh_alert_grouping() -> Dict[str, Any]:
    script_path = BASE_DIR / "scripts" / "run_alert_grouping.py"
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Alert grouping launcher not found: {script_path}")

    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=completed.stderr.strip() or "Alert grouping refresh failed",
        )

    return {
        "status": "ok",
        "message": "Alert grouping refreshed from stored MongoDB logs.",
        "stdout": completed.stdout.strip(),
    }


@app.post("/incidents/refresh")
def refresh_incidents():
    return _refresh_alert_grouping()


@app.get("/incidents/live")
def live_incident(device_id: str, limit: int = 200):
    document = {"device_id": device_id}
    history = _history_for_document(document, limit)
    if not history:
        return {"mode": "live_aice", "item": None}
    latest = history[0]
    analysis = _analyze(latest)
    return {"mode": "live_aice", "item": analysis["live_correlation"], "analysis": analysis}


@app.get("/responses")
def responses(limit: int = 50):
    if _mongo_available():
        _, response_repo, _ = _repos()
        return {"mode": "mongodb", "items": json_safe(response_repo.latest(limit))}
    return {"mode": "mock", "items": []}


@app.post("/responses/action")
def response_action(payload: ResponseActionRequest):
    command_payload = _control_metadata(payload.action, {
        "requested_by": payload.requested_by,
        "reason": payload.reason,
        "manual_dashboard_action": True,
    })
    if _mongo_available():
        _, _, controller = _repos()
        command = controller.issue(
            payload.device_id,
            payload.action,
            metadata=command_payload,
            requested_by=payload.requested_by,
        )
        state_update = _record_device_state(
            payload.device_id,
            payload.action,
            payload.reason,
            metadata=command_payload,
        )
        return {"mode": "mongodb", "issued": True, "command": json_safe(command.__dict__), "state_update": json_safe(state_update)}
    return {
        "mode": "mock",
        "issued": True,
        "command": {
            "command_id": "MOCK-COMMAND",
            "device_id": payload.device_id,
            "action": payload.action,
            "status": "simulated",
            "metadata": command_payload,
        },
    }


@app.get("/quarantine")
def quarantine(limit: int = 50):
    if _mongo_available():
        _, response_repo, _ = _repos()
        items = response_repo.find_by_actions(["quarantine", "shutdown", "temporary_isolate"], limit)
        return {"mode": "mongodb", "items": json_safe(items)}
    return {"mode": "mock", "items": []}


@app.get("/devices/states")
def device_states(limit: int = 100):
    if _mongo_available():
        return {"mode": "mongodb", "items": json_safe(_state_repo().list_all(limit))}
    return {"mode": "mock", "items": []}


@app.get("/devices/states/{device_id}")
def device_state(device_id: str):
    if _mongo_available():
        return {"mode": "mongodb", "item": json_safe(_state_repo().get(device_id))}
    return {"mode": "mock", "item": None}


@app.get("/reports/summary")
def report_summary():
    summary = dashboard_summary()
    report = ReportSummary(
        generated_at=utc_now_iso(),
        total_logs=summary["totalLogs"],
        attack_logs=summary["attackLogs"],
        total_responses=summary["responses"],
        active_devices=summary["activeDevices"],
        model_accuracy=summary["modelAccuracy"],
        alert_reduction=summary["alertReduction"],
        notes=[
            "Priority is generated live from the saved Random Forest model.",
            "Attack prediction is generated live from the latest AI Threat Intel Random Forest, encoder pack, and Isolation Forest models.",
            "Response action is generated live from the AR System response model with safety overrides.",
            "PHI guard uses the AR System PHI model plus regex redaction before evidence is shown in reports.",
            "Incident grouping uses precomputed DBSCAN results until continuous windows are enabled.",
            "Quarantine is currently backend-only; operators are instructed to manually turn off quarantined physical sensors.",
        ],
    )
    payload = json_safe(report.__dict__)
    payload["mode"] = summary["mode"]
    payload["severity_counts"] = summary["severityCounts"]
    payload["simulator"] = json_safe(simulator().status())
    payload["simulation_config"] = sim_config_store().get().to_dict()
    payload["active_restrictions"] = {"count": 0, "items": []}
    payload["recent_predictions"] = []
    payload["latest_event"] = None
    payload["latest_analysis"] = None

    if _mongo_available():
        restricted_states = [
            item for item in _state_repo().list_all(20)
            if str(item.get("state", "")) in {"Temporarily Isolated", "Quarantined"}
        ]
        payload["active_restrictions"] = {
            "count": len(restricted_states),
            "items": json_safe(restricted_states[:8]),
        }
        payload["recent_predictions"] = json_safe(_prediction_repo().latest(5))

    latest = telemetry(1)["items"]
    if latest:
        payload["latest_event"] = json_safe(latest[0])
        latest_analysis = _analyze(latest[0])
        payload["latest_analysis"] = json_safe(latest_analysis)
        payload["redacted_evidence"] = latest_analysis["privacy"]["redacted_text"]
    else:
        payload["redacted_evidence"] = "No telemetry evidence available."
    return payload


@app.post("/privacy/redact")
def privacy_redact(payload: RedactionRequest):
    return json_safe(phi_guard().redact(payload.text).__dict__)


@app.on_event("shutdown")
def stop_simulator_on_shutdown():
    simulator().stop()
