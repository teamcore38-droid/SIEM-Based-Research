import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

DATA_PATH = "X:/AI-TI/data/combined_dataset.csv"
df = pd.read_csv(DATA_PATH)

print("Dataset loaded:", df.shape)

# Remove same columns
df = df.drop(columns=["device_id", "attack_type", "src_ip"], errors='ignore')

# Load encoders
encoders = joblib.load("X:/AI-TI/models/encoders.pkl")

# Apply encoding
for column in encoders:
    if column in df.columns:
        df[column] = df[column].map(
            lambda x: encoders[column].transform([str(x)])[0]
            if str(x) in encoders[column].classes_ else -1
        )

# Select features
feature_cols = [
    "timestamp",
    "criticality_tier",
    "dst_port",
    "ecg_raw_value",
    "heart_rate_bpm",
    "accel_x",
    "accel_y",
    "accel_z",
    "gyro_x",
    "gyro_y",
    "gyro_z",
    "temperature_celsius"
]

X = df[feature_cols]

joblib.dump(feature_cols, "X:/AI-TI/models/iso_features.pkl")

model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
model.fit(X)

joblib.dump(model, "X:/AI-TI/models/isolation_forest_model.pkl")

print("Isolation Forest training completed")