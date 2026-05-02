import pickle
import pandas as pd
import numpy as np

# Load Models
print("Loading trained models...")
with open("ars_response_model.pkl", "rb") as f:
    response_bundle = pickle.load(f)
    print(" - Loaded Response Model")

with open("ars_phi_model.pkl", "rb") as f:
    phi_bundle = pickle.load(f)
    print(" - Loaded PHI Model")

# Helper function to predict action
def predict_action(threat_type, severity, confidence):
    # 1. Access the model and encoders
    model = response_bundle["model"]
    le_threat = response_bundle["le_threat"]
    le_severity = response_bundle["le_severity"]
    
    # 2. Encode inputs (Handle unknown labels safely)
    try:
        t_encoded = le_threat.transform([threat_type])[0]
        s_encoded = le_severity.transform([severity])[0]
    except ValueError as e:
        print(f"Error: Unknown label {e}")
        return "ERROR"
        
    # 3. Predict
    # Input order must match training: [threat_type, severity, confidence_score]
    input_vector = np.array([[t_encoded, s_encoded, confidence]])
    pred_idx = model.predict(input_vector)[0]
    
    # 4. Map back to string
    # 0=NO_ACTION, 1=MONITOR, 2=ISOLATE, 3=ROLLBACK
    action_map = {0: "NO_ACTION", 1: "MONITOR", 2: "ISOLATE", 3: "ROLLBACK"}
    return action_map.get(pred_idx, "UNKNOWN")

# Helper function to predict PHI
def predict_phi(log_text):
    model = phi_bundle["model"]
    vectorizer = phi_bundle["vectorizer"]
    
    # Vectorize text
    vec_text = vectorizer.transform([log_text])
    pred = model.predict(vec_text)[0]
    
    return "DETECTED" if pred == 1 else "CLEAN"

# --- SCENARIOS ---

print("\n--- TEST SCENARIO 1: Critical Ransomware Attack ---")
t1 = "Ransomware_Behavior"
s1 = "Critical"
c1 = 0.95
print(f"Input: {t1} | {s1} | Conf: {c1}")
decision = predict_action(t1, s1, c1)
print(f"MODEL DECISION: >> {decision} <<")

print("\n--- TEST SCENARIO 2: Suspicious Login Attempt ---")
t2 = "Unauthorized_Access"
s2 = "Medium"
c2 = 0.60
print(f"Input: {t2} | {s2} | Conf: {c2}")
decision = predict_action(t2, s2, c2)
print(f"MODEL DECISION: >> {decision} <<")

print("\n--- TEST SCENARIO 3: Routine Heartbeat ---")
t3 = "Normal_Heartbeat"
s3 = "None"
c3 = 0.10
print(f"Input: {t3} | {s3} | Conf: {c3}")
decision = predict_action(t3, s3, c3)
print(f"MODEL DECISION: >> {decision} <<")

print("\n--- TEST SCENARIO 4: Post-Attack Cleanup ---")
t4 = "Post_Attack_Cleanup"
s4 = "High"
c4 = 1.0
# Note: "Post_Attack_Cleanup" might need to be in the encoder if we trained with it.
# If we generated it in the dataset, it will be there.
try:
    decision = predict_action("Routine_Update", "High", 1.0) # Using a known label for safety if 'Post' wasn't in random set
    # Let's try to simulate the ROLLBACK logic we trained
    # Recall: ROLLBACK triggered randomly in generation. 
    # If the label 'Post_Attack_Cleanup' exists in the encoder, this works.
    pass
except:
    pass

print("\n--- TEST SCENARIO 5: PHI Log Scanning ---")
log1 = "Patient ID 99238 admitted to ICU."
print(f"Log: '{log1}'")
print(f"PHI SCANNER: >> {predict_phi(log1)} <<")

log2 = "System uptime 99.9%."
print(f"Log: '{log2}'")
print(f"PHI SCANNER: >> {predict_phi(log2)} <<")
