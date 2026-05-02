"""
SCRIPT 02 — Preprocess
IoMT Monitoring System | MMM Ukasha IT22904232

What this does:
  - Loads master_dataset.csv
  - Encodes categorical columns
  - Engineers new features
  - Splits into train (80%) / test (20%)
  - Saves X_train, X_test, y_train, y_test
  - Saves label encoders for later use
"""

import pandas as pd
import numpy as np
import os
import pickle
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

print("=" * 65)
print("  SCRIPT 02 — PREPROCESS DATA")
print("=" * 65)

# ── Paths ────────────────────────────────────────────────────────
BASE      = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_PATH  = os.path.join(BASE, "data", "raw",       "master_dataset.csv")
PROC_DIR  = os.path.join(BASE, "data", "processed")
MODEL_DIR = os.path.join(BASE, "models")
os.makedirs(PROC_DIR,  exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# ── Load ─────────────────────────────────────────────────────────
df = pd.read_csv(RAW_PATH)
print(f"\n  Loaded master_dataset.csv: {len(df)} rows, {len(df.columns)} columns")

# ── Encode binary columns ─────────────────────────────────────────
df["life_support_int"] = (df["life_support"].astype(str).str.upper() == "TRUE").astype(int)
df["is_attack_int"]    = (df["is_attack"].astype(str).str.upper()    == "TRUE").astype(int)

# ── Label encode categoricals ─────────────────────────────────────
label_encoders = {}
cat_cols = ["device_type", "ward", "protocol", "attack_type", "sensor_source"]

for col in cat_cols:
    le = LabelEncoder()
    df[col + "_enc"] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = le
    print(f"  Encoded {col}: {list(le.classes_)}")

# ── Engineer features ─────────────────────────────────────────────
df["is_icu"]              = (df["ward"] == "ICU").astype(int)
df["is_port_anomaly"]     = (df["dst_port"] != 1883).astype(int)
df["is_unknown_device"]   = df["device_id"].str.contains(
                                "UNKNOWN|ROGUE|FAKE|GHOST|CLONE", case=False, na=False
                            ).astype(int)
df["is_protocol_anomaly"] = (~df["protocol"].isin(["MQTT","BLE_MQTT"])).astype(int)

print(f"\n  Engineered 4 new features: is_icu, is_port_anomaly, is_unknown_device, is_protocol_anomaly")

# ── Select feature columns ────────────────────────────────────────
FEATURES = [
    "criticality_tier",
    "life_support_int",
    "is_attack_int",
    "dst_port",
    "device_type_enc",
    "ward_enc",
    "protocol_enc",
    "attack_type_enc",
    "sensor_source_enc",
    "is_icu",
    "is_port_anomaly",
    "is_unknown_device",
    "is_protocol_anomaly",
]
TARGET = "priority_label"

X = df[FEATURES]
y = df[TARGET]

print(f"\n  Features selected: {len(FEATURES)}")
print(f"  Target: {TARGET}")
print(f"  Class distribution:\n{y.value_counts().to_string()}")

# ── Train / Test split ────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\n  Train: {len(X_train)} rows | Test: {len(X_test)} rows")

# ── Save splits ───────────────────────────────────────────────────
X_train.to_csv(os.path.join(PROC_DIR, "X_train.csv"), index=False)
X_test.to_csv( os.path.join(PROC_DIR, "X_test.csv"),  index=False)
y_train.to_csv(os.path.join(PROC_DIR, "y_train.csv"), index=False)
y_test.to_csv( os.path.join(PROC_DIR, "y_test.csv"),  index=False)

# ── Save label encoders ───────────────────────────────────────────
with open(os.path.join(MODEL_DIR, "label_encoders.pkl"), "wb") as f:
    pickle.dump(label_encoders, f)

with open(os.path.join(MODEL_DIR, "feature_names.pkl"), "wb") as f:
    pickle.dump(FEATURES, f)

print("\n  Saved files:")
print("    data/processed/X_train.csv")
print("    data/processed/X_test.csv")
print("    data/processed/y_train.csv")
print("    data/processed/y_test.csv")
print("    models/label_encoders.pkl")
print("    models/feature_names.pkl")
print("\n  ✅  SCRIPT 02 COMPLETE — Run 03_train_prioritization.py next")
print("=" * 65)