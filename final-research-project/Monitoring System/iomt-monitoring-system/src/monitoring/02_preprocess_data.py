"""
Script 02: Data Preprocessing
Prepare data for machine learning
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle
import os

print("="*75)
print("🔧 DATA PREPROCESSING")
print("="*75)

# Create directories
os.makedirs('../../data/processed', exist_ok=True)
os.makedirs('../../models', exist_ok=True)

# Load dataset
print("\n🔄 Loading dataset...")
df = pd.read_csv('../../data/raw/esp32_iomt_dataset_realistic.csv')
print(f"✅ Loaded {len(df):,} samples")

# Handle categorical columns
print("\n🔄 Encoding categorical variables...")
label_encoders = {}

categorical_cols = ['device_type', 'ward', 'protocol', 'attack_type']

for col in categorical_cols:
    le = LabelEncoder()
    df[f'{col}_encoded'] = le.fit_transform(df[col])
    label_encoders[col] = le
    print(f"   ✅ Encoded: {col} ({len(le.classes_)} unique values)")

# Select features for ML
print("\n🔄 Selecting features...")

feature_columns = [
    'criticality_tier',
    'life_support',
    'device_type_encoded',
    'ward_encoded',
    'protocol_encoded',
    'packet_size',
    'packet_rate',
    'packets_per_sec',
    'unique_ports',
    'failed_connections',
    'bytes_sent',
    'bytes_received',
    'flow_duration',
    'hour_of_day',
    'day_of_week',
    'is_night',
    'is_weekend',
    'attack_type_encoded',
    'attack_severity',
    'network_anomaly_score',
    'behavioral_anomaly_score',
    'time_anomaly_score'
]

# Convert boolean to int
df['life_support'] = df['life_support'].astype(int)
df['is_night'] = df['is_night'].astype(int)
df['is_weekend'] = df['is_weekend'].astype(int)

X = df[feature_columns]
y = df['priority_label']

print(f"   ✅ Selected {len(feature_columns)} features")
print(f"   ✅ Target variable: priority_label")

# Train-test split
print("\n🔄 Splitting data (80% train, 20% test)...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"   ✅ Training set: {len(X_train):,} samples")
print(f"   ✅ Testing set: {len(X_test):,} samples")

# Save processed data
print("\n💾 Saving processed data...")
X_train.to_csv('../../data/processed/X_train.csv', index=False)
X_test.to_csv('../../data/processed/X_test.csv', index=False)
y_train.to_csv('../../data/processed/y_train.csv', index=False)
y_test.to_csv('../../data/processed/y_test.csv', index=False)

print("   ✅ Saved: X_train.csv")
print("   ✅ Saved: X_test.csv")
print("   ✅ Saved: y_train.csv")
print("   ✅ Saved: y_test.csv")

# Save label encoders
with open('../../models/label_encoders.pkl', 'wb') as f:
    pickle.dump(label_encoders, f)
print("   ✅ Saved: label_encoders.pkl")

# Save feature names
with open('../../models/feature_names.pkl', 'wb') as f:
    pickle.dump(feature_columns, f)
print("   ✅ Saved: feature_names.pkl")

# Display sample
print("\n👀 Sample of processed data:")
print(X_train.head())

print("\n" + "="*75)
print("✅ PREPROCESSING COMPLETE!")
print("="*75)
print("\n🎯 Data is ready for model training!\n")