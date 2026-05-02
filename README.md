# SIEM-Based Research

Integrated IoMT cybersecurity research and demo project containing:

- `IoMT_Monitoring_System` - integrated backend, frontend, simulation, MongoDB, AI detection, correlation, and response workflow
- `final-research-project` - supporting research modules, datasets, models, and prior experiments
- `hardware-layer` - Arduino / ESP32 sensor code for the four physical sensor devices

## Quick Start

### Backend

```powershell
cd IoMT_Monitoring_System
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn src.api.app:app --reload
```

### Frontend

```powershell
cd IoMT_Monitoring_System\frontend
npm install
npm run dev
```

Open the dashboard at `http://localhost:3000`.

## Configuration

- Create your own MongoDB Atlas cluster or local MongoDB instance.
- Update `IoMT_Monitoring_System\.env` with your own database connection values.
- Do not commit real secrets or private database URIs.
