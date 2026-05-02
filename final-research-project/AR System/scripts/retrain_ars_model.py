"""
MedGuard-X | Retrain ARS Response Model
=========================================
Retrains the ARS automated response model using correlated_full_dataset.csv
which contains real device detection results, grouped alerts & incidents.

Target: Predict action_taken (PERMANENT QUARANTINE / TEMPORARY ISOLATION / MONITORING / NO_ACTION)
Features: classification, priority_label, is_attack, anomaly_flag, attack_type, data_source

Saves to: models/ars_response_model_v2.pkl
"""
import os
import pickle
import warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")

print("=" * 60)
print("  MedGuard-X | ARS Response Model Retraining")
print("=" * 60)

# -----------------------------------------------------------------------
# 1. LOAD CORRELATED DATASET
# -----------------------------------------------------------------------
df = pd.read_csv(os.path.join(DATA_DIR, "correlated_full_dataset.csv"))
print(f"\n[1] Loaded correlated dataset: {len(df)} rows, {len(df.columns)} columns")
print(f"    Columns: {df.columns.tolist()}")

# -----------------------------------------------------------------------
# 2. FEATURE ENGINEERING
# -----------------------------------------------------------------------
print("\n[2] Feature Engineering...")

# Fill missing values
df['classification'] = df['classification'].fillna('BENIGN')
df['priority_label'] = df['priority_label'].fillna('LOW')
df['action_taken'] = df['action_taken'].fillna('NO_ACTION')
df['is_attack'] = df['is_attack'].fillna(0)
df['anomaly_flag'] = df['anomaly_flag'].fillna(0)
df['attack_type'] = df['attack_type'].fillna('normal')
df['data_source'] = df['data_source'].fillna('unknown')
df['ai_prediction'] = df['ai_prediction'].fillna('BENIGN')

# Encode categorical features
label_encoders = {}

cat_features = ['classification', 'priority_label', 'data_source', 'ai_prediction', 'attack_type']
for col in cat_features:
    le = LabelEncoder()
    df[col + '_enc'] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = le
    print(f"    Encoded '{col}': {list(le.classes_)}")

# Encode target
target_le = LabelEncoder()
df['action_enc'] = target_le.fit_transform(df['action_taken'].astype(str))
label_encoders['action_taken'] = target_le
print(f"\n    TARGET 'action_taken': {list(target_le.classes_)}")

# Feature columns
feature_cols = ['classification_enc', 'priority_label_enc', 'data_source_enc',
                'ai_prediction_enc', 'attack_type_enc', 'is_attack', 'anomaly_flag']

# Handle is_attack: convert booleans to int
df['is_attack'] = df['is_attack'].apply(lambda x: 1 if x == True or x == 1 else (0 if x == False or x == 0 else -1))
df['anomaly_flag'] = df['anomaly_flag'].fillna(0).astype(int)

X = df[feature_cols].values
y = df['action_enc'].values

print(f"\n    Feature matrix: {X.shape}")
print(f"    Target distribution:")
for cls_name, cls_enc in zip(target_le.classes_, range(len(target_le.classes_))):
    count = (y == cls_enc).sum()
    print(f"      {cls_name}: {count} ({count/len(y)*100:.1f}%)")

# -----------------------------------------------------------------------
# 3. TRAIN / TEST SPLIT
# -----------------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"\n[3] Train/Test split: {len(X_train)} train, {len(X_test)} test")

# -----------------------------------------------------------------------
# 4. TRAIN MODEL (RandomForest + GradientBoosting, pick best)
# -----------------------------------------------------------------------
print("\n[4] Training models...")

models = {
    'RandomForest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1),
    'GradientBoosting': GradientBoostingClassifier(n_estimators=200, max_depth=5, learning_rate=0.1, random_state=42),
}

best_model = None
best_score = 0
best_name = None

for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    
    print(f"\n  {name}:")
    print(f"    Test Accuracy: {acc:.4f}")
    print(f"    CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    print(f"    Classification Report:")
    report = classification_report(y_test, y_pred, target_names=target_le.classes_, output_dict=False)
    for line in report.split('\n'):
        print(f"      {line}")
    
    if acc > best_score:
        best_score = acc
        best_model = model
        best_name = name

print(f"\n  BEST MODEL: {best_name} (Accuracy: {best_score:.4f})")

# -----------------------------------------------------------------------
# 5. SAVE RETRAINED MODEL
# -----------------------------------------------------------------------
print("\n[5] Saving retrained model...")

output = {
    'model': best_model,
    'label_encoders': label_encoders,
    'feature_cols': feature_cols,
    'target_encoder': target_le,
    'model_name': best_name,
    'accuracy': best_score,
    'action_classes': list(target_le.classes_),
    'version': 'v2_correlated',
}

# Save as v2
v2_path = os.path.join(MODELS_DIR, 'ars_response_model_v2.pkl')
with open(v2_path, 'wb') as f:
    pickle.dump(output, f)
print(f"    Saved: {v2_path}")

# Also overwrite original
orig_path = os.path.join(MODELS_DIR, 'ars_response_model.pkl')
with open(orig_path, 'wb') as f:
    pickle.dump(output, f)
print(f"    Updated: {orig_path}")

print(f"\n{'='*60}")
print(f"  RETRAINING COMPLETE")
print(f"  Model: {best_name} | Accuracy: {best_score:.4f}")
print(f"  Actions: {list(target_le.classes_)}")
print(f"{'='*60}")
