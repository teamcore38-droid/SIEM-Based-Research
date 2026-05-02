import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# 1. Load the High-Fidelity Data
data_path = "../../data/ars_high_fidelity_training.csv"
print(f"📂 Loading Dataset: {data_path}")

try:
    df = pd.read_csv(data_path)
except FileNotFoundError:
    print("[ERROR] Error: Dataset not found. Please run generate_high_fidelity.py first.")
    exit()

# 2. Preprocessing
# We need to drop non-numeric columns like 'threat_type' if we aren't encoding them, 
# BUT for High Accuracy, 'anomaly_score' + 'network_latency' + 'vitals' are usually enough.
# Let's drop 'threat_type' for simplicity as it maps 1:1 to Action usually.
X = df.drop(columns=['ACTION_LABEL', 'threat_type'])
y = df['ACTION_LABEL']

# 3. Split Data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Train Random Forest (The 'Golden' Standard for this tabular data)
print("🧠 Training Random Forest Model...")
clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
clf.fit(X_train, y_train)

# 5. Evaluate
y_pred = clf.predict(X_test)
accuracy = accuracy_score(y_test, y_pred) * 100

print("\n" + "="*50)
print(f"🎯 MODEL ACCURACY: {accuracy:.2f}%")
print("="*50)

if accuracy > 95:
    print("✅ SUCCESS: Accuracy Goal Met (>95%)")
else:
    print("⚠️ WARNING: Accuracy is below target. Check feature separation.")

print("\n📊 Detailed Report:")
print(classification_report(y_test, y_pred))

# 6. Save Model
model_dir = "../../models"
if not os.path.exists(model_dir):
    os.makedirs(model_dir)

model_path = os.path.join(model_dir, 'ars_decision_model_final.pkl')
joblib.dump(clf, model_path)
print(f"💾 Model Saved to: {model_path}")
print("🚀 You can now restart your main ARS system to use this High-Accuracy brain.")
