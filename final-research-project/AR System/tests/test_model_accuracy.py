import joblib
import pandas as pd
import os
import sys
from sklearn.metrics import accuracy_score, classification_report

def check_threat_model_accuracy():
    print("\n🔍 CHECKING THREAT MODEL ACCURACY")
    print("==================================")
    
    # 1. Define Paths
    base_dir = os.path.dirname(os.path.abspath(__file__)) # tests/
    model_path = os.path.join(base_dir, '..', 'models', 'ars_decision_model_final.pkl')
    data_path = os.path.join(base_dir, '..', 'data', 'ars_high_fidelity_training.csv')
    
    # 2. Load Model
    if not os.path.exists(model_path):
        print("[ERROR] Model not found.")
        return
    model = joblib.load(model_path)
    print(f"✅ Model Loaded: {os.path.basename(model_path)}")

    # 3. Load Data
    if not os.path.exists(data_path):
        print("[ERROR] Data not found.")
        return
    df = pd.read_csv(data_path)
    print(f"✅ Data Loaded: {len(df)} records")

    # 4. Prepare Features
    # The model was trained on specific columns: 
    # ['heart_rate', 'spo2', 'sys_bp', 'network_latency', 'packet_size', 'anomaly_score']
    # We must ensure we pass exactly these.
    
    # Check if 'ACTION_LABEL' exists (Target)
    if 'ACTION_LABEL' not in df.columns:
        print("[ERROR] Data missing 'ACTION_LABEL' column.")
        return

    # Drop target and extra metadata columns to get X
    # Based on retraining script: X = df.drop(columns=['ACTION_LABEL', 'threat_type'])
    X = df.drop(columns=['ACTION_LABEL', 'threat_type'])
    y_true = df['ACTION_LABEL']
    
    # 5. Predict
    y_pred = model.predict(X)
    
    # 6. Score
    acc = accuracy_score(y_true, y_pred)
    print(f"\n🏆 MODEL ACCURACY: {acc * 100:.2f}%")
    print("\n📊 CLASSIFICATION REPORT:")
    print(classification_report(y_true, y_pred))

if __name__ == "__main__":
    check_threat_model_accuracy()
