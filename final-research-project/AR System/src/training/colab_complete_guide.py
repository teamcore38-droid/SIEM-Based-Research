
# ==============================================================================
# 🎓 STEP-BY-STEP GUIDE: TRAINING ARS MODELS IN GOOGLE COLAB
# ==============================================================================
# Follow these 3 Cells sequentially in your Google Colab Notebook.

# ==============================================================================
# CELL 1: INSTALL AND SETUP (Run this first)
# ==============================================================================
# We need a special library to handle your data balance issues
# !pip install imbalanced-learn 

import json
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import joblib

# Machine Learning Libraries
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.pipeline import make_pipeline
from imblearn.over_sampling import SMOTE

# Load Data Function
def load_data(filename):
    try:
        with open(filename, 'r', encoding='utf-16') as f:
            return pd.json_normalize(json.load(f))
    except:
        print(f"❌ Error: Please upload '{filename}' to Colab Files first!")
        return None

print("✅ Setup Complete. Please upload your 2 JSON files to Colab now.")


# ==============================================================================
# CELL 2: MODEL 1 - THREAT DEFENSE BRAIN (Input: Vital SIgns -> Output: Action)
# ==============================================================================
print("\n🤖 TRAINING MODEL 1: THREAT DEFENSE CORE")

# 1. READ DATA
df_threats = load_data('Automated Response System 2.json')

if df_threats is not None:
    # 2. PREPARE FEATURES (X) AND TARGET (y)
    # X = The vital signs the ESP32 sends
    X = df_threats[[
        'Heart Rate (bpm)', 'SpO2 Level (%)', 
        'Systolic Blood Pressure (mmHg)', 'Diastolic Blood Pressure (mmHg)', 
        'Body Temperature (°C)', 'Fall Detection'
    ]].fillna(0)
    
    # y = The decision we want the AI to make (ISOLATE vs MONITOR vs NO ACTION)
    y = df_threats['Response_Action']

    # 3. SPLIT DATA (80% for Training, 20% for Testing)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. FIX IMBALANCE (SMOTE)
    # This creates fake examples of "ISOLATE" so the model learns it better
    smote = SMOTE(random_state=42)
    X_train_bal, y_train_bal = smote.fit_resample(X_train, y_train)

    # 5. TRAIN MODEL (Gradient Boosting)
    defense_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
    defense_model.fit(X_train_bal, y_train_bal)
    print("✅ Defense Model Trained!")

    # 6. EVALUATE (Check Accuracy)
    preds = defense_model.predict(X_test)
    print(f"🏆 Accuracy: {accuracy_score(y_test, preds)*100:.2f}%")
    print("\n📝 Detailed Report:")
    print(classification_report(y_test, preds))

    # 7. VISUALIZE CONFUSION MATRIX
    plt.figure(figsize=(6,5))
    sns.heatmap(confusion_matrix(y_test, preds), annot=True, fmt='d', cmap='Blues')
    plt.title('Confusion Matrix (Defense Model)')
    plt.show()

    # 8. SAVE MODEL
    joblib.dump(defense_model, 'ars_defense_model.pkl')
    print("💾 Model saved as 'ars_defense_model.pkl'")


# ==============================================================================
# CELL 3: MODEL 2 - PRIVACY ENFORCER (Input: Text Log -> Output: Has PHI?)
# ==============================================================================
print("\n🔐 TRAINING MODEL 2: PRIVACY DETECTOR (PHI)")

# 1. READ DATA
df_logs = load_data('Automated Response System 1.json')

if df_logs is not None:
    # 2. PREPARE DATA
    X_text = df_logs['Log_Text']
    y_phi = df_logs['Contains_Phi'].astype(int) # 1 = Yes, 0 = No

    # 3. SPLIT DATA
    X_train_t, X_test_t, y_train_t, y_test_t = train_test_split(X_text, y_phi, test_size=0.2, random_state=42)

    # 4. TRAIN MODEL (Pipeline: Convert Text to Numbers -> Naive Bayes Classifier)
    phi_model = make_pipeline(TfidfVectorizer(), MultinomialNB())
    phi_model.fit(X_train_t, y_train_t)
    print("✅ Privacy Model Trained!")

    # 5. EVALUATE
    preds_t = phi_model.predict(X_test_t)
    print(f"🏆 Accuracy: {accuracy_score(y_test_t, preds_t)*100:.2f}%")
    
    # 6. REAL PREDICTION TEST
    test_log = "Patient P-102 showing signs of fever."
    prediction = phi_model.predict([test_log])[0]
    result = "CONTAINS_PHI" if prediction == 1 else "SAFE"
    print(f"\n🧪 Test: '{test_log}' -> [{result}]")

    # 7. SAVE MODEL
    joblib.dump(phi_model, 'ars_phi_model.pkl')
    print("💾 Model saved as 'ars_phi_model.pkl'")

print("\n🎉 DONE! Please download both .pkl files from the Files tab.")
