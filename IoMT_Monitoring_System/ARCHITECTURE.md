# Planned MongoDB + AI Response Architecture

This workspace is the integrated FastAPI + Next.js demonstration layer. It now uses only these main project locations:

```text
C:\Users\ahame\Documents\Ukasha Research\final-research-project
C:\Users\ahame\Documents\Ukasha Research\IoMT_Monitoring_System
```

The planned architecture extends those modules into a live system with:

1. Sensor telemetry ingestion into MongoDB.
2. AI Threat Intel attack prediction.
3. AI-based alert prioritization and DBSCAN grouping evidence.
4. Live AICE-style MongoDB window correlation and validation of severity.
5. AR System response-model orchestration for log, quarantine, rollback, or monitor actions, with safety overrides, PHI redaction, and device-state tracking.
6. A dashboard that requests actions through the backend.

## Recommended Structure

```text
src/
  common/        Shared dataclasses and settings
  mongo/         MongoDB client and repositories
  simulation/    Replay existing CSVs as near-real-time sensor traffic
  ai/            Attack prediction and priority inference over incoming logs
  correlation/   Live AICE-style validation of true criticality vs false alarms
  response/      AR System model adapter, PHI guard, and policy engine for final actions
  control/       Device control adapter for isolate/shutdown commands
  api/           FastAPI backend used by the dashboard
  monitoring/    Existing research pipeline scripts
frontend/       Future live dashboard implementation
scripts/         CLI entry points for simulation and API startup
data/            Raw, processed, and simulated data
models/          Trained model artifacts and encoders
results/         Reports, charts, and dashboard output
```

The local `data/`, `models/`, and `results/` folders are the active priority/grouping source used by the dashboard and API.

## Runtime Flow

```text
Sensors or replay simulator
  -> MongoDB sensor_logs
  -> AI Threat Intel attack prediction
  -> AI prioritizer
  -> live AICE correlation validator
  -> AR System response model
  -> response policy with safety overrides
  -> PHI-redacted evidence
  -> device_states registry
  -> control adapter
  -> MongoDB responses
  -> dashboard
```

## Implemented Stack

- Frontend: Next.js dashboard in `frontend/`
- Backend: FastAPI app in `src/api/app.py`
- Database: MongoDB Atlas, using `sensor_logs` and `responses`
- Attack prediction models: `AI Threat Intel/random_forest_model.pkl` and `AI Threat Intel/isolation_forest_model.pkl`
- Priority model: `models/alert_prioritization_model.pkl`
- Response model: `AR System/models/ars_decision_model_final.pkl`
- PHI model: `AR System/models/ARS PHI.pkl`
- Grouping/correlation evidence: DBSCAN output in `data/processed/grouped_incidents.csv`
- Live correlation: recent MongoDB logs from the same `device_id` are grouped in a 5-minute window and scored before final response.
- Device states: automatic and manual actions update `device_states`; quarantined devices are skipped by the simulator while other sensors continue logging.
- Simulation: random live sensor generator in `src/simulation/generator.py`
- Control placeholder: `src/control/device_controller.py`

## API Surface

```text
GET  /health
GET  /dashboard/summary
GET  /telemetry
GET  /logs
POST /simulate/tick
POST /alerts/predict
POST /alerts/analyze
GET  /incidents
GET  /responses
POST /responses/action
GET  /quarantine
GET  /reports/summary
```

## Safety Notes

- Dashboard actions should never talk directly to hardware.
- The backend should validate permissions and correlation before sending control commands.
- Shutdown is simulated only. In production it must be a last-resort workflow with approval, audit logs, and physical safety checks.
- The MongoDB URI should live in `.env`, not in source control.
- The AI Threat Intel bundle now includes `encoders.pkl`, and `src/ai/attack_prediction.py` uses those saved encoders directly, with safe fallbacks only for unseen live simulator categories.
