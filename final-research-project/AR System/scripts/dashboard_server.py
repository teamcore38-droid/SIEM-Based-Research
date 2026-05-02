from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
import json
import time
import random
import sys
import functools
import jwt
import datetime

# 1. Initialize App
app = Flask(__name__)
CORS(app)

# 2. Setup Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'ars_events.json')
sys.path.append(os.path.join(BASE_DIR, 'src'))

# 3. Import Reporting Module
try:
    from core.modules.reporting import ReportGenerator
except ImportError:
    ReportGenerator = None
    print("Warning: Reporting module missing dependencies (pandas/matplotlib). PDF generation disabled.")

# 4. Routes
@app.route('/api/report', methods=['GET'])
def generate_report():
    """Generates and serves the PDF report."""
    if not ReportGenerator:
        return jsonify({"error": "Reporting dependencies missing (pip install pandas fpdf matplotlib seaborn)"}), 500
        
    try:
        reporter = ReportGenerator(log_file=LOG_FILE)
        pdf_path = reporter.generate_daily_report()
        # Serve the generated file
        return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Secret Key for JWT
app.config['SECRET_KEY'] = 'medguard_secret_key_123'

def token_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1] # Bearer <token>
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(*args, **kwargs)
    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    """Simple Admin Authentication."""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Hardcoded credentials for prototype
    if username == "admin" and password == "medguard123":
        token = jwt.encode({
            'user': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            "status": "success", 
            "token": token,
            "role": "admin"
        })
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/devices/add', methods=['POST'])
@token_required
def add_device():
    """Manually add a new device to inventory."""
    data = request.json
    new_device = {
        "id": data.get('id', f"D-{random.randint(200,999)}"),
        "ip": data.get('ip'),
        "type": data.get('type', "Manual Entry"),
        "location": data.get('location', "General Ward"),
        "status": "SAFE",
        "last_seen": "Just Now",
        "risk_score": 0
    }
    
    global DEVICES
    # check duplicates
    if not any(d['ip'] == new_device['ip'] for d in DEVICES):
        DEVICES.append(new_device)
        save_inventory() # Save changes
        return jsonify({"status": "success", "device": new_device})
    return jsonify({"error": "Device already exists"}), 400

@app.route('/api/devices/remove', methods=['POST'])
@token_required
def remove_device():
    """Remove a device from inventory."""
    data = request.json
    ip_to_remove = data.get('ip')
    
    global DEVICES
    DEVICES = [d for d in DEVICES if d['ip'] != ip_to_remove]
    save_inventory() # Save changes
    return jsonify({"status": "success", "message": "Device removed"})

@app.route('/api/privacy', methods=['GET'])
def get_privacy_logs():
    """Returns only Privacy/PHI related events."""
    events = read_logs()
    # Filter for PRIVACY_ALERT (Check original_type if event_type was remapped to INFO)
    privacy_events = [
        e for e in events 
        if e.get('event_type') == 'PRIVACY_ALERT' or e.get('original_type') == 'PRIVACY_ALERT'
    ]
    return jsonify(privacy_events)

@app.route('/api/history', methods=['GET'])
def get_history():
    """Returns full event history for the Incident Log."""
    return jsonify(read_logs())

def read_logs():
    """Reads the JSON log file safely."""
    if not os.path.exists(LOG_FILE):
        return []
    
    events = []
    try:
        with open(LOG_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        print(f"Error reading logs: {e}")
    return events

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Returns aggregated stats including specific Response Flow counts."""
    events = read_logs()
    
    total_events = len(events)
    # Filter by Decision Types
    quarantined = set()
    rollbacks = set()
    temporary_isolation = set()
    
    for e in events:
        decision = e.get('decision', 'NO_ACTION')
        ip = e.get('src_ip')
        
        if decision == "QUARANTINE":
            quarantined.add(ip)
            if ip in temporary_isolation:
                 temporary_isolation.remove(ip) # Moved to permanent
        elif decision == "ROLLBACK":
            rollbacks.add(ip)
            if ip in temporary_isolation:
                 temporary_isolation.remove(ip) # Restored
            if ip in quarantined:
                 quarantined.remove(ip) # Restored from quarantine (rare but possible manual override logic)
        elif decision == "ISOLATE":
             # Only count as temp if not fully quarantined yet
             if ip not in quarantined and ip not in rollbacks:
                 temporary_isolation.add(ip)

    # Calculate active threats (current danger)
    active_threats = len(quarantined) + len(temporary_isolation)
    
    # Calculate simple uptime
    uptime = "99.9%" if total_events > 0 else "100%"

    return jsonify({
        "total_events": total_events,
        "active_threats": active_threats,
        "system_health": "98%" if active_threats < 2 else "85%",
        "uptime": uptime,
        "recent_alerts": [e for e in events if e.get('event_type') == 'DANGER'][-50:],
        # Specific Counters for User Requirement:
        "metrics": {
            "temp_isolate": len(temporary_isolation),
            "quarantined": len(quarantined),
            "rollbacks": len(rollbacks),
            "phi_attempts": len([e for e in events if e.get('event_type') == 'PRIVACY_ALERT'])
        }
    })

# Persistence File
INVENTORY_FILE = os.path.join(BASE_DIR, 'logs', 'inventory.json')

def load_inventory():
    """Loads device inventory from JSON file."""
    if not os.path.exists(INVENTORY_FILE):
        return [
            {"id": "PULSE_ESP32_001", "ip": "10.86.251.45", "type": "Pulse/PPG Sensor", "location": "ICU", "last_seen": "Active"},
            {"id": "ECG_ESP32_001", "ip": "10.38.16.20", "type": "ECG Monitor", "location": "ICU", "last_seen": "Active"},
            {"id": "TEMP_ESP32_001", "ip": "10.18.166.210", "type": "Temperature Sensor", "location": "General_Ward", "last_seen": "Active"},
            {"id": "MOTION_ESP32_001", "ip": "10.98.160.21", "type": "Motion/IMU Sensor", "location": "Ward_01", "last_seen": "Active"},
        ]
    try:
        with open(INVENTORY_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading inventory: {e}")
        return []

def save_inventory():
    """Saves current global DEVICES to JSON file."""
    try:
        with open(INVENTORY_FILE, 'w') as f:
            json.dump(DEVICES, f, indent=4)
    except Exception as e:
        print(f"Error saving inventory: {e}")

# Global Device Inventory
DEVICES = load_inventory()

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Returns the list of active devices with status synced from AI logs."""
    logs = read_logs()
    
    # Scan logs to determine current state of each IP
    device_states = {}
    for log in logs:
        ip = log.get('src_ip')
        decision = log.get('decision')
        
        # Simple state machine based on log history order
        if decision == "QUARANTINE":
            device_states[ip] = "QUARANTINED"
        elif decision == "ROLLBACK":
            device_states[ip] = "SAFE"
        elif decision == "ISOLATE":
             # If not already quarantined, mark as isolating
             if device_states.get(ip) != "QUARANTINED":
                 device_states[ip] = "ISOLATING"

    # Apply to inventory
    response_devices = []
    
    for d in DEVICES:
        dev = d.copy() 
        ip = dev['ip']
        
        # Sync status from AI logs
        if ip in device_states:
            status = device_states[ip]
            dev['status'] = status
            
            if status == "QUARANTINED":
                dev['risk_score'] = 100
            elif status == "ISOLATING":
                dev['risk_score'] = 80
            elif status == "SAFE":
                dev['risk_score'] = 0
        else:
            # Default state if no AI events
            if 'status' not in dev: # Preserve manual isolate/release status if no AI event overrides it?
                dev['status'] = "SAFE"
                dev['risk_score'] = 0
            
        response_devices.append(dev)

    return jsonify(response_devices)

@app.route('/api/isolate', methods=['POST'])
@token_required
def isolate_device():
    """Handles manual isolation/release commands."""
    from flask import request
    data = request.json
    device_id = data.get('device_id')
    action = data.get('action') # 'ISOLATE' or 'RELEASE'
    
    print(f"⚠️ COMMAND RECEIVED: {action} DEVICE {device_id}")
    
    # Update global mock state
    global DEVICES
    for d in DEVICES:
        if d['id'] == device_id:
            d['status'] = 'ISOLATED' if action == 'ISOLATE' else 'SAFE'
            break
            
    # Save state changes (optional, if we want manual isolation to persist)
    save_inventory()
            
    return jsonify({"status": "success", "message": f"Device {action}D"})

@app.route('/api/traffic', methods=['GET'])
def get_traffic():
    """Returns real-time traffic data AND IoMT Model Prediction."""
    
    # 1. Base Traffic Stats
    events = read_logs()
    latest_severity = 0.5
    if events:
         last = events[-1]
         if last.get('event_type') == 'DANGER':
             latest_severity = 0.95
    
    cpu_load = 10 + (random.random() * 40 * latest_severity) + (40 if latest_severity > 0.8 else 0)
    packets = 2000 + (random.random() * 3000 * latest_severity)

    # 2. IoMT Model Inference (Automated)
    iomt_result = {"priority": "MONITORING", "confidence": 0}
    
    if IOMT_MODEL and IOMT_FEATURES is not None:
        try:
            # Simulate features based on current load
            # High load = High Packet Rate = Likely Attack
            sim_packet_rate = packets / 60.0
            sim_attack_sev = 40 if latest_severity > 0.8 else 0
            
            # Construct feature vector (Must match model expectations)
            # Defaulting to 'ESP32_Pulse_Oximeter' generally
            features = {
                'criticality_tier': 8.0, # Contain critical devices
                'life_support': 0,
                'device_type_encoded': 0, # Pulse Oximeter
                'ward_encoded': 0, # ICU
                'protocol_encoded': 0, # MQTT
                'packet_size': 512.0,
                'packet_rate': sim_packet_rate, # Dynamic
                'packets_per_sec': sim_packet_rate / 60.0,
                'unique_ports': 10 if latest_severity > 0.8 else 1,
                'failed_connections': 20 if latest_severity > 0.8 else 0,
                'bytes_sent': 512.0 * sim_packet_rate,
                'bytes_received': 512.0 * sim_packet_rate * 0.5,
                'flow_duration': 30.0,
                'hour_of_day': int(time.strftime("%H")),
                'day_of_week': 0, 
                'is_night': 0,
                'is_weekend': 0,
                'attack_type_encoded': 2 if latest_severity > 0.8 else 0, # 2=DDoS, 0=Normal (approx)
                'attack_severity': sim_attack_sev, # Dynamic
                'network_anomaly_score': latest_severity,
                'behavioral_anomaly_score': latest_severity,
                'time_anomaly_score': 0.0
            }
            
            X = pd.DataFrame([features])[IOMT_FEATURES]
            p_res = IOMT_MODEL.predict(X)[0]
            c_res = max(IOMT_MODEL.predict_proba(X)[0]) * 100
            
            iomt_result = {
                "priority": str(p_res),
                "confidence": round(float(c_res), 1),
                "timestamp": time.strftime("%H:%M:%S")
            }
            
            # Append to history
            IOMT_ALERTS.append(iomt_result)
            if len(IOMT_ALERTS) > 500: # Keep limit
                IOMT_ALERTS.pop(0)

        except Exception as e:
            print(f"Prediction Error: {e}")

    return jsonify({
        "time": time.strftime("%H:%M:%S"),
        "cpu_load": cpu_load,
        "packets": packets,
        "iomt": iomt_result
    })

# -------------------------------------------------------------------------
# ARS RESPONSE MODEL (v2 - Retrained with Correlated Data, 93.7% accuracy)
# -------------------------------------------------------------------------
import pickle
import pandas as pd
import numpy as np

# Load the ONLY model: ars_response_model_v2.pkl
ARS_MODEL = None
ARS_LABEL_ENCODERS = None
ARS_TARGET_ENCODER = None
ARS_FEATURE_COLS = None
ARS_MODEL_ACCURACY = 0

try:
    model_path = os.path.join(BASE_DIR, 'models', 'ars_response_model_v2.pkl')
    if not os.path.exists(model_path):
        model_path = os.path.join(BASE_DIR, 'models', 'ars_response_model.pkl')
    with open(model_path, 'rb') as f:
        pkg = pickle.load(f)
    ARS_MODEL = pkg['model']
    ARS_LABEL_ENCODERS = pkg['label_encoders']
    ARS_TARGET_ENCODER = pkg['target_encoder']
    ARS_FEATURE_COLS = pkg['feature_cols']
    ARS_MODEL_ACCURACY = pkg.get('accuracy', 0)
    print(f"✅ ARS Response Model v2 loaded: {pkg.get('model_name', '?')} "
          f"(accuracy: {ARS_MODEL_ACCURACY:.2%}, actions: {pkg.get('action_classes', [])})")
except Exception as e:
    print(f"⚠️ ARS Model load failed: {e}")

# Store history of alerts for the Monitoring Tab
IOMT_ALERTS = []

@app.route('/api/iomt/analyze', methods=['POST'])
@token_required
def analyze_iomt():
    """Uses the v2 ARS Response Model to predict automated response action."""
    if not ARS_MODEL:
        return jsonify({"error": "ARS Model not loaded"}), 503

    try:
        data = request.json
        le = ARS_LABEL_ENCODERS

        classification = data.get('classification', 'BENIGN')
        priority = data.get('priority_label', 'LOW')
        data_src = data.get('data_source', 'detection_results')
        ai_pred = data.get('ai_prediction', 'BENIGN')
        atk_type = data.get('attack_type', 'normal')
        is_atk = int(data.get('is_attack', 0))
        anom = int(data.get('anomaly_flag', 0))

        features = {
            'classification_enc': int(le['classification'].transform([str(classification)])[0]),
            'priority_label_enc': int(le['priority_label'].transform([str(priority)])[0]),
            'data_source_enc': int(le['data_source'].transform([str(data_src)])[0]),
            'ai_prediction_enc': int(le['ai_prediction'].transform([str(ai_pred)])[0]),
            'attack_type_enc': int(le['attack_type'].transform([str(atk_type)])[0]),
            'is_attack': is_atk,
            'anomaly_flag': anom,
        }
        X = np.array([[features[c] for c in ARS_FEATURE_COLS]])
        pred_enc = ARS_MODEL.predict(X)[0]
        action = ARS_TARGET_ENCODER.inverse_transform([pred_enc])[0]
        proba = ARS_MODEL.predict_proba(X)[0]
        confidence = round(float(max(proba)) * 100, 1)

        return jsonify({
            "action": action,
            "confidence": confidence,
            "model_accuracy": round(ARS_MODEL_ACCURACY * 100, 1),
            "features_processed": features
        })
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/iomt/alerts', methods=['GET'])
def get_iomt_alerts():
    """Returns the history of IoMT alerts."""
    return jsonify(IOMT_ALERTS[-100:]) # Return last 100 alerts



if __name__ == '__main__':
    import threading

    def background_data_pump():
        """Background thread that generates AI-predicted alerts using ARS v2 model."""
        import time as t
        global IOMT_ALERTS
        counter = 0

        # Real device IPs for realistic data
        DEVICE_MAP = {
            'PULSE_ESP32_001': '10.86.251.45',
            'ECG_ESP32_001': '10.38.16.20',
            'TEMP_ESP32_001': '10.18.166.210',
            'MOTION_ESP32_001': '10.98.160.21',
        }
        device_list = list(DEVICE_MAP.keys())

        # Classification scenarios for realistic variation
        scenarios = [
            ('ATTACK', 'HIGH', 'ATTACK', 'ddos', 1, 1),
            ('ATTACK', 'CRITICAL', 'ATTACK', 'flooding', 1, 1),
            ('ANOMALY', 'MEDIUM', 'BENIGN', 'normal', -1, 1),
            ('BENIGN', 'LOW', 'BENIGN', 'normal', 0, 0),
            ('BENIGN', 'LOW', 'BENIGN', 'normal', 0, 0),
            ('ANOMALY', 'MEDIUM', 'BENIGN', 'protocol_anomaly', -1, 1),
            ('ATTACK', 'HIGH', 'ATTACK', 'ip_spoofing', 1, 1),
            ('BENIGN', 'LOW', 'BENIGN', 'normal', 0, 0),
        ]

        print("[BG] Background data pump started - ARS v2 model predictions")

        while True:
            try:
                # --- ARS v2 Model Predictions (for Monitoring System page) ---
                if ARS_MODEL and ARS_LABEL_ENCODERS:
                    scenario = scenarios[counter % len(scenarios)]
                    classification, priority, ai_pred, atk_type, is_atk, anom = scenario
                    device = device_list[counter % len(device_list)]

                    try:
                        le = ARS_LABEL_ENCODERS
                        features = {
                            'classification_enc': int(le['classification'].transform([classification])[0]),
                            'priority_label_enc': int(le['priority_label'].transform([priority])[0]),
                            'data_source_enc': int(le['data_source'].transform(['detection_results'])[0]),
                            'ai_prediction_enc': int(le['ai_prediction'].transform([ai_pred])[0]),
                            'attack_type_enc': int(le['attack_type'].transform([atk_type])[0]),
                            'is_attack': is_atk,
                            'anomaly_flag': anom,
                        }
                        X = np.array([[features[c] for c in ARS_FEATURE_COLS]])
                        pred_enc = ARS_MODEL.predict(X)[0]
                        action = ARS_TARGET_ENCODER.inverse_transform([pred_enc])[0]
                        proba = ARS_MODEL.predict_proba(X)[0]
                        confidence = round(float(max(proba)) * 100, 1)
                    except Exception:
                        action = 'MONITORING'
                        confidence = 75.0

                    alert = {
                        "action": action,
                        "priority": priority,
                        "confidence": confidence,
                        "device_id": device,
                        "device_ip": DEVICE_MAP[device],
                        "classification": classification,
                        "model_accuracy": round(ARS_MODEL_ACCURACY * 100, 1),
                        "timestamp": t.strftime("%H:%M:%S")
                    }
                    IOMT_ALERTS.append(alert)
                    if len(IOMT_ALERTS) > 500:
                        IOMT_ALERTS.pop(0)

                # --- Privacy / PHI Events (for Privacy Vault page) ---
                counter += 1
                if counter % 3 == 0:
                    phi_patterns = [
                        "SSN: ***-**-1234",
                        "Patient Name: [REDACTED]",
                        "DOB: [REDACTED] -> ****-**-**",
                        "MRN#: [REDACTED]",
                        "Insurance ID: [REDACTED]",
                        "Blood Type: [REDACTED]",
                        "Diagnosis: [REDACTED]",
                        "Prescription: [REDACTED]",
                    ]
                    dev = random.choice(device_list)
                    phi_event = {
                        "timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
                        "event_type": "PRIVACY_ALERT",
                        "original_type": "PRIVACY_ALERT",
                        "decision": "REDACT",
                        "src_ip": DEVICE_MAP[dev],
                        "anomaly_score": round(random.uniform(0.6, 1.0), 2),
                        "message": f"PHI Detected & Redacted on {dev}: {random.choice(phi_patterns)}",
                        "details": "Auto-redaction by AI Privacy Engine"
                    }
                    with open(LOG_FILE, 'a') as f:
                        f.write(json.dumps(phi_event) + '\n')

            except Exception as e:
                print(f"[BG] Error: {e}")

            t.sleep(3)

    # Start background thread
    bg_thread = threading.Thread(target=background_data_pump, daemon=True)
    bg_thread.start()

    print(f"ARS Dashboard Server running on http://localhost:5000")
    print(f"Watching logs at: {LOG_FILE}")
    app.run(port=5000, debug=True, use_reloader=False)
