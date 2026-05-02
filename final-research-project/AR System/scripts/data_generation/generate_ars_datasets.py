import json
import random
import datetime
import uuid

# ==========================================
# DATASET 1: THREAT TRIGGER DATASET
# Purpose: To test Device Isolation & Rollback logic
# Input Source: From Correlation Engine (Component 4)
# ==========================================

def generate_threat_dataset(num_records=50000):
    dataset = []
    threat_types = ["Ransomware_Behavior", "DDoS_Flood", "Unauthorized_Access", "Data_Exfiltration", "Malware_C2", "Normal_Heartbeat", "Routine_Update"]
    severities = ["Critical", "High", "Medium", "Low", "None"]
    
    for _ in range(num_records):
        device_ip = f"192.168.1.{random.randint(10, 200)}"
        device_id = f"IOT-{random.randint(1000, 9999)}"
        threat = random.choice(threat_types)
        
        # Logic to assign Action based on Severity & Context
        # User Logic: Normal -> Quarantine(Monitor) -> Isolate -> Rollback
        
        # 1. Random base values
        confidence_score = round(random.uniform(0.0, 0.99), 2)
        
        # 2. Assign Severity & Action Logic
        if threat in ["Normal_Heartbeat", "Routine_Update"]:
            severity = "None"
            action = "NO_ACTION"
            confidence_score = round(random.uniform(0.0, 0.3), 2) # Low confidence of threat
            
        elif threat in ["Unauthorized_Access", "Data_Exfiltration"]:
            # Suspicious but maybe not confirmed yet -> MONITOR (Deep Scan)
            severity = random.choice(["Medium", "High"])
            action = "MONITOR"
            confidence_score = round(random.uniform(0.4, 0.7), 2)
            
        elif threat in ["Ransomware_Behavior", "DDoS_Flood", "Malware_C2"]:
            # Active Attack -> ISOLATE
            severity = "Critical"
            action = "ISOLATE"
            confidence_score = round(random.uniform(0.8, 0.99), 2)
            
        # 3. Simulate Rollback Condition
        # Occasional case: A device was isolated and now needs recovery
        # We simulate this by having a specific "Recovery_Flag" or treating it as a specific state
        if random.random() < 0.1: # 10% chance it's a post-attack recovery event
            threat = "Post_Attack_Cleanup"
            severity = "High"
            action = "ROLLBACK"
            confidence_score = 1.0 # Certainty that we need to fix it

        record = {
            "alert_id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.now().isoformat(),
            "target_ip": device_ip,
            "device_id": device_id,
            "threat_type": threat,
            "severity": severity,
            "confidence_score": confidence_score,
            "action_required": action # Target Variable: NO_ACTION, MONITOR, ISOLATE, ROLLBACK
        }
        dataset.append(record)
        
    return dataset

# ==========================================
# DATASET 2: PHI LOG DATASET
# Purpose: To test PHI Redaction Module
# Input Source: From Monitoring System (Component 1)
# ==========================================

def generate_phi_log_dataset(num_records=50):
    dataset = []
    
    # Fake PHI data generators
    first_names = ["John", "Jane", "Alice", "Bob", "Saman", "Kamal", "Nimal"]
    last_names = ["Doe", "Smith", "Perera", "Silva", "Fernando"]
    conditions = ["Cardiac Arrest", "Diabetes Type 2", "High Fever", "COVID-19 Positive", "Normal"]
    
    for _ in range(num_records):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        patient_id = f"{random.randint(100000, 999999)}"
        condition = random.choice(conditions)
        
        # Generate a log message that mimics a hospital device log
        log_templates = [
            f"Patient {name} (ID: {patient_id}) admitted to ICU.",
            f"Infusion pump error for patient {name}. Dosage mismatch.",
            f"Vitals update: HR 120bpm for ID #{patient_id}. Condition: {condition}.",
            f"User admin accessed record of {name} at 10:00 AM.",
            f"Device connection established. No patient data context."
        ]
        
        raw_log = random.choice(log_templates)
        
        record = {
            "log_id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.now().isoformat(),
            "source_device": f"BED-{random.randint(100,200)}-MONITOR",
            
            # --- CRITICAL COLUMNS FOR REDACTION ---
            "raw_log_message": raw_log,      # The text we need to clean
            "phi_present": True if ("Patient" in raw_log or "ID" in raw_log) else False,
            
            # --- DATA FOR VADLIATION (Ground Truth) ---
            "detected_entities_verification": { 
                "names": [name] if name in raw_log else [],
                "ids": [patient_id] if patient_id in raw_log else [],
                "medical_terms": [condition] if condition in raw_log else []
            }
            
            # --- REMOVED UNWANTED COLUMNS ---
            # - No "Source_Port" (Not relevant for text redaction context)
            # - No "Hex_Dump" (Unless we are parsing packets depth, but typically we redact string logs)
        }
        dataset.append(record)
        
    return dataset

if __name__ == "__main__":
    # Generate 50,000 records for robust testing
    threat_data = generate_threat_dataset(50000)
    phi_data = generate_phi_log_dataset(50000)
    
    # Save
    with open("optimized_threat_triggers.json", "w") as f:
        json.dump(threat_data, f, indent=4)
        print("Created: optimized_threat_triggers.json (50,000 records)")
        
    with open("optimized_phi_logs.json", "w") as f:
        json.dump(phi_data, f, indent=4)
        print("Created: optimized_phi_logs.json (50,000 records)")
