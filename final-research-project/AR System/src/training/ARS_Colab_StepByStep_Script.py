# --- CELL 1: SETUP ---
# Run this cell first to import libraries.
import json
import pandas as pd
import numpy as np
import pickle
from google.colab import files
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report

print("Setup Complete. Libraries Imported.")


# --- CELL 2: UPLOAD DATA ---
# Run this cell and click "Choose Files" to upload your 2 JSON files.
print("Please upload 'optimized_threat_triggers.json' and 'optimized_phi_logs.json'...")
uploaded = files.upload()

# Verify upload
if "optimized_threat_triggers.json" in uploaded and "optimized_phi_logs.json" in uploaded:
    print("Files uploaded successfully!")
    
    # Load into Pandas (The "Read" step)
    with open("optimized_threat_triggers.json", "r") as f:
        df_threats = pd.DataFrame(json.load(f))
        
    with open("optimized_phi_logs.json", "r") as f:
        df_phi = pd.DataFrame(json.load(f))
        
    print(f"Loaded Threats: {len(df_threats)} rows")
    print(f"Loaded PHI Logs: {len(df_phi)} rows")
else:
    print("ERROR: Missing files. Please re-run and upload both JSONs.")


# --- CELL 3: TRAIN RESPONSE MODEL ---
# This trains the logic for ISOLATE, MONITOR, etc.
print("\n--- Training Response Model ---")

# 1. Encoding (Text -> Numbers)
le_threat = LabelEncoder()
df_threats['threat_encoded'] = le_threat.fit_transform(df_threats['threat_type'])

severity_map = {"None": 0, "Low": 1, "Medium": 2, "High": 3, "Critical": 4}
df_threats['severity_encoded'] = df_threats['severity'].map(severity_map)

action_map = {"NO_ACTION": 0, "MONITOR": 1, "ISOLATE": 2, "ROLLBACK": 3}
df_threats['action_target'] = df_threats['action_required'].map(action_map)

# 2. Select Features
X_resp = df_threats[['threat_encoded', 'severity_encoded', 'confidence_score']]
y_resp = df_threats['action_target']

# 3. Train
X_train, X_test, y_train, y_test = train_test_split(X_resp, y_resp, test_size=0.2, random_state=42)
clf_resp = RandomForestClassifier(n_estimators=100, random_state=42)
clf_resp.fit(X_train, y_train)

# 4. Results
acc = accuracy_score(y_test, clf_resp.predict(X_test))
print(f"Response Model Accuracy: {acc*100:.2f}%")

# Save Bundle
resp_bundle = {
    "model": clf_resp,
    "le_threat": le_threat, 
    "action_map": action_map
}
with open('ars_response_model.pkl', 'wb') as f:
    pickle.dump(resp_bundle, f)
print("Saved: ars_response_model.pkl")


# --- CELL 4: TRAIN PHI MODEL ---
# This trains the privacy scanner (NLP).
print("\n--- Training PHI Scanner Model ---")

# 1. Vectorization (Text -> Numbers)
vectorizer = TfidfVectorizer(max_features=5000)
X_phi = vectorizer.fit_transform(df_phi['raw_log_message'].str.lower())
y_phi = df_phi['phi_label']

# 2. Train
X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(X_phi, y_phi, test_size=0.2, random_state=42)
clf_phi = RandomForestClassifier(n_estimators=50, random_state=42)
clf_phi.fit(X_train_p, y_train_p)

# 3. Results
acc_phi = accuracy_score(y_test_p, clf_phi.predict(X_test_p))
print(f"PHI Scanner Accuracy: {acc_phi*100:.2f}%")

# Save Bundle
phi_bundle = {
    "model": clf_phi,
    "vectorizer": vectorizer
}
with open('ars_phi_model.pkl', 'wb') as f:
    pickle.dump(phi_bundle, f)
print("Saved: ars_phi_model.pkl")


# --- CELL 5: DOWNLOAD ---
# Creates the download prompt for your PC.
print("\n--- Downloading Models ---")
files.download('ars_response_model.pkl')
files.download('ars_phi_model.pkl')
