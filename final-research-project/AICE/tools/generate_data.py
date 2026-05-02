import json
import random
from datetime import datetime, timedelta

def generate_alerts(output_file="data/alerts.json"):
    alerts = []
    base_time = datetime.now() - timedelta(hours=1)

    devices = [
        {"id": "ICU-VENT-014", "type": "ventilator"},
        {"id": "ICU-VENT-015", "type": "ventilator"},
        {"id": "MRI-SCAN-001", "type": "mri_scanner"},
        {"id": "ADMIN-PC-102", "type": "admin_pc"},
        {"id": "GW-001", "type": "gateway"}
    ]

    # SCENARIO 1: Critical Ventilator Attack (High Severity)
    # Series of high confidence alerts in a short window
    print("Generating Scenario 1: Critical Ventilator Attack...")
    target_vent = devices[0]
    start_time = base_time + timedelta(minutes=10)
    for i in range(6):
        alerts.append({
            "device_id": target_vent["id"],
            "device_type": target_vent["type"],
            "prediction": "Ransomware_Activity" if i > 3 else "Anomaly",
            "confidence_score": round(random.uniform(0.85, 0.99), 2),
            "timestamp": (start_time + timedelta(seconds=i*30)).isoformat()
        })

    # SCENARIO 2: Gateway Scanning (High/Medium Severity)
    print("Generating Scenario 2: Gateway Network Scan...")
    target_gw = devices[4]
    start_time_gw = base_time + timedelta(minutes=25)
    for i in range(15): # Noisy
        alerts.append({
            "device_id": target_gw["id"],
            "device_type": target_gw["type"],
            "prediction": "Network_Scan",
            "confidence_score": round(random.uniform(0.6, 0.8), 2),
            "timestamp": (start_time_gw + timedelta(seconds=i*10)).isoformat()
        })

    # SCENARIO 3: Isolated Low Confidence Noise (Should be Low Severity or ignored)
    print("Generating Scenario 3: Random Noise...")
    for _ in range(5):
        dev = random.choice(devices)
        rand_time = base_time + timedelta(minutes=random.randint(0, 50))
        alerts.append({
            "device_id": dev["id"],
            "device_type": dev["type"],
            "prediction": "Unknown_Traffic",
            "confidence_score": round(random.uniform(0.2, 0.45), 2),
            "timestamp": rand_time.isoformat()
        })

    # SCENARIO 4: Admin PC Anomaly (Medium Severity)
    print("Generating Scenario 4: Admin PC Anomalies...")
    target_pc = devices[3]
    start_time_pc = base_time + timedelta(minutes=40)
    for i in range(3):
        alerts.append({
            "device_id": target_pc["id"],
            "device_type": target_pc["type"],
            "prediction": "Unauthorized_Access_Attempt",
            "confidence_score": round(random.uniform(0.7, 0.9), 2),
            "timestamp": (start_time_pc + timedelta(minutes=i)).isoformat()
        })

    # Sort by timestamp to simulate real log stream (though engine handles sorting)
    alerts.sort(key=lambda x: x["timestamp"])

    with open(output_file, 'w') as f:
        json.dump(alerts, f, indent=2)
    
    print(f"Generated {len(alerts)} alerts in {output_file}")

if __name__ == "__main__":
    generate_alerts()
