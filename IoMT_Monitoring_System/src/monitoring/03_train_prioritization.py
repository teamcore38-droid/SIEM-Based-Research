"""
SCRIPT 03 — Train Alert Prioritization Model (Novelty 1)
IoMT Monitoring System | MMM Ukasha IT22904232

What this does:
  - Loads X_train / X_test / y_train / y_test
  - Trains Random Forest Classifier with class_weight='balanced'
    (balanced is CRITICAL because ICU/CRITICAL rows are fewer)
  - Evaluates: accuracy, confusion matrix, F1 per class
  - Shows feature importance (what drives priority decision)
  - Saves trained model → models/alert_prioritization_model.pkl
  - Saves confusion matrix and feature importance charts → results/
"""

import pandas as pd
import numpy as np
import os
import pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (classification_report, confusion_matrix,
                              accuracy_score)

print("=" * 65)
print("  SCRIPT 03 — TRAIN ALERT PRIORITIZATION MODEL (NOVELTY 1)")
print("=" * 65)

# ── Paths ────────────────────────────────────────────────────────
BASE      = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROC_DIR  = os.path.join(BASE, "data", "processed")
MODEL_DIR = os.path.join(BASE, "models")
RES_DIR   = os.path.join(BASE, "results")
os.makedirs(RES_DIR, exist_ok=True)

# ── Load data ─────────────────────────────────────────────────────
X_train = pd.read_csv(os.path.join(PROC_DIR, "X_train.csv"))
X_test  = pd.read_csv(os.path.join(PROC_DIR, "X_test.csv"))
y_train = pd.read_csv(os.path.join(PROC_DIR, "y_train.csv")).values.ravel()
y_test  = pd.read_csv(os.path.join(PROC_DIR, "y_test.csv")).values.ravel()

print(f"\n  Train: {len(X_train)} | Test: {len(X_test)} | Features: {len(X_train.columns)}")

# ── Train model ───────────────────────────────────────────────────
print("\n  Training Random Forest Classifier...")
print("  (class_weight=balanced — ensures CRITICAL alerts are not ignored)")

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=20,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight="balanced",   # KEY: treats CRITICAL equally despite fewer rows
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)
print("  Training complete!")

# ── Evaluate ──────────────────────────────────────────────────────
y_pred   = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
report   = classification_report(y_test, y_pred, digits=4)
cm       = confusion_matrix(y_test, y_pred,
               labels=["CRITICAL", "HIGH", "MEDIUM", "LOW"])

print(f"\n  Overall Accuracy: {accuracy*100:.2f}%")
print("\n  Classification Report:")
print(report)

# ── Chart 1: Confusion Matrix ─────────────────────────────────────
labels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
fig, ax = plt.subplots(figsize=(7, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=labels, yticklabels=labels, ax=ax)
ax.set_title("Alert Prioritization — Confusion Matrix\n(IoMT Monitoring System | Ukasha IT22904232)",
             fontsize=11, fontweight="bold")
ax.set_xlabel("Predicted Priority"); ax.set_ylabel("Actual Priority")
plt.tight_layout()
plt.savefig(os.path.join(RES_DIR, "03_confusion_matrix.png"), dpi=150)
plt.close()
print("  Saved → results/03_confusion_matrix.png")

# ── Chart 2: Feature Importance ───────────────────────────────────
importances = model.feature_importances_
feat_df = pd.DataFrame({
    "feature": X_train.columns,
    "importance": importances
}).sort_values("importance", ascending=False)

fig, ax = plt.subplots(figsize=(8, 5))
colors = ["#d62728" if i == 0 else "#1f77b4" for i in range(len(feat_df))]
ax.barh(feat_df["feature"][::-1], feat_df["importance"][::-1], color=colors[::-1])
ax.set_title("Feature Importance — What Drives Priority?\n(Alert Prioritization Model)",
             fontsize=11, fontweight="bold")
ax.set_xlabel("Importance Score")
plt.tight_layout()
plt.savefig(os.path.join(RES_DIR, "04_feature_importance.png"), dpi=150)
plt.close()
print("  Saved → results/04_feature_importance.png")

# ── Chart 3: Priority Distribution (Actual vs Predicted) ──────────
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
colors_map = {"CRITICAL":"#d62728","HIGH":"#ff7f0e","MEDIUM":"#2ca02c","LOW":"#1f77b4"}

pd.Series(y_test).value_counts().reindex(order).plot(
    kind="bar", ax=axes[0], color=[colors_map[l] for l in order], edgecolor="black")
axes[0].set_title("Actual Priority Labels"); axes[0].set_xlabel(""); axes[0].tick_params(rotation=0)

pd.Series(y_pred).value_counts().reindex(order).plot(
    kind="bar", ax=axes[1], color=[colors_map[l] for l in order], edgecolor="black")
axes[1].set_title("Predicted Priority Labels"); axes[1].set_xlabel(""); axes[1].tick_params(rotation=0)

plt.suptitle("Alert Prioritization — Actual vs Predicted Distribution",
             fontsize=12, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(RES_DIR, "05_priority_comparison.png"), dpi=150)
plt.close()
print("  Saved → results/05_priority_comparison.png")

# ── Save model ────────────────────────────────────────────────────
with open(os.path.join(MODEL_DIR, "alert_prioritization_model.pkl"), "wb") as f:
    pickle.dump(model, f)

metrics = {"accuracy": accuracy, "report": report, "feature_importance": feat_df}
with open(os.path.join(MODEL_DIR, "model_metrics.pkl"), "wb") as f:
    pickle.dump(metrics, f)

# ── Save text summary ──────────────────────────────────────────────
with open(os.path.join(RES_DIR, "03_model_training_summary.txt"), "w") as f:
    f.write("IoMT Alert Prioritization Model — Training Summary\n")
    f.write("Student: MMM Ukasha  IT22904232\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Overall Accuracy: {accuracy*100:.2f}%\n\n")
    f.write("Classification Report:\n")
    f.write(report)
    f.write("\nTop Feature Importances:\n")
    f.write(feat_df.to_string(index=False))

print("\n  Saved → models/alert_prioritization_model.pkl")
print("  Saved → models/model_metrics.pkl")
print("  Saved → results/03_model_training_summary.txt")
print(f"\n  🎯  MODEL ACCURACY: {accuracy*100:.2f}%")
print("\n  ✅  SCRIPT 03 COMPLETE — Run 04_alert_grouping.py next")
print("=" * 65)