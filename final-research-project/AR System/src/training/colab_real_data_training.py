
import json
import pandas as pd
import numpy as np
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# ==============================================================
# INSTRUCTIONS FOR GOOGLE COLAB USER
# ==============================================================
# 1. Upload your two JSON files to the "Files" tab on the left in Colab.
#    - Automated Response System 1.json
#    - Automated Response System 2.json
# 2. Run this entire script cells.
# ==============================================================

DATASET_1_PATH = "Automated Response System 1.json"
DATASET_2_PATH = "Automated Response System 2.json"

def load_json_utf16(filepath):
    """Helper to load UTF-16 encoded JSON files."""
    try:
        with open(filepath, 'r', encoding='utf-16') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    except FileNotFoundError:
        print(f"ERROR: File not found at {filepath}. Please upload it.")
        return None
    except Exception as e:
        print(f"ERROR reading {filepath}: {e}")
        return None

# ==============================================================
# PART 1: ARS DEFENSE ENGINE (Dataset 2)
# Purpose: Predict 'Response_Action' (ISOLATE/MONITOR) based on Vitals
# ==============================================================
print("\n" + "="*60)
print("🚀 PART 1: TRAINING ARS RESPONSE ENGINE (Threat Detection)")
print("="*60)

df_defense = load_json_utf16(DATASET_2_PATH)

if df_defense is not None:
    print(f"✅ Loaded Dataset 2 with {len(df_defense)} records.")
    
    # 1. Feature Engineering
    # Define Input Features (Sensor Data)
    feature_cols = [
        'Heart Rate (bpm)', 
        'SpO2 Level (%)', 
        'Systolic Blood Pressure (mmHg)', 
        'Diastolic Blood Pressure (mmHg)', 
        'Body Temperature (°C)', 
        'Fall Detection'
    ]
    
    # Define Target (What action should ARS take?)
    target_col = 'Response_Action'
    
    # Handle missing values if any
    df_defense = df_defense.dropna(subset=feature_cols + [target_col])
    
    X = df_defense[feature_cols]
    y = df_defense[target_col]
    
    # Convert 'Fall Detection' from boolean to int
    X['Fall Detection'] = X['Fall Detection'].astype(int)
    
    print("\nTarget Distribution:")
    print(y.value_counts())
    
    # 2. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Model Training (Random Forest)
    # Good for tabular data and capturing non-linear relationships in vitals
    response_model = RandomForestClassifier(n_estimators=100, random_state=42)
    response_model.fit(X_train, y_train)
    
    # 4. Evaluation
    y_pred = response_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    print(f"\n🏆 Defense Model Accuracy: {acc*100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # 5. Example Prediction
    example_patient = pd.DataFrame([{
        'Heart Rate (bpm)': 180,              # High!
        'SpO2 Level (%)': 80,                 # Low!
        'Systolic Blood Pressure (mmHg)': 140,
        'Diastolic Blood Pressure (mmHg)': 90,
        'Body Temperature (°C)': 38.5,
        'Fall Detection': 1
    }])
    feature_names = X_train.columns
    # Ensure column order
    example_patient = example_patient[feature_names] 
    
    action = response_model.predict(example_patient)[0]
    print(f"\n🧪 Test Case (Critical Patient): Predicted Action -> {action}")


# ==============================================================
# PART 2: ARS CONTEXT AWARENESS (Dataset 1)
# Purpose: Detect if a Log contains PHI (Protected Health Info)
# ==============================================================
print("\n" + "="*60)
print("🔒 PART 2: TRAINING PHI DETECTION MODEL (Contextual Privacy)")
print("="*60)

df_logs = load_json_utf16(DATASET_1_PATH)

if df_logs is not None:
    print(f"✅ Loaded Dataset 1 with {len(df_logs)} records.")
    
    # 1. Feature Engineering
    # Input: Log Text string
    # Target: Boolean (Contains_Phi)
    
    X_text = df_logs['Log_Text']
    y_phi = df_logs['Contains_Phi'].astype(int) # 1 = Has PHI, 0 = No PHI
    
    print("\nPHI Class Distribution:")
    print(y_phi.value_counts())
    
    # 2. Train/Test Split
    X_train_txt, X_test_txt, y_train_txt, y_test_txt = train_test_split(X_text, y_phi, test_size=0.2, random_state=42)
    
    # 3. Model Training (TF-IDF + Naive Bayes)
    # Standard pipeline for text classification
    phi_model = make_pipeline(TfidfVectorizer(), MultinomialNB())
    phi_model.fit(X_train_txt, y_train_txt)
    
    # 4. Evaluation
    y_pred_txt = phi_model.predict(X_test_txt)
    acc_txt = accuracy_score(y_test_txt, y_pred_txt)
    
    print(f"\n🏆 PHI Detection Accuracy: {acc_txt*100:.2f}%")
    print("\nClassification Report (1=Includes PHI, 0=Safe):")
    print(classification_report(y_test_txt, y_pred_txt))
    
    # 5. Quick Test
    test_log = ["System status check normal.", "Patient ID P-999 detected arrhythmia."]
    preds = phi_model.predict(test_log)
    print(f"\n🧪 Test Logs Analysis:")
    for log, pred in zip(test_log, preds):
        status = "🔴 CONTAINS PHI" if pred == 1 else "🟢 SAFE"
        print(f"   Log: '{log}' -> {status}")

print("\n" + "="*60)
print("✅ ARS Training Complete.")
