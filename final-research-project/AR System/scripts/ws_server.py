"""
MedGuard-X | Dual-Mode WebSocket Server
========================================
Feeds dashboard via ws://localhost:8000/ws

Mode 1 (--mode trained) : Replays MODEL-TRAINED data from data/ folder
Mode 2 (--mode sim)      : Generates random simulated telemetry as fallback
Mode 3 (--mode real)     : Replays saved ESP32 logs from local_logs.jsonl
Mode 4 (--mode live)     : LIVE - subscribes to MQTT and streams real device data

Default: auto-detect (trained if data files exist, else sim)
"""
import asyncio
import json
import os
import sys
import time
import random
import argparse
import pickle

import pandas as pd
from websockets.asyncio.server import serve

# MQTT for live mode
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

import queue
MQTT_QUEUE = queue.Queue()  # Thread-safe queue: MQTT thread -> asyncio loop

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
IOMT_MODELS_DIR = os.path.join(BASE_DIR, "src", "core", "models")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "ars_events.json")
REAL_LOGS = os.path.join(
    os.path.dirname(BASE_DIR),  # Go up to final-research-project
    "..", "..",                  # Go up to Research
    "Heart_Rate_ESP32", "Python", "local_logs.jsonl"
)

# Normalize
REAL_LOGS = os.path.normpath(REAL_LOGS)

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# ---------------------------------------------------------------------------
# CONNECTED CLIENTS
# ---------------------------------------------------------------------------
CLIENTS = set()

# ---------------------------------------------------------------------------
# LOAD TRAINING DATA
# ---------------------------------------------------------------------------
VITALS_DATA = None     # ars_high_fidelity_training.csv
THREATS_DATA = None    # processed_threats.csv
REAL_IOMT_DATA = None  # local_logs.jsonl

# ARS Models
ARS_RESPONSE_MODEL = None


def load_training_data():
    """Load CSV training datasets from data/ folder."""
    global VITALS_DATA, THREATS_DATA

    vitals_path = os.path.join(DATA_DIR, "ars_high_fidelity_training.csv")
    threats_path = os.path.join(DATA_DIR, "processed_threats.csv")

    if os.path.exists(vitals_path):
        VITALS_DATA = pd.read_csv(vitals_path)
        print(f"[OK] Loaded vitals training data: {len(VITALS_DATA)} records")
    else:
        print(f"[!!] Vitals data not found: {vitals_path}")

    if os.path.exists(threats_path):
        THREATS_DATA = pd.read_csv(threats_path)
        print(f"[OK] Loaded threats training data: {len(THREATS_DATA)} records")
    else:
        print(f"[!!] Threats data not found: {threats_path}")


def load_real_iomt_logs():
    """Load real ESP32 device logs from local_logs.jsonl."""
    global REAL_IOMT_DATA
    if os.path.exists(REAL_LOGS):
        logs = []
        with open(REAL_LOGS, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        REAL_IOMT_DATA = logs
        print(f"[OK] Loaded real IoMT logs: {len(REAL_IOMT_DATA)} records from {REAL_LOGS}")
    else:
        print(f"[!!] Real IoMT logs not found: {REAL_LOGS}")


def load_models():
    """Load ARS Response Model v2 (the only model used)."""
    global ARS_RESPONSE_MODEL

    # ARS Response Model v2 (retrained with correlated data)
    v2_path = os.path.join(MODELS_DIR, "ars_response_model_v2.pkl")
    resp_path = os.path.join(MODELS_DIR, "ars_response_model.pkl")
    model_path = v2_path if os.path.exists(v2_path) else resp_path

    if os.path.exists(model_path):
        ARS_RESPONSE_MODEL = pickle.load(open(model_path, "rb"))
        print(f"[OK] Loaded ARS Response Model v2 (accuracy: {ARS_RESPONSE_MODEL.get('accuracy', 0):.2%})")
    else:
        print(f"[!!] ARS Response Model not found")


# ---------------------------------------------------------------------------
# DATA GENERATORS
# ---------------------------------------------------------------------------
THREAT_MSGS = [
    "Ransomware signature detected in packet header",
    "Unusual outbound traffic to known botnet IP",
    "PHI Pattern match detected in network stream",
    "CPU usage spike (99%) from unknown process",
    "Port 22 SSH Brute Force attempt detected",
    "Data Exfiltration: Large file transfer (2GB)",
    "Unauthorized access attempt on medical device",
    "Anomalous heart-rate reading detected",
    "Network anomaly: unexpected protocol usage",
    "Suspicious firmware update attempt blocked",
]


def trained_vitals_record(idx):
    """Get a record from the trained vitals dataset."""
    row = VITALS_DATA.iloc[idx % len(VITALS_DATA)]
    return {
        "device_id": f"TRAINED-ESP32-{(idx % 5) + 1:03d}",
        "heart_rate_bpm_pulse": float(row.get("heart_rate", 0)),
        "ppg_raw_value": int(row.get("ppg_raw_value", 0)),
        "spo2": int(row.get("spo2", 98)),
        "temperature_celsius": round(36.0 + random.random() * 2.5, 1),
        "sys_bp": int(row.get("sys_bp", 120)),
        "network_latency": float(row.get("network_latency", 0)),
        "anomaly_score": float(row.get("anomaly_score", 0)),
        "criticality_tier": "HIGH" if float(row.get("anomaly_score", 0)) > 0.7 else "MEDIUM" if float(row.get("anomaly_score", 0)) > 0.4 else "LOW",
        "timestamp": time.time(),
        "data_source": "MODEL_TRAINED",
    }


def trained_threat_record(idx):
    """Get a record from the trained threats dataset and produce a response event."""
    row = THREATS_DATA.iloc[idx % len(THREATS_DATA)]
    threat_type = str(row.get("threat_type", "Unknown"))
    severity = str(row.get("severity", "Medium"))
    confidence = float(row.get("confidence_score", row.get("confidence_scaled", 0.5)))

    # Map severity to action
    if severity in ("Critical", "critical"):
        action = "PERMANENT QUARANTINE"
        event_sev = "CRITICAL"
    elif severity in ("High", "high"):
        action = "TEMPORARY ISOLATION"
        event_sev = "HIGH"
    elif severity in ("Medium", "medium"):
        action = "MONITORING"
        event_sev = "MEDIUM"
    else:
        action = "NO_ACTION"
        event_sev = "LOW"

    return {
        "severity": event_sev,
        "action_taken": action,
        "threat_type": threat_type,
        "confidence": round(confidence, 2),
        "src_ip": f"192.168.1.{random.randint(2, 254)}",
        "message": f"{threat_type}: {random.choice(THREAT_MSGS)}",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": "MODEL_TRAINED",
    }


def real_iomt_record(idx):
    """Get a record from real IoMT device logs."""
    log = REAL_IOMT_DATA[idx % len(REAL_IOMT_DATA)].copy()
    log["data_source"] = "REAL_IOMT"
    log["timestamp"] = time.time()
    return log


def sim_vitals_record():
    """Generate a random simulated telemetry record."""
    hr = random.uniform(55, 120)
    ppg = random.randint(500, 4095)
    return {
        "device_id": f"SIM-ESP32-{random.choice(['A1','A2','B1','B2','C1'])}",
        "heart_rate_bpm_pulse": round(hr, 1),
        "ppg_raw_value": ppg,
        "spo2": random.randint(92, 100),
        "temperature_celsius": round(random.uniform(36.0, 38.5), 1),
        "criticality_tier": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
        "timestamp": time.time(),
        "data_source": "SIMULATED",
    }


def sim_threat_record():
    """Generate a random simulated threat event."""
    sev = random.choices(["CRITICAL", "HIGH", "MEDIUM", "LOW"], weights=[5, 15, 40, 40])[0]
    action = ("PERMANENT QUARANTINE" if sev == "CRITICAL" else
              "TEMPORARY ISOLATION" if sev == "HIGH" else "MONITORING")
    return {
        "severity": sev,
        "action_taken": action,
        "src_ip": f"192.168.1.{random.randint(2, 254)}",
        "message": random.choice(THREAT_MSGS),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": "SIMULATED",
    }


# ---------------------------------------------------------------------------
# LOG WRITER (for Flask API compatibility)
# ---------------------------------------------------------------------------
def write_event_to_log(event):
    """Append event to ars_events.json for Flask API."""
    sev = event.get("severity", "LOW")
    mapped = {
        "timestamp": event["timestamp"],
        "event_type": "DANGER" if sev in ("CRITICAL", "HIGH") else "INFO",
        "original_type": "THREAT_DETECTED" if sev in ("CRITICAL", "HIGH") else "SYSTEM_HEALTH",
        "decision": ("QUARANTINE" if event.get("action_taken") == "PERMANENT QUARANTINE"
                     else "ISOLATE" if event.get("action_taken") == "TEMPORARY ISOLATION"
                     else "NO_ACTION"),
        "src_ip": event.get("src_ip", "0.0.0.0"),
        "anomaly_score": round(random.uniform(0.6, 1.0) if sev in ("CRITICAL", "HIGH") else random.uniform(0.0, 0.4), 2),
        "message": event.get("message", ""),
        "details": f"Source: {event.get('data_source', 'UNKNOWN')}",
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(mapped) + "\n")


# ---------------------------------------------------------------------------
# WEBSOCKET HANDLERS
# ---------------------------------------------------------------------------
async def broadcast(msg):
    """Send message to all connected clients."""
    global CLIENTS
    data = json.dumps(msg)
    dead = set()
    for ws in list(CLIENTS):
        try:
            await ws.send(data)
        except Exception:
            dead.add(ws)
    CLIENTS -= dead


async def send_history(ws, mode):
    """Send initial history burst when a client connects."""
    history = []

    if mode == "trained" and VITALS_DATA is not None:
        # Send last 40 trained records
        start = max(0, len(VITALS_DATA) - 40)
        for i in range(start, start + 40):
            history.append(trained_vitals_record(i))
    elif mode == "real" and REAL_IOMT_DATA:
        start = max(0, len(REAL_IOMT_DATA) - 40)
        for i in range(start, start + 40):
            history.append(real_iomt_record(i))
    else:
        for _ in range(40):
            history.append(sim_vitals_record())

    await ws.send(json.dumps({"type": "history", "data": history}))

    # Response history
    resp_history = []
    if mode == "trained" and THREATS_DATA is not None:
        start = max(0, len(THREATS_DATA) - 10)
        for i in range(start, start + 10):
            resp_history.append(trained_threat_record(i))
    else:
        for _ in range(10):
            resp_history.append(sim_threat_record())

    await ws.send(json.dumps({"type": "response_history", "data": resp_history}))


async def handler(websocket):
    """Handle WebSocket connection."""
    global CLIENTS
    CLIENTS.add(websocket)
    print(f"[+] Client connected ({len(CLIENTS)} total)")
    try:
        await send_history(websocket, ACTIVE_MODE)
        async for _ in websocket:
            pass
    except Exception:
        pass
    finally:
        CLIENTS.discard(websocket)
        print(f"[-] Client disconnected ({len(CLIENTS)} total)")


# ---------------------------------------------------------------------------
# DATA PUMP (main broadcast loop)
# ---------------------------------------------------------------------------
async def data_pump(mode):
    """Continuously stream data to all connected clients."""
    print(f"[*] Data pump running in [{mode.upper()}] mode - broadcasting every 1.5s")

    vitals_idx = 0
    threat_idx = 0
    counter = 0

    while True:
        # -- TELEMETRY (every tick) --
        if mode == "trained" and VITALS_DATA is not None:
            telem = trained_vitals_record(vitals_idx)
            vitals_idx += 1
            # Loop back to start when we reach the end
            if vitals_idx >= len(VITALS_DATA):
                vitals_idx = 0
                print("[*] Vitals dataset looped - restarting from beginning")
        elif mode == "real" and REAL_IOMT_DATA:
            telem = real_iomt_record(vitals_idx)
            vitals_idx += 1
            if vitals_idx >= len(REAL_IOMT_DATA):
                vitals_idx = 0
                print("[*] Real IoMT logs looped - restarting from beginning")
        else:
            telem = sim_vitals_record()

        await broadcast({"type": "new_log", "data": telem})

        # -- SECURITY EVENTS (every 5 ticks) --
        counter += 1
        if counter % 5 == 0:
            if mode == "trained" and THREATS_DATA is not None:
                evt = trained_threat_record(threat_idx)
                threat_idx += 1
                if threat_idx >= len(THREATS_DATA):
                    threat_idx = 0
            else:
                evt = sim_threat_record()

            write_event_to_log(evt)
            await broadcast({"type": "new_response", "data": evt})

        await asyncio.sleep(1.5)


async def live_data_pump():
    """Stream LIVE MQTT data to dashboard as it arrives from real devices."""
    print("[*] LIVE data pump running - broadcasting real device data as it arrives")
    counter = 0

    while True:
        # Check the MQTT queue for new device data
        messages_this_tick = []
        while not MQTT_QUEUE.empty():
            try:
                messages_this_tick.append(MQTT_QUEUE.get_nowait())
            except queue.Empty:
                break

        for log_data in messages_this_tick:
            log_data["data_source"] = "LIVE_IOMT"
            log_data["timestamp"] = time.time()
            await broadcast({"type": "new_log", "data": log_data})

            # Generate security event based on vitals thresholds
            hr = log_data.get("heart_rate_bpm_pulse", 0)
            spo2 = log_data.get("spo2", 99)
            device = log_data.get("device_id", "UNKNOWN")

            counter += 1
            if counter % 8 == 0:  # Every 8th reading, generate security event
                if hr > 120 or hr < 50 or spo2 < 90:
                    sev = "CRITICAL"
                    action = "PERMANENT QUARANTINE"
                    msg = f"ANOMALOUS VITALS from {device}: HR={hr}, SpO2={spo2}"
                elif hr > 100 or spo2 < 95:
                    sev = "HIGH"
                    action = "TEMPORARY ISOLATION"
                    msg = f"Elevated readings from {device}: HR={hr}, SpO2={spo2}"
                else:
                    sev = "LOW"
                    action = "MONITORING"
                    msg = f"Normal vitals from {device}: HR={hr}, SpO2={spo2}"

                evt = {
                    "severity": sev,
                    "action_taken": action,
                    "src_ip": f"192.168.1.{random.randint(2,254)}",
                    "message": msg,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "data_source": "LIVE_IOMT",
                }
                write_event_to_log(evt)
                await broadcast({"type": "new_response", "data": evt})

        # If no messages, send a heartbeat so chart stays alive
        if not messages_this_tick:
            pass  # Just wait

        await asyncio.sleep(0.5)  # Check queue every 500ms for low latency


# ---------------------------------------------------------------------------
# CORRELATED DATA PUMP (real device alert correlation)
# ---------------------------------------------------------------------------
CORRELATOR = None

async def correlated_data_pump():
    """Stream correlated real device data with attack classification.
    
    Populates ALL dashboard pages:
    - Dashboard: via write_event_to_log (stats counters)
    - Threat Monitor: via write_event_to_log (device IP states)
    - Monitoring: via WebSocket broadcast (live alerts)
    - Privacy Vault: via write_privacy_event (PHI events)
    - Incident Log: via write_event_to_log (full history)
    """
    global CORRELATOR
    from alert_correlator import AlertCorrelator
    CORRELATOR = AlertCorrelator()

    print("[*] CORRELATED data pump running - streaming real device alerts")
    counter = 0

    while True:
        # -- Telemetry from detection results (every tick ~1.5s) --
        detection = CORRELATOR.get_next_detection()
        if detection:
            await broadcast({"type": "new_log", "data": detection})

        counter += 1

        # -- Correlated alerts (every 3 ticks ~4.5s) --
        if counter % 3 == 0:
            alert = CORRELATOR.get_next_alert()
            if alert:
                CORRELATOR.write_event_to_log(alert)
                await broadcast({"type": "new_response", "data": alert})

        # -- Privacy / PHI events (every 5 ticks ~7.5s) --
        if counter % 5 == 0:
            phi_event = CORRELATOR.write_privacy_event()
            await broadcast({"type": "new_response", "data": phi_event})

        # -- Incident escalations (every 15 ticks ~22.5s) --
        if counter % 15 == 0:
            incident = CORRELATOR.get_next_incident()
            if incident:
                CORRELATOR.write_event_to_log(incident)
                await broadcast({"type": "new_response", "data": incident})

        await asyncio.sleep(1.5)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
ACTIVE_MODE = "sim"  # Global so handler can access it


async def main(mode):
    global ACTIVE_MODE
    ACTIVE_MODE = mode

    print("=" * 60)
    print("  MEDGUARD-X  |  WebSocket Data Server")
    print("=" * 60)

    # Load resources based on mode
    if mode in ("trained", "auto"):
        load_training_data()
        load_models()

    if mode in ("real", "auto"):
        load_real_iomt_logs()

    if mode == "live":
        if not MQTT_AVAILABLE:
            print("[!!] ERROR: paho-mqtt not installed. Run: pip install paho-mqtt")
            return
        # Start MQTT subscriber in background thread
        import threading

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("[OK] MQTT connected - subscribing to hospital/iomt/#")
                client.subscribe("hospital/iomt/#")
            else:
                print(f"[!!] MQTT connection failed (rc={rc})")

        def on_message(client, userdata, msg):
            try:
                payload = msg.payload.decode()
                if payload.startswith("{"):
                    log = json.loads(payload)
                    MQTT_QUEUE.put(log)
            except Exception:
                pass

        mqtt_client = mqtt.Client()
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        try:
            mqtt_client.connect("localhost", 1883, 60)
            mqtt_thread = threading.Thread(target=mqtt_client.loop_forever, daemon=True)
            mqtt_thread.start()
            print("[OK] MQTT subscriber started on localhost:1883")
        except Exception as e:
            print(f"[!!] MQTT connection failed: {e}")
            print("[!!] Make sure Mosquitto broker is running!")
            return

    # Auto-detect mode
    if mode == "auto":
        if VITALS_DATA is not None and THREATS_DATA is not None:
            ACTIVE_MODE = "trained"
            print("[*] Auto-detected: using MODEL TRAINED data")
        elif REAL_IOMT_DATA:
            ACTIVE_MODE = "real"
            print("[*] Auto-detected: using REAL IoMT data")
        else:
            ACTIVE_MODE = "sim"
            print("[*] Auto-detected: using SIMULATED data (no training data found)")
    else:
        ACTIVE_MODE = mode

    print(f"[*] Active mode: {ACTIVE_MODE.upper()}")
    print(f"[*] Listening on ws://localhost:8000/ws")
    print(f"[*] Log file: {LOG_FILE}")
    print("=" * 60)

    async with serve(handler, "localhost", 8000) as server:
        if ACTIVE_MODE == "live":
            await live_data_pump()
        elif ACTIVE_MODE == "correlated":
            await correlated_data_pump()
        else:
            await data_pump(ACTIVE_MODE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MedGuard-X WebSocket Server")
    parser.add_argument(
        "--mode",
        choices=["trained", "real", "sim", "live", "correlated", "auto"],
        default="auto",
        help="Data mode: trained, real, sim, live (MQTT), correlated (real device alerts), auto"
    )
    args = parser.parse_args()
    asyncio.run(main(args.mode))
