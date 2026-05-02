import pandas as pd
import pickle
import os
import json
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix

# Hardcoded Paths
BASE_DIR = r"c:\Users\yasim\OneDrive - Sri Lanka Institute of Information Technology (1)\Desktop\Research\Git-Repo PP1\final-research-project\AR System"
DATA_DIR = r"c:\Users\yasim\OneDrive - Sri Lanka Institute of Information Technology (1)\Desktop\Research\Git-Repo PP1\final-research-project\AR System\data"
MODEL_DIR = r"c:\Users\yasim\OneDrive - Sri Lanka Institute of Information Technology (1)\Desktop\Research\Git-Repo PP1\final-research-project\AR System\models"

RESPONSE_MODEL_PATH = os.path.join(MODEL_DIR, "ars_response_model.pkl")
RESPONSE_DATA_PATH = os.path.join(DATA_DIR, "optimized_threat_triggers.json")

PHI_MODEL_PATH = os.path.join(MODEL_DIR, "ars_phi_model.pkl")
PHI_DATA_PATH = os.path.join(DATA_DIR, "optimized_phi_logs.json")

def analyze_response_model():
    print("\n" + "="*60)
    print("🚨 MODEL 1: THREAT RESPONSE MODEL (Multi-Class)")
    print("="*60)

    # 1. Load Model
    if not os.path.exists(RESPONSE_MODEL_PATH):
        print(f"❌ Model not found: {RESPONSE_MODEL_PATH}")
        return

    with open(RESPONSE_MODEL_PATH, 'rb') as f:
        bundle = pickle.load(f)
    
    if isinstance(bundle, dict):
        model = bundle.get('model')
        le_threat = bundle.get('le_threat')
        le_severity = bundle.get('le_severity')
    else:
        print("Invalid model bundle format")
        return

    # 2. Load Data
    try:
        with open(RESPONSE_DATA_PATH, 'r') as f:
            df = pd.DataFrame(json.load(f))
    except Exception as e:
        print(f"❌ Load Failed: {e}")
        return

    # 3. Predict
    X = df[['threat_type', 'severity', 'confidence_score']].copy()
    y_true = df['action_required']
    
    # Transform format
    X['threat_type'] = le_threat.transform(X['threat_type'])
    X['severity'] = le_severity.transform(X['severity'])

    y_pred = model.predict(X)
    
    # 4. Matrix
    labels = sorted(list(set(y_true))) # ISOLATE, MONITOR, NO_ACTION, ROLLBACK
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    acc = accuracy_score(y_true, y_pred)
    
    print(f"Accuracy: {acc:.4f}")
    print(f"Labels: {labels}")
    print("Confusion Matrix (Rows=Actual, Cols=Predicted):")
    print(cm)
    
    # Calculate Total Correct
    total_correct = np.trace(cm)
    total_samples = np.sum(cm)
    print(f"Total Correct: {total_correct}")
    print(f"Total Samples: {total_samples}")


def analyze_phi_model():
    print("\n" + "="*60)
    print("🔐 MODEL 2: PHI DETECTION MODEL (Binary)")
    print("="*60)

    # 1. Load Model
    if not os.path.exists(PHI_MODEL_PATH):
        print(f"❌ Model not found: {PHI_MODEL_PATH}")
        return

    with open(PHI_MODEL_PATH, 'rb') as f:
        bundle = pickle.load(f)

    model = bundle['model']
    vectorizer = bundle['vectorizer']

    # 2. Load Data
    try:
        with open(PHI_DATA_PATH, 'r') as f:
            df = pd.DataFrame(json.load(f))
    except Exception as e:
        print(f"❌ Load Failed: {e}")
        return

    # 3. Predict
    X_text = df['raw_log_message']
    y_true = df['phi_present'].astype(int) # 1=PHI, 0=Safe

    X_vec = vectorizer.transform(X_text)
    y_pred = model.predict(X_vec)
    
    # 4. Matrix
    # Labels: 0=No PHI, 1=PHI
    # TN, FP, FN, TP structure for binary (0, 1) usually:
    # [[TN, FP],
    #  [FN, TP]]
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    acc = accuracy_score(y_true, y_pred)
    
    print(f"Accuracy: {acc:.4f}")
    print(f"TN: {tn}, FP: {fp}, FN: {fn}, TP: {tp}")

if __name__ == "__main__":
    analyze_response_model()
    analyze_phi_model()
