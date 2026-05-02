
import os
import joblib
import pandas as pd
import sys

# Color codes for terminal
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def test_local_models():
    print(f"\n🧪 {GREEN}STARTING LOCAL MODEL VERIFICATION TEST{RESET}")
    print("=" * 60)
    
    # 1. DEFINE PATHS
    # 1. DEFINE PATHS
    base_path = os.path.dirname(os.path.abspath(__file__))
    # Models are now at root/models (src/core -> src -> root)
    model_dir = os.path.abspath(os.path.join(base_path, '..', '..', 'models'))
    
    defense_path = os.path.join(model_dir, 'ars_decision_model_final.pkl')
    phi_path = os.path.join(model_dir, 'ars_phi_model.pkl')
    
    print(f"📂 Looking for models in: {model_dir}")
    
    # 2. CHECK FILE EXISTENCE
    if not os.path.exists(defense_path):
        print(f"{RED}❌ CRITICAL ERROR: 'ars_decision_model_final.pkl' NOT FOUND.{RESET}")
        print("   Did you download it from Colab and paste it here?")
        return
    else:
        print(f"{GREEN}✅ Found Defense Model.{RESET}")
        
    if not os.path.exists(phi_path):
        print(f"{RED}⚠️ WARNING: 'ars_phi_model.pkl' NOT FOUND.{RESET}")
        print("   Privacy features will fail, but Defense Core might work.")
    else:
        print(f"{GREEN}✅ Found Privacy Model.{RESET}")

    # 3. LOAD MODELS
    try:
        defense_model = joblib.load(defense_path)
        print(f"{GREEN}✅ Defense Model Loaded Successfully.{RESET}")
    except Exception as e:
        print(f"{RED}❌ Failed to load Defense Model: {e}{RESET}")
        return

    # 4. TEST CASE: HIGH THREAT (Should be ISOLATE)
    print("\n🔬 TEST 1: SIMULATING CYBER-ATTACK (Anomaly Score=0.95)")
    print("-" * 50)
    
    # Matches the feature columns used in training
    test_features = ['Heart Rate (bpm)', 'SpO2 Level (%)', 'Systolic Blood Pressure (mmHg)', 
                     'Diastolic Blood Pressure (mmHg)', 'Body Temperature (°C)', 'Fall Detection', 'Anomaly_Score']
    
    # Fake Malicious Data
    input_data = pd.DataFrame([{
        'Heart Rate (bpm)': 80,
        'SpO2 Level (%)': 98,
        'Systolic Blood Pressure (mmHg)': 120,
        'Diastolic Blood Pressure (mmHg)': 80,
        'Body Temperature (°C)': 37.0,
        'Fall Detection': 0,
        'Anomaly_Score': 0.95  # <--- THE TRIGGER
    }])
    
    # Reorder columns just to be safe
    input_data = input_data[test_features]
    
    prediction = defense_model.predict(input_data)[0]
    print(f"👉 Input Score: 0.95")
    print(f"👉 Model Prediction: {prediction}")
    
    if prediction == "ISOLATE":
        print(f"{GREEN}✅ SUCCESS: Model correctly blocked the attack.{RESET}")
    else:
        print(f"{RED}❌ FAILURE: Model predicted '{prediction}' instead of ISOLATE.{RESET}")

    # 5. TEST CASE: LOW THREAT (Should be NO_ACTION)
    print("\n🔬 TEST 2: SIMULATING HEALTHY DEVICE (Anomaly Score=0.01)")
    print("-" * 50)
    
    input_data['Anomaly_Score'] = 0.01
    prediction = defense_model.predict(input_data)[0]
    
    print(f"👉 Input Score: 0.01")
    print(f"👉 Model Prediction: {prediction}")
    
    if prediction == "NO_ACTION":
        print(f"{GREEN}✅ SUCCESS: Model correctly allowed normal traffic.{RESET}")
    else:
        print(f"{RED}❌ FAILURE: Model predicted '{prediction}' instead of NO_ACTION.{RESET}")

if __name__ == "__main__":
    test_local_models()
