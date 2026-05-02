# SIEM-Based Research

This repository contains the full IoMT cybersecurity research and demo system:

- `IoMT_Monitoring_System` - the integrated runnable system with FastAPI backend, Next.js dashboard, MongoDB logging, AI Threat Intel, AI prioritization, live correlation, AR response, and simulation
- `final-research-project` - supporting research assets, datasets, models, and earlier module implementations
- `hardware-layer` - Arduino / ESP32 code for the four physical sensor devices

## System Flow

```text
Sensors or simulator
  -> MongoDB sensor_logs
  -> AI Threat Intel attack prediction
  -> AI alert prioritization
  -> live AICE-style correlation
  -> AR System response model
  -> final response policy
  -> device states / prediction history / responses
  -> Next.js dashboard
```

## Prerequisites

- Windows, macOS, or Linux
- Python 3.11+ recommended
- Node.js 18+ recommended
- npm
- Git
- MongoDB Atlas or local MongoDB

## 1. Clone The Repository

```powershell
git clone https://github.com/teamcore38-droid/SIEM-Based-Research.git
cd SIEM-Based-Research
```

## 2. Configure Environment Variables

The integrated runtime uses `IoMT_Monitoring_System/.env`.

```powershell
cd IoMT_Monitoring_System
copy .env.example .env
```

Open `.env` and update at least:

```env
MONGODB_URI=your_mongodb_connection_string
MONGODB_DB=siem_db
MONGODB_SENSOR_COLLECTION=sensor_logs
MONGODB_RESPONSE_COLLECTION=responses
MONGODB_DEVICE_STATE_COLLECTION=device_states
MONGODB_PREDICTION_COLLECTION=predictions
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Keep these path variables as they are unless you move folders:

```env
RESEARCH_PROJECT_ROOT=<repo>\final-research-project
ALERT_MODULE_ROOT=<repo>\IoMT_Monitoring_System
```

Notes:

- If `MONGODB_URI` is blank, the backend may also try to read a local `mongoURI.txt`, but `.env` is the recommended setup.
- Do not commit real credentials.

## 3. Install Backend Dependencies

From the integrated app folder:

```powershell
cd IoMT_Monitoring_System
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Backend dependencies include FastAPI, Uvicorn, scikit-learn, joblib, pymongo, and dotenv support.

## 4. Start The Backend API

```powershell
cd IoMT_Monitoring_System
python -m uvicorn src.api.app:app --reload
```

The backend runs on:

```text
http://localhost:8000
```

Useful API routes:

- `GET /health`
- `GET /telemetry`
- `GET /predictions/recent?limit=10`
- `POST /simulate/start?interval_seconds=4.5`
- `POST /simulate/stop`
- `POST /simulate/tick?insert=true`
- `GET /devices/states`

## 5. Install Frontend Dependencies

Open a second terminal:

```powershell
cd SIEM-Based-Research\IoMT_Monitoring_System\frontend
npm install
```

## 6. Start The Frontend Dashboard

```powershell
npm run dev
```

Open:

```text
http://localhost:3000
```

The frontend talks to the backend using `NEXT_PUBLIC_API_BASE_URL`, which should point to `http://localhost:8000`.

## 7. Verify The System Is Running

After both services start:

1. Open `http://localhost:3000`
2. Check that the dashboard loads
3. Confirm the backend health route works at `http://localhost:8000/health`
4. Use the top-bar simulator controls to generate telemetry
5. Check that data appears in:
   - Dashboard
   - Telemetry
   - MongoDB Logs
   - AI Priority
   - Attack Prediction
   - Correlation
   - Response

## 8. Running In Simulation Mode

This is the easiest way to demonstrate the full project.

From the dashboard:

1. Set `Data Mode` to `Simulation`
2. Choose:
   - `Normal Mode` to send normal readings
   - `Anomaly Mode` to target one selected sensor
3. Select the anomaly sensor when in anomaly mode
4. Start the simulator or run manual ticks

Current simulated sensors:

- Heart rate / pulse oximeter
- ECG monitor
- Temperature sensor
- Fall detection sensor

Behavior:

- Normal sensors continue generating telemetry
- AI Threat Intel can temporarily isolate a suspicious device
- Correlation and response validation can escalate to quarantine or restore
- Quarantined devices are skipped by the simulator
- Temporarily isolated devices continue logging and appear as `Restricted`

## 9. Running In Real Data Mode

If physical sensors or an external writer insert logs directly into MongoDB:

1. Switch dashboard `Data Mode` to `Real`
2. Keep the backend running
3. Insert sensor documents into the `sensor_logs` collection

In real mode:

- Backend simulation is disabled
- Telemetry and MongoDB Logs read from MongoDB
- The integrated backend can still analyze events through its API routes
- Current physical control is backend-only, with operator instructions shown for quarantine

## 10. Optional: Replay Existing CSV Data

You can seed MongoDB with the existing dataset:

```powershell
cd IoMT_Monitoring_System
.venv\Scripts\activate
python scripts\replay_existing_data.py
```

This uses the raw CSV sensor logs already included in the repository.

## 11. Optional: Frontend Production Build

```powershell
cd IoMT_Monitoring_System\frontend
npm run build
npm run start
```

## 12. Project Structure

```text
SIEM-Based-Research/
|-- IoMT_Monitoring_System/
|-- final-research-project/
`-- hardware-layer/
```

Key integrated runtime folders:

- `IoMT_Monitoring_System/src/api` - FastAPI endpoints
- `IoMT_Monitoring_System/src/ai` - AI Threat Intel + priority adapters
- `IoMT_Monitoring_System/src/correlation` - live AICE-style validation
- `IoMT_Monitoring_System/src/response` - AR model + response policy
- `IoMT_Monitoring_System/src/simulation` - simulator and replay logic
- `IoMT_Monitoring_System/frontend` - Next.js dashboard

## 13. Hardware Layer

The `hardware-layer` folder contains separate Arduino / ESP32 code for:

- ECG sensor
- Heart rate sensor
- Temperature sensor
- Fall detection sensor

These are not required to run the software demo. The project can be demonstrated fully with simulation plus MongoDB.

## 14. Troubleshooting

- If the frontend loads but shows API errors:
  - confirm the backend is running on port `8000`
  - confirm `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
- If MongoDB is unavailable:
  - check `MONGODB_URI`
  - verify Atlas IP/network access
  - verify username and password
- If telemetry does not appear:
  - run a simulation tick
  - check `GET /health`
  - verify MongoDB collections are being created
- If `npm install` fails:
  - confirm Node.js 18+ is installed
- If Python packages fail:
  - confirm the virtual environment is activated before running backend commands

## 15. Important Notes

- This repository contains trained model files and research datasets required by the demo.
- Physical sensor shutdown is currently simulated at the backend level unless you later add Node-RED or MQTT control transport.
- The integrated project reuses the research assets in `final-research-project`, so keep both main folders together.
