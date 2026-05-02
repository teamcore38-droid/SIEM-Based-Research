import json
import pandas as pd
import numpy as np
import re
import time
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# ==============================================================
# 📂 CONFIGURATION
# ==============================================================
# PLEASE UPLOAD YOUR FILES TO COLAB:
DATASET_LOGS_PHI = "Automated Response System 1.json"    # Contains Text Logs (Patient ID, Age)
DATASET_ALERTS_THREATS = "Automated Response System 2.json" # Contains Vitals & Attack Types

def load_json_utf16(filepath):
    try:
        with open(filepath, 'r', encoding='utf-16') as f:
            return pd.json_normalize(json.load(f))
    except Exception as e:
        print(f"⚠️ Could not load {filepath}: {e}")
        return None

# ==============================================================
# 🛡️ MODULE 1: THREAT INTELLIGENCE & RESPONSE SIMULATION
# Requirement: Identify Attack -> Decide Action -> Block -> Monitor -> Rollback
# ==============================================================
def train_and_simulate_defense_core():
    print("\n" + "="*80)
    print("🚑 ARS CORE: THREAT RESPONSE SIMULATION (Dataset: Systems 2)")
    print("="*80)

    df = load_json_utf16(DATASET_ALERTS_THREATS)
    if df is None: return

    # --- 1. Train the Decision Brain ---
    print("🧠 Training Decision Models (Attack ID & Response Logic)...")
    
    feature_cols = ['Heart Rate (bpm)', 'SpO2 Level (%)', 'Systolic Blood Pressure (mmHg)', 
                    'Diastolic Blood Pressure (mmHg)', 'Body Temperature (°C)', 'Fall Detection']
    
    # We need two models: One to ID the attack, One to decide the action
    X = df[feature_cols].fillna(0)
    y_attack = df['Attack_Type']
    y_action = df['Response_Action']

    # Train Attack Identifier
    model_attack = RandomForestClassifier(n_estimators=50, random_state=42)
    model_attack.fit(X, y_attack)

    # Train Response Decider
    model_action = RandomForestClassifier(n_estimators=50, random_state=42)
    model_action.fit(X, y_action)

    print("✅ Models Trained successfully.\n")

    # --- 2. THE SIMULATION LOOP (As requested) ---
    print("⚡ STARTING REAL-TIME DEVICE SIMULATION")
    print("-" * 60)

    # Simulate processing the last 10 logs one by one
    simulation_data = X.tail(10).reset_index(drop=True)
    
    for i, row in simulation_data.iterrows():
        # Prepare input
        input_data = pd.DataFrame([row])
        
        # A. IDENTIFY ATTACK
        pred_attack = model_attack.predict(input_data)[0]
        
        # B. DECIDE ACTION
        pred_action = model_action.predict(input_data)[0]

        print(f"\n[LOG #{i+1}] Vitals: HR={row['Heart Rate (bpm)']} | SpO2={row['SpO2 Level (%)']}")
        print(f"   └── 🕵️  Analysis: Identified potential '{pred_attack}'")
        
        # C. EXECUTE RESPONSE LOGIC (State Machine)
        if pred_action == "NO ACTION":
            print(f"   └── ✅ Status: DEVICE NORMAL. No intervention needed.")
        
        elif pred_action == "MONITOR":
            print(f"   └── ⚠️  Action: INVESTIGATE. Deep scanning device...")
            # Logic: Check if it escalates (Simulated here as safe)
            print(f"       └── Result: Anomalies within variance limits. Continuing service.")

        elif pred_action == "ISOLATE":
            print(f"   └── 🚫 Action: BLOCK DEVICE (Firewall Rule Injected).")
            print(f"       └── 🔒 State: Device Isolated. Network Cut.")
            
            # D. DEEP MONITORING (In-depth investigation)
            print(f"       └── 🔎 Performing Deep Diagnostic Scan...")
            time.sleep(0.5) # Formatting pause
            
            # E. ROLLBACK DECISION
            # If the attack was NOT 'Unknown' or 'Malware', we might rollback after clearing
            if pred_attack != "Malware":
                print(f"       └── ✅ Diagnostic Clear: Threat neutralized.")
                print(f"       └── 🔄 ROLLBACK MECHANISM: Restoring firewall rules...")
                print(f"       └── 🟢 Device Online: Service Restored.")
                
            else:
                print(f"       └── ❌ CRITICAL: Malware persistence detected. Keeping Isolation.")

# ==============================================================
# 🕵️ MODULE 2: PHI REDACTION (PRIVACY)
# Requirement: Identify Patient ID/Age -> Mask (Redact)
# ==============================================================
def train_and_simulate_phi_redaction():
    print("\n" + "="*80)
    print("🔐 ARS PRIVACY: PHI REDACTION MODULE (Dataset: Systems 1)")
    print("="*80)

    df = load_json_utf16(DATASET_LOGS_PHI)
    if df is None: return

    # Custom Redaction Function using Regex (Pattern Matching)
    def redact_sensitive_info(text):
        original = text
        # 1. Redact Patient ID (Format Pxxxx or similar)
        # Using a broad regex for the dataset patterns like "Patient ID P1234"
        text = re.sub(r'(Patient ID\s+)[A-Z0-9]+', r'\1[REDACTED_ID]', text)
        
        # 2. Redact Age (Format Age=xx)
        text = re.sub(r'(Age=)\d+', r'\1[REDACTED_AGE]', text)
        
        # Check if reduction happened
        was_redacted = (original != text)
        return text, was_redacted

    print("📜 PROCESSING LOG STREAM FOR SENSITIVE DATA...")
    print("-" * 60)

    # Process a sample of logs
    sample_logs = df['Log_Text'].head(10)
    
    for i, log_text in enumerate(sample_logs):
        sanitized_text, modified = redact_sensitive_info(log_text)
        
        if modified:
            print(f"[LOG #{i+1}] 🔴 PHI DETECTED!")
            print(f"   Original:  {log_text}")
            print(f"   Sanitized: {sanitized_text}")
        else:
            print(f"[LOG #{i+1}] 🟢 Safe Log: {log_text}")

# ==============================================================
# MAIN EXECUTION
# ==============================================================
if __name__ == "__main__":
    train_and_simulate_defense_core()
    train_and_simulate_phi_redaction()
