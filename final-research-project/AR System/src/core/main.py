import os
import time
import logging
import warnings
warnings.filterwarnings("ignore") # Suppress sklearn/joblib warnings
import json
import random
from inference_engine import InferenceEngine
from modules.containment import IsolationManager
from modules.redaction import PHIRedactor
from modules.wazuh_connector import WazuhConnector
import queue

# Configure Tamper-Evident Logging
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
log_path = os.path.join(base_dir, 'logs', 'ars_audit.log')

logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)



# JSON Logger for Wazuh Ingestion
LOG_DIR = os.path.join(os.environ.get('ProgramData', 'C:\\ProgramData'), "AR_System")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
JSON_LOG_FILE = os.path.join(LOG_DIR, "ars_events.json")

# Dashboard Real-Time Feed
DASHBOARD_LOG = os.path.join(base_dir, 'logs', 'ars_events.json')

def log_to_wazuh_json(event_type, decision, ip, score, details):
    """
    Writes a structured JSON log that Wazuh agent can pick up natively.
    AND mirrors it to the Dashboard local log for visualization.
    """
    # 1. Wazuh Entry
    log_entry = {
        "app_name": "ARS_Defense_Core",
        "event_type": event_type, 
        "decision": decision,      
        "src_ip": ip,
        "anomaly_score": score,
        "details": details,
        "top_features": ["Heart_Rate", "SpO2"] if event_type == "THREAT_DETECTED" else ["None"]
    }
    
    # 2. Dashboard Entry (Enhanced for UI)
    dashboard_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event_type": "DANGER" if decision in ["ISOLATE", "QUARANTINE"] else "INFO", # Map for UI color
        "original_type": event_type,
        "decision": decision,
        "src_ip": ip,
        "anomaly_score": score,
        "message": details,
        "details": f"AI Decision: {decision}"
    }

    try:
        # Write to System Log (Wazuh)
        with open(JSON_LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        # Write to Dashboard Log
        with open(DASHBOARD_LOG, "a") as f:
            f.write(json.dumps(dashboard_entry) + "\n")
            
    except Exception as e:
        print(f"[ERROR] Could not write to log file: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="MedGuard-X AI Core")
    parser.add_argument('--mode', type=str, help="Operation Mode: 1 (Simulated), 2 (Wazuh), 3 (CSV Replay), 4 (Real-time MQTT)")
    args = parser.parse_args()

    print("[SYS_EVENT] STARTING AUTOMATED RESPONSE SYSTEM (ARS) - DEFENSE CORE")
    print("=========================================================")
    
    # 1. Initialize Components
    ai_brain = InferenceEngine()
    isolation_mgr = IsolationManager()
    phi_guard = PHIRedactor() # Uses Regex + AI Hybrid
    
    logging.info("ARS System Startup. Models loaded. Waiting for events...")
    
    mode = args.mode
    if not mode:
        # 2. Configure Event Source
        print("\n[CONFIG] Select Operation Mode:")
        print("   [1] Simulation Mode (Pre-defined scenarios)")
        print("   [2] Live Wazuh Integration (Real-time API)")
        print("   [3] Full Dataset Replay (High Fidelity CSV)")
        print("   [4] Real-Time MQTT Devices (Local Devices)")
        mode = input("Enter selection [1/2/3/4]: ").strip()

    event_stream = []
    mqtt_queue = queue.Queue()
    
    if mode == "4":
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            print("[ERROR] paho-mqtt is not installed. Please run: pip install paho-mqtt")
            return

        MQTT_BROKER = "127.0.0.1"
        MQTT_PORT = 1883
        MQTT_TOPIC = "hospital/iomt/#"

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print(f"[MQTT] Connected successfully to Mosquitto MQTT Broker ({MQTT_BROKER}:{MQTT_PORT})")
                client.subscribe(MQTT_TOPIC)
                print(f"[MQTT] Listening for real device data on topic: {MQTT_TOPIC}")
            else:
                print(f"[ERROR] Failed to connect to MQTT broker, return code {rc}")

        def on_message(client, userdata, msg):
            try:
                # Expecting JSON payload from devices
                payload = json.loads(msg.payload.decode('utf-8'))
                
                # Standardize incoming fields if missing
                event = {
                    "device_ip": payload.get('device_ip', payload.get('ip', f"Unknown-{msg.topic}")),
                    "heart_rate": payload.get('heart_rate', payload.get('hr', 75)),
                    "spo2": payload.get('spo2', 98),
                    "sys_bp": payload.get('sys_bp', payload.get('bp', 120)),
                    "network_latency": payload.get('network_latency', 20),
                    "packet_size": payload.get('packet_size', 500),
                    "anomaly_score": payload.get('anomaly_score', 0.0),
                    "log": payload.get('log', f"Data received from topic {msg.topic}"),
                }
                
                # Queue the event for the AI Core to process main thread safely
                mqtt_queue.put(event)
                
            except Exception as e:
                print(f"[MQTT ERROR] Invalid payload on {msg.topic}: {e} -> {msg.payload}")

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            client.loop_start()  # Start network loop in background thread
        except Exception as e:
            print(f"[ERROR] Could not start MQTT client: {e}")
            return
            
        # event_stream in Mode 4 will be dynamic from the mqtt_queue
        def mqtt_stream():
            while True:
                # Block until we get a real device payload
                event = mqtt_queue.get() 
                yield event
                
        event_stream = mqtt_stream()

    elif mode == "3":
        import csv
        # Path to data folder (up 2 levels from src/core)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(base_dir, 'data', 'ars_high_fidelity_training.csv')
        
        print(f"[INIT] Loading High Fidelity Dataset from: {csv_path}")
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Construct Log Message (Synthesized)
                    log_msg = f"Vitals Monitor: HR={row['heart_rate']} SPO2={row['spo2']} SYS_BP={row['sys_bp']}"
                    
                    # Randomly inject PHI for testing Privacy Module
                    if random.random() < 0.05: # 5% chance
                        log_msg += " | Patient ID: P-999 (Confidential)"

                    event = {
                        "device_ip": f"192.168.1.{random.randint(50, 200)}",
                        "heart_rate": int(row['heart_rate']),
                        "spo2": int(row['spo2']),
                        "sys_bp": int(row['sys_bp']),
                        "network_latency": int(row['network_latency']),
                        "packet_size": int(row['packet_size']),
                        "anomaly_score": float(row['anomaly_score']),
                        "log": log_msg,
                        "timestamp": time.time()  # Internal use only (removed before sending)
                    }
                    event_stream.append(event)
            print(f"[INIT] Successfully loaded {len(event_stream)} events for replay.")
            
        except Exception as e:
            print(f"[ERROR] Failed to load CSV: {e}")
            event_stream = []

    elif mode == "2":
        wazuh_ip = "20.239.185.152" # Default from project
        wazuh_user = input("Enter Wazuh Username [wazuh-wui]: ").strip() or "wazuh-wui"
        wazuh_pass = input("Enter Wazuh Password: ").strip()
        
        connector = WazuhConnector(wazuh_ip, wazuh_user, wazuh_pass)
        if connector.authenticate():
            print("[SYS_EVENT] Connected to Wazuh Manager. Listening for alerts...")
            def live_stream():
                # Hybrid Mode:
                # 1. We start by showing steady 'Heartbeats' from the Real Wazuh Agent.
                # 2. Key: We inject the 'Simulated Attack' events after a few seconds
                #    so the user can see the AR System react to a threat while connected.
                
                simulated_threats = [
                    # Event 1: Malware Attack (High Anomaly)
                    {"device_ip": "192.168.1.50", "heart_rate": 78, "spo2": 97, "anomaly_score": 0.95, "log": "Malware detected: Unauthorized process on port 22."},
                    # Event 2: Ransomware Attack (Critical)
                    {"device_ip": "192.168.1.99", "heart_rate": 120, "spo2": 85, "anomaly_score": 0.99, "log": "Ransomware active: File encryption started."},
                ]
                
                threat_index = 0
                tick = 0
                
                while True:
                    # A. Fetch Real-time Agent Status (Heartbeat)
                    events = connector.get_monitoring_data()
                    for event in events:
                        yield event
                    
                    # B. Inject Simulated Threat? (Every 3rd poll, roughly 15s)
                    tick += 1
                    if tick % 3 == 0:
                        print(f"\n[HYBRID_DEMO] Injecting Simulated High-Severity Threat...")
                        yield simulated_threats[threat_index]
                        threat_index = (threat_index + 1) % len(simulated_threats)
                        
                    time.sleep(5)
            event_stream = live_stream()
        else:
            print("[ERROR] Authentication failed. Falling back to Simulation.")
            mode = "1"

    else:
        # Simulation Mode (Default or Mode 1)
        event_stream = [
        # Event 1: Normal Heartbeat
        {"device_ip": "192.168.1.50", "heart_rate": 75, "spo2": 98, "anomaly_score": 0.1, "log": "Patient P-123 stable."},
        # Event 2: Malware Attack Detected (High Anomaly)
        {"device_ip": "192.168.1.50", "heart_rate": 78, "spo2": 97, "anomaly_score": 0.95, "log": "Patient ID P-123. Unauthorized process detected on port 22."},
        # Event 3: Attack Cleared (False Positive Rollback Test)
        {"device_ip": "192.168.1.50", "heart_rate": 76, "spo2": 98, "anomaly_score": 0.05, "log": "System scan complete. No threats."},
        
        # --- NEW TEST: PERMANENT QUARANTINE ---
        # Event 4: Another Device with High Threat
        {"device_ip": "192.168.1.99", "heart_rate": 120, "spo2": 85, "anomaly_score": 0.99, "log": "Ransomware detected."},
        # Event 5: Threat Persists (Should Trigger Quarantine)
        {"device_ip": "192.168.1.99", "heart_rate": 122, "spo2": 84, "anomaly_score": 0.99, "log": "Encryption process active."},
        # Event 6: Ignored Data (Should be skipped)
        {"device_ip": "192.168.1.99", "heart_rate": 0, "spo2": 0, "anomaly_score": 0.0, "log": "Trying to reconnect..."},
        
        # --- USER VALIDATION TEST ---
        {"device_ip": "10.0.0.5", "heart_rate": 60, "spo2": 99, "anomaly_score": 0.0, "log": "TEST: Patient John Doe (ID P-999) transfer request."}
    ]
    
    
    
    # Track states
    isolated_devices = {}
    quarantined_devices = set()   # Permanent Quarantine

    # 3. Processing Loop
    for event in event_stream:
        device_ip = event['device_ip']
        anomaly_score = event['anomaly_score']
        
        # Skip processing if device is already in Permanent Quarantine
        if device_ip in quarantined_devices:
            print(f"\n[SYS_EVENT] IGNORED DATA from {device_ip}: Device is in PERMANENT QUARANTINE.")
            continue

        print(f"\n[INGEST] RECEIVED DATA: IP={device_ip} | Score={event['anomaly_score']}")
        
        # Speed up simulation for CSV Replay (Mode 3)
        if mode == "3":
            time.sleep(0.1) # Fast replay
        elif mode != "4":
            time.sleep(1)   # Normal demo speed for modes 1 and 2
        # In mode 4, we don't artificially sleep because we wait on the queue.get()
        
        # A. PRIVACY CHECK (PHI Redaction)
        if 'log' in event and phi_guard.has_regex_phi(event['log']):
            print(f"   [DLP] PRIVACY ALERT: Protected Health Information (PHI) detected in logs.")
            redacted_text = phi_guard.redact_log(event['log'])
            print(f"      REDACTED LOG: {redacted_text}")
            logging.info(f"Redacted log for {device_ip}: {redacted_text}")
            # SEND TO DASHBOARD (Privacy Vault)
            log_to_wazuh_json("PRIVACY_ALERT", "REDACTED", device_ip, 0.0, f"PHI Detected & Redacted: {redacted_text}")
            
        # B. THREAT RESPONSE (Defense Core)
        action = ai_brain.predict_action(event)
        print(f"   [THREAT_INTEL] AI DECISION: {action}")
        
        # 1. IMMEDIATE QUARANTINE (Attack Confirmed by AI)
        if action == "QUARANTINE":
            if device_ip not in quarantined_devices:
                print(f"   [CRITICAL] AI CONFIRMED ATTACK! Initiating Protocol...")
                print(f"      1. ISOLATING Device {device_ip}...")
                isolation_mgr.isolate_device(device_ip)
                
                print(f"      2. PERMANENT QUARANTINE Applied.")
                quarantined_devices.add(device_ip)
                logging.critical(f"DEVICE {device_ip} QUARANTINED (AI PREDICTION).")
                log_to_wazuh_json("THREAT_DETECTED", "QUARANTINE", device_ip, anomaly_score, "High fidelity threat confirmed. Immediate Quarantine.")

        # 2. ISOLATE / SUSPICIOUS (High Risk Score but AI unsure or explicit ISOLATE)
        elif action == "ISOLATE" or (action == "MONITOR" and anomaly_score > 0.8):
             if device_ip not in isolated_devices and device_ip not in quarantined_devices:
                print(f"   [RESPONSE] EXECUTING CONTAINMENT (Temporary Isolation)...")
                isolation_mgr.isolate_device(device_ip)
                isolated_devices[device_ip] = time.time()
                logging.warning(f"ISOLATION TRIGGERED for {device_ip}")
                log_to_wazuh_json("THREAT_RESPONSE", "ISOLATE", device_ip, anomaly_score, "High Anomaly Score. Investigating.")

        # 3. ROLLBACK (False Positive Cleanup)
        elif action == "ROLLBACK":
            if device_ip in isolated_devices:
                print(f"   [RESOLVED] AI Identified FALSE POSITIVE. Rolling back...")
                success = isolation_mgr.rollback(device_ip)
                if success:
                    del isolated_devices[device_ip]
                    print(f"   [AUDIT_PASS] Device {device_ip} restored to network.")
                    logging.info(f"ROLLBACK EXECUTED for {device_ip}")
                    log_to_wazuh_json("FALSE_POSITIVE", "ROLLBACK", device_ip, anomaly_score, "AI cleared threat. Connection restored.")
            else:
                 print("   [INFO] AI indicates Safe/Rollback state (No action needed).")

        # 4. MONITOR / SAFE
        else:
            if device_ip in isolated_devices:
                # Timer based release for manually isolated devices
                if time.time() - isolated_devices[device_ip] > 30:
                     print(f"   [TIMER] Isolation expired. Releasing device...")
                     isolation_mgr.rollback(device_ip)
                     del isolated_devices[device_ip]
            else:
                print(f"   [OK] Monitoring Active. System Stable.")

if __name__ == "__main__":
    main()
