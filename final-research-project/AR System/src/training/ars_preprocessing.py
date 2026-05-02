import json
import pandas as pd
import re
import string
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

# File Paths
THREAT_SOURCE = "optimized_threat_triggers.json"
PHI_SOURCE = "optimized_phi_logs.json"

THREAT_OUTPUT = "processed_threats.csv"
PHI_OUTPUT = "processed_phi.csv"

def preprocess_threat_data():
    print("--- Preprocessing Threat Response Data ---")
    
    # 1. Load Data
    try:
        with open(THREAT_SOURCE, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        print(f"Loaded {len(df)} records.")
    except FileNotFoundError:
        print(f"Error: {THREAT_SOURCE} not found. Please regenerate datasets first.")
        return

    # 2. Basic Cleaning
    # Drop identifying columns not needed for training logic (IPs, IDs are for action, not learning patterns)
    df_clean = df.drop(columns=['alert_id', 'target_ip', 'device_id', 'timestamp'])
    
    # 3. Encode Severity
    # Added "None" for normal traffic
    severity_map = {"None": 0, "Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    df_clean['severity_encoded'] = df_clean['severity'].map(severity_map)
    
    # 4. Encode Threat Type
    le_threat = LabelEncoder()
    df_clean['threat_encoded'] = le_threat.fit_transform(df_clean['threat_type'])
    
    # 5. Normalize Confidence Score
    scaler = MinMaxScaler()
    df_clean['confidence_scaled'] = scaler.fit_transform(df_clean[['confidence_score']])
    
    # 6. Encode Target Variable (4 Actions)
    # 0 = NO_ACTION, 1 = MONITOR, 2 = ISOLATE, 3 = ROLLBACK
    action_map = {
        "NO_ACTION": 0, 
        "MONITOR": 1, 
        "ISOLATE": 2, 
        "ROLLBACK": 3
    }
    df_clean['action_target'] = df_clean['action_required'].map(action_map)
    
    # Validation Check
    if df_clean['action_target'].isnull().any():
        print("Warning: Some actions were not mapped correctly!")
        print(df_clean[df_clean['action_target'].isnull()]['action_required'].unique())
    
    # Save Mapping for reference (so we know what 0 and 1 mean later)
    print(f"Severity Mapping: {severity_map}")
    print(f"Threat Mapping: {dict(zip(le_threat.classes_, le_threat.transform(le_threat.classes_)))}")
    
    # 7. Save to CSV
    df_clean.to_csv(THREAT_OUTPUT, index=False)
    print(f"Saved processed threat data to {THREAT_OUTPUT}")
    print(df_clean.head())


def preprocess_phi_data():
    print("\n--- Preprocessing PHI Detection Data ---")
    
    # 1. Load Data
    try:
        with open(PHI_SOURCE, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        print(f"Loaded {len(df)} records.")
    except FileNotFoundError:
        print(f"Error: {PHI_SOURCE} not found.")
        return

    # 2. Text Cleaning Function
    def clean_text(text):
        text = text.lower() # Lowercase
        text = re.sub(f"[{string.punctuation}]", "", text) # Remove punctuation
        return text

    # Apply cleaning
    df['clean_log'] = df['raw_log_message'].apply(clean_text)
    
    # 3. Encode Target (True/False -> 1/0)
    df['phi_label'] = df['phi_present'].astype(int)
    
    # 4. Select relevant columns
    df_final = df[['clean_log', 'phi_label']]
    
    # 5. Save to CSV
    df_final.to_csv(PHI_OUTPUT, index=False)
    print(f"Saved processed PHI data to {PHI_OUTPUT}")
    print(df_final.head())

if __name__ == "__main__":
    preprocess_threat_data()
    preprocess_phi_data()
