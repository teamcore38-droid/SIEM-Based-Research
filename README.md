<div align="center">

# SIEM-Based Research

**An integrated IoMT cybersecurity monitoring platform for telemetry simulation, AI-driven threat detection, live correlation, automated response, and dashboard-based operations.**

[![Platform](https://img.shields.io/badge/Platform-IoMT%20Security-0f172a?style=for-the-badge)](./IoMT_Monitoring_System)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-059669?style=for-the-badge)](./IoMT_Monitoring_System/src/api)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js-111827?style=for-the-badge)](./IoMT_Monitoring_System/frontend)
[![Database](https://img.shields.io/badge/Database-MongoDB-166534?style=for-the-badge)](./IoMT_Monitoring_System/.env.example)
[![Models](https://img.shields.io/badge/ML-Random%20Forest%20%2B%20Isolation%20Forest-7c3aed?style=for-the-badge)](./final-research-project/AI%20Threat%20Intel)

</div>

## Overview

This repository packages the full research and demo stack for an IoMT SIEM-style monitoring system. It combines simulated or real sensor telemetry, MongoDB event logging, AI Threat Intelligence, alert prioritization, AICE-style live correlation, automated response decisions, and a dashboard for security operations.

The project is designed to support both academic demonstration and practical extension. You can run it today with simulation only, or evolve it later toward physical sensors, Node-RED/MQTT control, and production-grade orchestration.

## What This Repository Contains

| Area | Purpose |
| --- | --- |
| [`IoMT_Monitoring_System`](./IoMT_Monitoring_System) | Main runnable system with FastAPI backend, Next.js dashboard, simulation engine, MongoDB integration, AI orchestration, and response workflow |
| [`final-research-project`](./final-research-project) | Research datasets, trained models, AICE module, AR System assets, and supporting experiments |
| [`hardware-layer`](./hardware-layer) | Arduino / ESP32 code for ECG, heart-rate, temperature, and fall-detection sensor devices |

## Key Capabilities

| Capability | Description |
| --- | --- |
| Telemetry Ingestion | Accepts simulated data now and can be extended to real sensor streams later |
| AI Threat Intel | Uses Random Forest, Isolation Forest, and saved encoders for attack prediction |
| AI Prioritization | Assigns `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW` severity to incoming alerts |
| Live Correlation | Performs AICE-style validation on recent MongoDB history before final action |
| Automated Response | Uses AR model inference plus safety overrides for isolation, quarantine, rollback, and restore |
| Device State Tracking | Maintains `Normal`, `Temporarily Isolated`, `Quarantined`, and `Restored` states |
| Dashboard Operations | Shows telemetry, predictions, correlation output, response history, and reports |

## Runtime Architecture

```text
Sensors or simulator
  -> MongoDB sensor_logs
  -> AI Threat Intel attack prediction
  -> AI alert prioritization
  -> live AICE-style correlation validation
  -> AR System response model
  -> final response policy
  -> device state registry / prediction history / responses
  -> Next.js dashboard
```

## Quick Start

### 1. Clone the repository

```powershell
git clone https://github.com/teamcore38-droid/SIEM-Based-Research.git
cd SIEM-Based-Research
```

### 2. Configure environment variables

The integrated runtime uses [`IoMT_Monitoring_System/.env`](./IoMT_Monitoring_System/.env.example).

```powershell
cd IoMT_Monitoring_System
copy .env.example .env
```

Open `.env` and set at least:

```env
MONGODB_URI=your_mongodb_connection_string
MONGODB_DB=siem_db
MONGODB_SENSOR_COLLECTION=sensor_logs
MONGODB_RESPONSE_COLLECTION=responses
MONGODB_DEVICE_STATE_COLLECTION=device_states
MONGODB_PREDICTION_COLLECTION=predictions
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Keep these path variables unchanged unless you move folders:

```env
RESEARCH_PROJECT_ROOT=<repo>\final-research-project
ALERT_MODULE_ROOT=<repo>\IoMT_Monitoring_System
```

### 3. Install backend dependencies

```powershell
cd IoMT_Monitoring_System
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Start the backend API

```powershell
cd IoMT_Monitoring_System
python -m uvicorn src.api.app:app --reload
```

Backend URL:

```text
http://localhost:8000
```

### 5. Install frontend dependencies

Open a second terminal:

```powershell
cd SIEM-Based-Research\IoMT_Monitoring_System\frontend
npm install
```

### 6. Start the dashboard

```powershell
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

## First Run Checklist

1. Open `http://localhost:8000/health` and confirm the backend is reachable.
2. Open `http://localhost:3000` and confirm the dashboard loads.
3. Set `Data Mode` to `Simulation`.
4. Run a simulator tick or start the simulator from the dashboard top bar.
5. Confirm that data appears across Telemetry, MongoDB Logs, AI Priority, Attack Prediction, Correlation, and Response pages.

## Simulation Mode

Simulation mode is the fastest way to demonstrate the full end-to-end workflow.

Available sensors:

- Heart rate / pulse oximeter
- ECG monitor
- Temperature sensor
- Fall detection sensor

Supported simulation patterns:

- `Normal Mode` sends continuous normal data
- `Anomaly Mode` targets one selected sensor while keeping the others normal

Current system behavior:

- AI Threat Intel can stage temporary isolation for suspicious devices
- Correlation and response validation can escalate to quarantine or restore
- Quarantined sensors stop simulated telemetry
- Temporarily isolated sensors continue logging and appear as `Restricted`

## Real Data Mode

If physical sensors or another external process insert logs directly into MongoDB:

1. Switch the dashboard `Data Mode` to `Real`
2. Keep the backend running
3. Write sensor documents into the `sensor_logs` collection

In real mode:

- Backend simulation is disabled
- Telemetry and MongoDB Logs are read from MongoDB
- The backend still exposes the AI and response pipeline through its API
- Physical shutdown is still represented as backend state plus operator instruction

## Helpful API Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Service health and model availability |
| `GET /telemetry` | Latest telemetry records |
| `GET /predictions/recent?limit=10` | Latest saved prediction history |
| `POST /simulate/start?interval_seconds=4.5` | Start live simulation |
| `POST /simulate/stop` | Stop live simulation |
| `POST /simulate/tick?insert=true` | Run one processing tick and save it |
| `GET /devices/states` | View tracked device states |
| `GET /responses` | View response history |

## Optional Dataset Replay

To seed MongoDB with the included CSV telemetry data:

```powershell
cd IoMT_Monitoring_System
.venv\Scripts\activate
python scripts\replay_existing_data.py
```

## Optional Frontend Production Build

```powershell
cd IoMT_Monitoring_System\frontend
npm run build
npm run start
```

## Repository Structure

```text
SIEM-Based-Research/
|-- IoMT_Monitoring_System/
|-- final-research-project/
`-- hardware-layer/
```

Key integrated runtime folders:

- [`IoMT_Monitoring_System/src/api`](./IoMT_Monitoring_System/src/api) - FastAPI application layer
- [`IoMT_Monitoring_System/src/ai`](./IoMT_Monitoring_System/src/ai) - AI Threat Intel and priority adapters
- [`IoMT_Monitoring_System/src/correlation`](./IoMT_Monitoring_System/src/correlation) - live AICE-style validation
- [`IoMT_Monitoring_System/src/response`](./IoMT_Monitoring_System/src/response) - AR model adapter and final response policy
- [`IoMT_Monitoring_System/src/simulation`](./IoMT_Monitoring_System/src/simulation) - telemetry generation and replay
- [`IoMT_Monitoring_System/frontend`](./IoMT_Monitoring_System/frontend) - Next.js dashboard

## Hardware Layer

The [`hardware-layer`](./hardware-layer) folder contains separate ESP32/Arduino code for:

- ECG sensor
- Heart-rate sensor
- Temperature sensor
- Fall-detection sensor

These hardware sketches are not required to run the software demo. The repository can be demonstrated completely with simulation plus MongoDB.

## Troubleshooting

- If the dashboard loads but API calls fail, confirm the backend is running on `http://localhost:8000`.
- If MongoDB does not connect, verify `MONGODB_URI`, Atlas access rules, and credentials.
- If telemetry does not appear, run a simulator tick and recheck `GET /health`.
- If `npm install` fails, confirm Node.js 18+ is installed.
- If backend imports fail, confirm the virtual environment is activated before running Python commands.

## Notes

- This repository includes trained model artifacts and supporting datasets required by the demo.
- Physical device shutdown is currently simulated at the backend level unless you later connect Node-RED or MQTT transport.
- The integrated system depends on both `IoMT_Monitoring_System` and `final-research-project`, so keep them together inside the same cloned repository.
