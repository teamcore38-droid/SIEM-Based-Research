import pickle
import numpy as np
import time

# Load Models
print("--- Loading ARS Models ---")
try:
    with open("ars_response_model.pkl", "rb") as f:
        response_bundle = pickle.load(f)
    print("✅ Response Model Loaded")

    with open("ars_phi_model.pkl", "rb") as f:
        phi_bundle = pickle.load(f)
    print("✅ PHI Model Loaded")
except FileNotFoundError:
    print("❌ ERROR: Model files not found! Please ensure .pkl files are in this folder.")
    exit()

def get_action_prediction(threat_type, severity, confidence):
    model = response_bundle["model"]
    le_threat = response_bundle["le_threat"]
    # We might not have le_severity inside if we updated logic, 
    # but let's assume standard map logic just in case:
    severity_map = {"None": 0, "Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    
    # 1. Encode Threat
    try:
        t_encoded = le_threat.transform([threat_type])[0]
    except:
        return f"⚠️ Unknown Threat: {threat_type}"
        
    # 2. Encode Severity
    s_encoded = severity_map.get(severity, 0)
    
    # 3. Predict
    decision_idx = model.predict([[t_encoded, s_encoded, float(confidence)]])[0]
    
    # 4. Map Action
    action_map = {0: "NO_ACTION", 1: "MONITOR", 2: "ISOLATE", 3: "ROLLBACK"}
    return action_map.get(decision_idx, "UNKNOWN")

def get_phi_prediction(log_text):
    model = phi_bundle["model"]
    vectorizer = phi_bundle["vectorizer"]
    vec = vectorizer.transform([log_text.lower()])
    pred = model.predict(vec)[0]
    return "🛑 PHI DETECTED" if pred == 1 else "✅ CLEAN LOG"

# --- PART 1: ACCURACY CHECK (Self-Test) ---
print("\n[PART 1] Running Auto-Verification Tests...")
test_cases = [
    ("Ransomware_Behavior", "Critical", 0.95, "ISOLATE"),
    ("Normal_Heartbeat", "None", 0.10, "NO_ACTION"),
    ("Data_Exfiltration", "High", 0.60, "MONITOR")
]

passed = 0
for t, s, c, expected in test_cases:
    result = get_action_prediction(t, s, c)
    if result == expected:
        print(f"  [PASS] {t} -> {result}")
        passed += 1
    else:
        print(f"  [FAIL] {t} -> Got {result}, Expected {expected}")

if passed == len(test_cases):
    print(">>> Accuracy Check: 100% (Models are working correctly)")
else:
    print(">>> Accuracy Check: FAILED. Please retrain.")

# --- PART 2: MANUAL INTERFACE ---
print("\n[PART 2] Manual Testing Mode")
print("Type 'exit' to quit.\n")

while True:
    print("-" * 30)
    mode = input("Select Mode (1=Threat Action, 2=PHI Check): ")
    
    if mode.lower() == 'exit': break
    
    if mode == "1":
        print("\n--- Threat Response Test ---")
        print("Threat Options: Ransomware_Behavior, DDoS_Flood, Unauthorized_Access, Normal_Heartbeat, Routine_Update")
        t_in = input("Enter Threat Type: ")
        if t_in.lower() == 'exit': break
        
        print("Severity Options: Critical, High, Medium, Low, None")
        s_in = input("Enter Severity: ")
        
        c_in = input("Enter Confidence (0.0 - 1.0): ")
        
        print(f"\n>>> MODEL SAYS: {get_action_prediction(t_in, s_in, c_in)}")
        
    elif mode == "2":
        print("\n--- PHI Log Scanner ---")
        l_in = input("Enter Log Message: ")
        if l_in.lower() == 'exit': break
        
        print(f"\n>>> MODEL SAYS: {get_phi_prediction(l_in)}")
    
    else:
        print("Invalid Selection.")
