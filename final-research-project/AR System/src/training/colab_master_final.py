
# ==============================================================================
# 🌟 FINAL MASTER SCRIPT: AR SYSTEM TRAINING & VALIDATION (OPTIMIZED)
# ==============================================================================
# INSTRUCTIONS:
# 1. This script uses 'optimized_threat_triggers.json' and 'optimized_phi_logs.json'.
# 2. It trains:
#    - Defense Model: Predicts ISOLATE/MONITOR/ROLLBACK based on Network Threats.
#    - Privacy Model: Detects PHI in logs using Hybrid AI + Regex.
# 3. Output: 'ars_decision_model_final.pkl' & 'ars_phi_model.pkl'
# ==============================================================================

import json
import pandas as pd
import numpy as np
import re
import joblib
import os

# ML Libraries
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import accuracy_score, classification_report

# ==============================================================================
# 📂 CONFIGURATION
# ==============================================================================
# Navigate to data folder (assuming script is in src/training/ and data is in data/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'data'))
MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'models'))

THREAT_DATASET = os.path.join(DATA_DIR, "optimized_threat_triggers.json")
PHI_DATASET = os.path.join(DATA_DIR, "optimized_phi_logs.json")

# Helper to load JSON
def load_data(filepath):
    try:
        if not os.path.exists(filepath):
             print(f"❌ ERROR: File '{filepath}' not found.")
             return None
        with open(filepath, 'r', encoding='utf-8') as f: # standard encoding for optimized files
            return pd.json_normalize(json.load(f))
    except Exception as e:
        print(f"❌ ERROR loading '{filepath}': {e}")
        return None

# ==============================================================================
# 🛡️ MODULE 1: DEFENSE CORE (Network Threat -> Response)
# ==============================================================================
print("\n" + "="*80)
print("🚀 PHASE 1: TRAINING DEFENSE MODEL (Network Threats)")
print("="*80)

df_threats = load_data(THREAT_DATASET)

if df_threats is not None:
    # 1. Prepare Data
    # Features: Threat Type, Severity, Confidence
    # Target: Action Required (ISOLATE, MONITOR, ROLLBACK, NO_ACTION)
    
    X = df_threats[['threat_type', 'severity', 'confidence_score']]
    y = df_threats['action_required']
    
    # 2. Pipeline: OneHotEncode Categoricals + RandomForest
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), ['threat_type', 'severity'])
        ],
        remainder='passthrough' # Keep confidence_score as is
    )
    
    model_defense = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    # 3. Train
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model_defense.fit(X_train, y_train)
    
    # 4. Accuracy Check
    preds = model_defense.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"🏆 DEFENSE MODEL ACCURACY: {acc*100:.2f}%")
    
    # 5. Visual Verification
    print("\n📋 TEST PREDICTIONS:")
    test_inputs = pd.DataFrame([
        {'threat_type': 'Ransomware_Behavior', 'severity': 'Critical', 'confidence_score': 0.95}, # Should ISOLATE
        {'threat_type': 'Routine_Update', 'severity': 'None', 'confidence_score': 0.10},        # Should NO_ACTION
        {'threat_type': 'Post_Attack_Cleanup', 'severity': 'High', 'confidence_score': 1.0}     # Should ROLLBACK
    ])
    
    pred_test = model_defense.predict(test_inputs)
    for i, row in test_inputs.iterrows():
        print(f"   Input: {row['threat_type']} ({row['severity']}) -> Predicted: {pred_test[i]}")

    # Save
    if not os.path.exists(MODEL_DIR): os.makedirs(MODEL_DIR)
    joblib.dump(model_defense, os.path.join(MODEL_DIR, 'ars_decision_model_final.pkl'))
    print(f"✅ Saved model to: {MODEL_DIR}")

# ==============================================================================
# 🔐 MODULE 2: PRIVACY CORE (Logs -> PHI Redaction)
# ==============================================================================
print("\n" + "="*80)
print("🚀 PHASE 2: TRAINING PRIVACY MODEL (PHI Detection)")
print("="*80)

df_phi = load_data(PHI_DATASET)

if df_phi is not None:
    # 1. Prepare Data
    X_txt = df_phi['raw_log_message']
    y_detect = df_phi['phi_present'].astype(int) # True/False -> 1/0
    
    # 2. Pipeline: TF-IDF + Naive Bayes
    model_phi = make_pipeline(TfidfVectorizer(), MultinomialNB())
    
    # 3. Train
    X_train_phi, X_test_phi, y_train_phi, y_test_phi = train_test_split(X_txt, y_detect, test_size=0.2, random_state=42)
    model_phi.fit(X_train_phi, y_train_phi)
    
    # 4. Accuracy
    preds_phi = model_phi.predict(X_test_phi)
    acc_phi = accuracy_score(y_test_phi, preds_phi)
    print(f"🏆 PRIVACY MODEL ACCURACY: {acc_phi*100:.2f}%")
    
    # 5. Visual Check
    print("\n📋 TEST REDACTION:")
    sample_log = "Patient ID 12345 admitted with severe symptoms."
    
    # Prediction
    is_phi = model_phi.predict([sample_log])[0]
    result_status = "DETECTED" if is_phi else "SAFE"
    
    # Regex Cleanup (as part of the 'System' logic, usually runs after detection)
    if is_phi:
        redacted_text = re.sub(r'\b\d{5,6}\b', '[REDACTED_ID]', sample_log)
    else:
        redacted_text = sample_log
        
    print(f"   Log: '{sample_log}' -> {result_status}")
    print(f"   Output: '{redacted_text}'")

    # Save
    joblib.dump(model_phi, os.path.join(MODEL_DIR, 'ars_phi_model.pkl'))

print("\n" + "="*80)
print("🎉 ALL SYSTEMS GO. MODELS UPDATED.")
print("="*80)
