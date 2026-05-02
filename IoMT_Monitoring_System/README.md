# IoMT Monitoring System — Alert Prioritization & Alert Grouping

**Student:** MMM Ukasha (IT22904232)
**Project ID:** 25-26J-70
**Supervisor:** Mr. Kanishka Yapa
**Co-Supervisor:** Mr. Deemantha Siriwardhana

---

## Project Overview
Real-Time SIEM-Based Monitoring System for IoMT Cybersecurity.
This component covers two novel features:
1. Alert Prioritization (CRITICAL / HIGH / MEDIUM / LOW)
2. Alert Grouping (cluster related alerts into one incident)

## Devices Monitored
| Device              | Ward         | Life Support | Criticality |
|---------------------|--------------|--------------|-------------|
| Pulse Oximeter      | ICU          | TRUE         | 9           |
| ECG Monitor         | Ward_02      | FALSE        | 7           |
| Temperature Sensor  | General_Ward | FALSE        | 6           |
| Motion Sensor       | Ward_01      | FALSE        | 5           |

## Attack Types in Dataset
- sensor_spoofing, mqtt_port_manipulation, device_identity_spoofing
- protocol_anomaly, flooding, ip_spoofing, data_tampering, ddos, normal

## Run Order
```
Step 1: python src/monitoring/01_merge_and_label.py
Step 2: python src/monitoring/02_preprocess.py
Step 3: python src/monitoring/03_train_prioritization.py
Step 4: python src/monitoring/04_alert_grouping.py
Step 5: python src/monitoring/05_demo.py
```

---

## Planned MongoDB Architecture

This workspace now also includes the scaffolding needed for the planned live system:

- `src/common/` for shared data models and environment settings
- `src/mongo/` for MongoDB connection and collections
- `src/simulation/` for replaying the existing CSV logs as near-real-time sensor traffic
- `src/ai/` for priority inference over incoming telemetry
- `src/correlation/` for live AICE-style MongoDB windowing and true-attack validation
- `src/response/` for AR System model inference and the final action policy
- `src/response/phi_guard.py` for AR System PHI detection and redacted evidence generation
- `src/control/` for safe isolate/quarantine/shutdown command handling
- `predictions` MongoDB collection for persistent AI priority and attack-prediction history
- `src/api/` for the FastAPI backend used by the dashboard
- `frontend/` for the Next.js live dashboard implementation
- `scripts/replay_existing_data.py` to seed MongoDB from the current dataset
- `scripts/run_api.py` to start the backend

## Source-of-Truth Project Paths

The integrated dashboard/backend uses these folders by default:

```text
Original docs and system modules:
C:\Users\ahame\Documents\Ukasha Research\final-research-project

Runnable dashboard, API, priority model, grouping data, and results:
C:\Users\ahame\Documents\Ukasha Research\IoMT_Monitoring_System
```

These can be overridden with:

```text
RESEARCH_PROJECT_ROOT=<path to final-research-project>
ALERT_MODULE_ROOT=<path to IoMT_Monitoring_System or an external alert module>
```

### Runtime Flow

```text
Sensors or simulator
  -> MongoDB sensor_logs
  -> AI Threat Intel attack prediction
  -> AI prioritization
  -> live AICE correlation validation
  -> AR System response model
  -> response policy with safety overrides
  -> PHI redaction for reports/evidence
  -> device state registry
  -> prediction history
  -> device control adapter
  -> MongoDB responses
  -> dashboard
```

### Safety Notes

- The dashboard should call the backend, not the sensor directly.
- Shutdown should be the last control action after validation.
- For production use, keep the MongoDB URI in `.env` and out of source control.
- Prefer quarantine or network isolation over immediate power-off for medical devices.

### Simulation Startup

1. Copy `.env.example` to `.env` and fill in the MongoDB values.
2. Install backend dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the FastAPI backend:

   ```bash
   python scripts/run_api.py
   ```

4. Start the frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. Open `http://localhost:3000`.

6. Use the simulator control in the dashboard top bar to start or stop backend-generated live telemetry. The backend will:
   - generate realistic IoMT sensor events,
   - skip devices already marked as `Quarantined`,
   - mark temporarily isolated devices as restricted,
   - insert active telemetry into MongoDB,
   - run attack prediction, priority prediction, live correlation, AR response, and PHI redaction,
   - update `responses` and `device_states` when a response action is selected.

Backend simulator endpoints:

```text
POST /simulate/start?interval_seconds=4.5
POST /simulate/stop
GET  /simulate/status
GET  /simulate/latest
GET  /predictions/recent?limit=10
POST /simulate/tick?insert=true
POST /simulate/tick?insert=false
```

### Optional Data Replay

Replay the existing raw CSVs into MongoDB:

   ```bash
   python scripts/replay_existing_data.py
   ```

### Frontend Preview Build

   ```bash
   cd frontend
   npm run build
   npm run start -- --hostname localhost --port 3001
   ```

### Implementation Assumptions

- Frontend: Next.js, chosen for a professional dashboard app and clean routing surface.
- Backend: FastAPI, chosen because the trained ML artifacts are Python pickles.
- Storage: MongoDB Atlas database `siem_db`, collections `sensor_logs` and `responses`.
- Prediction history: model outputs are saved in the `predictions` collection so the AI Priority and Attack Prediction pages can show the latest 5-10 decisions after refresh.
- Attack prediction: live attack classification uses the latest `AI Threat Intel/random_forest_model.pkl`, `AI Threat Intel/isolation_forest_model.pkl`, and `AI Threat Intel/encoders.pkl`.
- Priority prediction: live priority prediction uses the saved Random Forest model and encoders from this project folder's `models/`.
- Response prediction: live response action uses `final-research-project/AR System/models/ars_decision_model_final.pkl`, then applies safety overrides before writing commands.
- PHI redaction: report evidence uses `final-research-project/AR System/models/ARS PHI.pkl` plus regex redaction before display/export.
- Correlation: live AICE-style correlation now reads recent MongoDB logs for the same device in a 5-minute window; DBSCAN incident outputs are still reused from `data/processed/grouped_incidents.csv` as precomputed evidence.
- AICE: integrated conceptually through the correlation, severity validation, response, and recommendation flow.
- Current hardware-control mode: backend-only. Real sensor logs can be inserted into MongoDB directly, and quarantine records the device state while instructing the operator to manually turn off the sensor.
- Real Data Mode disables backend simulation so physical sensor logs in MongoDB drive the telemetry, AI, correlation, and response flow.
- Simulation Mode is dashboard-controlled. Normal Mode emits normal readings, while Anomaly Mode targets one selected sensor and keeps the other simulated sensors normal.
- Future Node-RED/MQTT mode: represented by `src/control/device_controller.py`; set `DEVICE_CONTROL_TRANSPORT=http` with `DEVICE_CONTROL_ENDPOINT` for a Node-RED bridge, or `DEVICE_CONTROL_TRANSPORT=mqtt` with broker settings for direct ESP32 control. The optional Node-RED flow lives at `integration/node-red/http-control-bridge.json`.
- Device state tracking: `device_states` records Normal, Temporarily Isolated, Quarantined, and Restored states. Quarantined devices are skipped by the simulator so other sensors continue logging.
- AI Threat Intel note: the latest bundle includes `encoders.pkl`, and the live adapter now uses those saved encoders directly with safe fallbacks for unseen simulator categories.
