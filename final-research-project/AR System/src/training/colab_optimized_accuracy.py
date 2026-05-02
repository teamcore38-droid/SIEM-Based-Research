
import json
import pandas as pd
import numpy as np
import re
import time
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from imblearn.over_sampling import SMOTE  # IMPORTANT: For handling class imbalance

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
# 🚀 OPTIMIZATION ENGINE to Reach 99% Accuracy
# ==============================================================
def train_optimized_defense_core():
    print("\n" + "="*80)
    print("🚀 OPTIMIZING MODEL FOR >95% ACCURACY")
    print("="*80)

    df = load_json_utf16(DATASET_ALERTS_THREATS)
    if df is None: return

    feature_cols = ['Heart Rate (bpm)', 'SpO2 Level (%)', 'Systolic Blood Pressure (mmHg)', 
                    'Diastolic Blood Pressure (mmHg)', 'Body Temperature (°C)', 'Fall Detection']
    
    # Preprocessing
    X = df[feature_cols].fillna(0)
    y_action = df['Response_Action']

    # --- PROBLEM DIAGNOSIS ---
    print("📊 Original Class Distribution:")
    print(y_action.value_counts())
    print("\n⚠️ Note: If 'NO_ACTION' is 90% of data, the model ignores ISOLATE/MONITOR.")
    print("👉 ACTION: Applying SMOTE (Synthetic Minority Over-sampling Technique) to balance classes.\n")

    # 1. SPLIT DATA
    X_train, X_test, y_train, y_test = train_test_split(X, y_action, test_size=0.2, random_state=42)

    # 2. APPLY SMOTE (Fixing Imbalance)
    # This creates synthetic examples of "ISOLATE" so the model learns them better
    smote = SMOTE(random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
    
    print(f"✅ Balanced Class Distribution (Training Set):")
    print(y_train_balanced.value_counts())

    # 3. UPGRADE MODEL (RandomForest -> GradientBoosting)
    # GBM is often more precise for structured data than bare RF
    print("\nTraining Advanced Gradient Boosting Model...")
    model = GradientBoostingClassifier(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
    model.fit(X_train_balanced, y_train_balanced)

    # 4. EVALUATE
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    print(f"\n🏆 FINAL OPTIMIZED ACCURACY: {acc*100:.2f}%")
    
    print("\n📉 CLASSIFICATION REPORT (Look at Recall for ISOLATE):")
    print(classification_report(y_test, y_pred))

    return model

# ==============================================================
# 🛡️ VALIDATION (Retesting Logic)
# ==============================================================
def run_functional_simulation(model):
    print("\n" + "="*80)
    print("⚙️ LOGIC RE-VERIFICATION")
    print("="*80)
    
    test_cases = [
        {'Heart Rate (bpm)': 75, 'SpO2 Level (%)': 98, 'Systolic Blood Pressure (mmHg)': 120, 'Diastolic Blood Pressure (mmHg)': 80, 'Body Temperature (°C)': 37, 'Fall Detection': False, 'Label': 'Normal'},
        {'Heart Rate (bpm)': 200, 'SpO2 Level (%)': 50, 'Systolic Blood Pressure (mmHg)': 180, 'Diastolic Blood Pressure (mmHg)': 100, 'Body Temperature (°C)': 39, 'Fall Detection': True, 'Label': 'CRITICAL ATTACK'}
    ]
    
    df_test = pd.DataFrame(test_cases).drop(columns=['Label'])
    predictions = model.predict(df_test)
    
    for i, pred_action in enumerate(predictions):
        label = test_cases[i]['Label']
        print(f"Test '{label}' -> Predicted: {pred_action}")

if __name__ == "__main__":
    optimized_model = train_optimized_defense_core()
    if optimized_model:
        run_functional_simulation(optimized_model)
