import time
import json
import random
import os
import sys

# Setup Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'ars_events.json')

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

print(f"🚀 ARS Traffic Simulator Started")
print(f"📂 Target Log: {LOG_FILE}")
print("⚡ Generating High-Fidelity Security Events... (Ctrl+C to stop)")

# Simulation Templates
EVENT_TYPES = ["THREAT_DETECTED", "PRIVACY_ALERT", "SYSTEM_HEALTH", "NETWORK_ANOMALY"]
DECISIONS = ["ISOLATE", "MONITOR", "QUARANTINE", "ROLLBACK", "NO_ACTION"]
THREAT_DETAILS = [
    "Ransomware signature detected in packet header",
    "Unusual outbound traffic to known botnet IP",
    "PHI Pattern match: 'Patient ID: P-882'",
    "Sudden spike in CPU usage (99%) from unknown process",
    "Port 22 SSH Brute Force attempt",
    "Data Exfiltration detected: Large file transfer (2GB)"
]

def generate_event():
    event_type = random.choice(EVENT_TYPES)
    
    # Logic for meaningful data
    if event_type == "THREAT_DETECTED":
        decision = random.choice(["ISOLATE", "QUARANTINE"])
        severity = "DANGER"
        score = random.uniform(0.8, 1.0)
    elif event_type == "PRIVACY_ALERT":
        decision = "MONITOR"
        severity = "WARNING"
        score = random.uniform(0.5, 0.8)
    else:
        decision = "NO_ACTION"
        severity = "INFO"
        score = random.uniform(0.0, 0.3)

    event = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event_type": severity, # Dashboard expects DANGER/INFO
        "original_type": event_type,
        "decision": decision,
        "src_ip": f"192.168.1.{random.randint(2, 254)}",
        "anomaly_score": round(score, 2),
        "message": random.choice(THREAT_DETAILS),
        "details": f"Simulated Event: {event_type}"
    }
    
    return event

def write_log(event):
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(event) + "\n")

# Main Loop
try:
    while True:
        evt = generate_event()
        write_log(evt)
        print(f"[GEN] {evt['timestamp']} | {evt['event_type']} | {evt['message'][:30]}...")
        
        # Burst mode or steady state
        time.sleep(random.uniform(0.5, 3.0))

except KeyboardInterrupt:
    print("\n🛑 Simulation Stopped.")
