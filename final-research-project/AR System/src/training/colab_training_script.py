import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# ==========================================
# DATASET 1: IoT Network Intrusion Detection
# Purpose: Detect attacks on ESP32 (MQTT/Wifi)
# ==========================================
print("--- [1/2] Training IoT Network Threat Detection Model ---")

# 1.1 Generate Synthetic Traffic Data
# Features: Packet Size, Time Interval, Error Rate, Protocol (0=MQTT, 1=HTTP)
n_samples = 5000
rng = np.random.RandomState(42)

# Normal Traffic (Regular intervals, small packets)
X_normal = pd.DataFrame({
    'packet_size': rng.normal(100, 20, n_samples),   # Small MQTT packets
    'time_delta': rng.normal(1.0, 0.1, n_samples),   # 1 second intervals
    'error_rate': rng.uniform(0, 0.05, n_samples),   # Low errors
    'protocol': rng.choice([0, 0, 0, 1], n_samples)  # Mostly MQTT
})
y_normal = np.zeros(n_samples) # Label 0 = Normal

# Attack Traffic (DDoS/Flooding: Fast intervals, erratics)
X_attack = pd.DataFrame({
    'packet_size': rng.normal(500, 100, n_samples),  # Large payloads
    'time_delta': rng.exponential(0.01, n_samples),  # Fast flooding
    'error_rate': rng.uniform(0.1, 0.5, n_samples),  # High errors
    'protocol': rng.choice([0, 1], n_samples)
})
y_attack = np.ones(n_samples) # Label 1 = Attack

# Combine
X_net = pd.concat([X_normal, X_attack])
y_net = np.concatenate([y_normal, y_attack])

# 1.2 Train Model (Random Forest)
X_train, X_test, y_train, y_test = train_test_split(X_net, y_net, test_size=0.2)
net_model = RandomForestClassifier(n_estimators=100)
net_model.fit(X_train, y_train)

# 1.3 Validate
preds = net_model.predict(X_test)
print(f"Network Model Accuracy: {accuracy_score(y_test, preds)*100:.2f}%")
print(classification_report(y_test, preds, target_names=['Normal', 'Attack']))


# ==========================================
# DATASET 2: Biometric Anomaly Detection (AICE)
# Purpose: Detect Spoofed Data vs Real Patient Crisis
# ==========================================
print("\n--- [2/2] Training Biometric Anomaly Detection (AICE) ---")

# 2.1 Generate Synthetic Heart Rate Data
# We use Isolation Forest for anomaly detection (Unsupervised)
n_bio = 3000

# Normal Patient (HR 60-100, SpO2 95-100)
X_patient = pd.DataFrame({
    'heart_rate': rng.normal(75, 10, n_bio),
    'spo2': rng.normal(98, 1, n_bio),
    'acceleration': rng.normal(0, 0.1, n_bio) # Sitting still
})

# Suspicious/Spoofed Data (Impossible values or flatlines)
X_spoof = pd.DataFrame({
    'heart_rate': rng.normal(200, 50, 100),    # Impossible HR
    'spo2': rng.normal(50, 10, 100),           # Dead?
    'acceleration': rng.normal(5, 2, 100)      # Violent shaking
})

# 2.2 Train Model (Isolation Forest - detects outliers)
bio_model = IsolationForest(contamination=0.04) # Expect ~4% anomalies
bio_model.fit(X_patient)

# 2.3 Test on mixed data
X_test_bio = pd.concat([X_patient[:50], X_spoof[:50]])
bio_preds = bio_model.predict(X_test_bio)
# Isolation Forest returns -1 for outlier, 1 for normal

print(f"Anomalies Detected in Test Batch: {list(bio_preds).count(-1)} / {len(bio_preds)}")
print("(-1 indicates Threat/Anomaly, 1 indicates Normal)")
