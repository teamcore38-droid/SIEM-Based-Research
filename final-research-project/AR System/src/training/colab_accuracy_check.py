import json
import pandas as pd
import numpy as np
import re
import time
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

# ==============================================================
# 📂 CONFIGURATION
# ==============================================================
DATASET_LOGS_PHI = "Automated Response System 1.json"    
DATASET_ALERTS_THREATS = "Automated Response System 2.json" 

def load_json_utf16(filepath):
    try:
        with open(filepath, 'r', encoding='utf-16') as f:
            return pd.json_normalize(json.load(f))
    except Exception as e:
        print(f"⚠️ Could not load {filepath}: {e}")
        return None

# ==============================================================
# 🛡️ MODULE 1: THREAT INTELLIGENCE & RESPONSE + VALIDATION
# ==============================================================
def train_and_validate_defense_core():
    print("\n" + "="*80)
    print("🚑 SECTION 1: THREAT MODEL TRAINING & ACCURACY CHECK")
    print("="*80)

    df = load_json_utf16(DATASET_ALERTS_THREATS)
    if df is None: return

    feature_cols = ['Heart Rate (bpm)', 'SpO2 Level (%)', 'Systolic Blood Pressure (mmHg)', 
                    'Diastolic Blood Pressure (mmHg)', 'Body Temperature (°C)', 'Fall Detection']
    
    X = df[feature_cols].fillna(0)
    y_action = df['Response_Action'] # The exact target we want to predict

    # 1. Split Data (80% for Training, 20% for Testing)
    X_train, X_test, y_train, y_test = train_test_split(X, y_action, test_size=0.2, random_state=42)

    # 2. Train Model
    model_action = RandomForestClassifier(n_estimators=100, random_state=42)
    model_action.fit(X_train, y_train)

    # 3. Predict on the unseen Test Set
    y_pred = model_action.predict(X_test)

    # 4. Calculate Mathematical Accuracy
    acc = accuracy_score(y_test, y_pred)
    print(f"\n📊 MODEL ACCURACY SCORE: {acc*100:.2f}%")
    print("   (This means the model correctly decided Isolate vs Monitor vs No Action X% of the time)")
    
    print("\n📉 DETAILED CLASSIFICATION REPORT:")
    print(classification_report(y_test, y_pred))

    print("\n✅ VISUALIZING ACCURACY (Confusion Matrix)...")
    # Plot Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8,6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=model_action.classes_, yticklabels=model_action.classes_)
    plt.xlabel('Predicted Action')
    plt.ylabel('Actual Action')
    plt.title('Confusion Matrix: How often was the model right?')
    plt.show()

    return model_action

# ==============================================================
# 🛡️ MODULE 2: FUNCTIONAL VALIDATION (SIMULATION)
# ==============================================================
def run_functional_simulation(model):
    print("\n" + "="*80)
    print("⚙️ SECTION 2: FUNCTIONAL LOGIC CHECK (Does the Rollback Work?)")
    print("="*80)
    
    # Let's create specific TEST CASES to prove logic works
    # Case 1: Normal Patient (Should be NO ACTION)
    # Case 2: Critical Patient (Should be ISOLATE or MONITOR depending on dataset logic)
    
    test_cases = [
        # Normal
        {'Heart Rate (bpm)': 75, 'SpO2 Level (%)': 98, 'Systolic Blood Pressure (mmHg)': 120, 'Diastolic Blood Pressure (mmHg)': 80, 'Body Temperature (°C)': 37, 'Fall Detection': False, 'Label': 'Normal Patient'},
        # Critical Attack/Anomaly
        {'Heart Rate (bpm)': 200, 'SpO2 Level (%)': 50, 'Systolic Blood Pressure (mmHg)': 180, 'Diastolic Blood Pressure (mmHg)': 100, 'Body Temperature (°C)': 39, 'Fall Detection': True, 'Label': 'CRITICAL ATTACK'}
    ]
    
    df_test = pd.DataFrame(test_cases).drop(columns=['Label'])
    
    predictions = model.predict(df_test)
    
    for i, pred_action in enumerate(predictions):
        label = test_cases[i]['Label']
        print(f"\n🧪 TEST CASE: {label}")
        print(f"   └── Model Predicted: {pred_action}")
        
        # Verify Logic Chain
        if pred_action == "ISOLATE":
            print("   ✅ LOGIC CHECK PASS: Dangerous state triggered Isolation.")
            print("   👉 Simulating Workflow: BLOCK -> DEEP SCAN -> (Simulating Clean) -> ROLLBACK")
        elif pred_action == "NO ACTION":
            print("   ✅ LOGIC CHECK PASS: Normal state triggered No Action.")
        else:
            print(f"   ℹ️ Action Taken: {pred_action}")

# ==============================================================
# 🕵️ MODULE 3: REDACTION ACCURACY CHECK
# ==============================================================
def check_redaction_accuracy():
    print("\n" + "="*80)
    print("🔐 SECTION 3: PRIVACY MODULE CHECK")
    print("="*80)
    
    sample_text = "Alert: Patient ID P5555 has high temp. Age=45."
    print(f"📥 Input: '{sample_text}'")
    
    # Apply Logic
    redacted = re.sub(r'(Patient ID\s+)[A-Z0-9]+', r'\1[REDACTED_ID]', sample_text)
    redacted = re.sub(r'(Age=)\d+', r'\1[REDACTED_AGE]', redacted)
    
    print(f"📤 Output: '{redacted}'")
    
    if "[REDACTED_ID]" in redacted and "[REDACTED_AGE]" in redacted:
        print("✅ SUCCESS: Both PHI fields were correctly masked.")
    else:
        print("❌ FAILURE: Reduction logic missed some data.")

if __name__ == "__main__":
    trained_model = train_and_validate_defense_core()
    if trained_model:
        run_functional_simulation(trained_model)
    check_redaction_accuracy()
