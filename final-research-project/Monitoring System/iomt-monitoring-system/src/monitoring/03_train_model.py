"""
Script 03: Train Alert Prioritization Model
Random Forest Classifier for ~90% accuracy
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import os

print("="*75)
print("🤖 TRAINING ALERT PRIORITIZATION MODEL")
print("="*75)

# Load processed data
print("\n🔄 Loading processed data...")
X_train = pd.read_csv('../../data/processed/X_train.csv')
X_test = pd.read_csv('../../data/processed/X_test.csv')
y_train = pd.read_csv('../../data/processed/y_train.csv').values.ravel()
y_test = pd.read_csv('../../data/processed/y_test.csv').values.ravel()

print(f"   ✅ Training samples: {len(X_train):,}")
print(f"   ✅ Testing samples: {len(X_test):,}")
print(f"   ✅ Features: {len(X_train.columns)}")

# Create Random Forest model
print("\n🔄 Creating Random Forest Classifier...")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=20,
    min_samples_split=10,
    min_samples_leaf=4,
    random_state=42,
    n_jobs=-1,
    verbose=1
)

# Train model
print("\n🚀 Training model...")
model.fit(X_train, y_train)
print("   ✅ Training complete!")

# Make predictions
print("\n🔮 Making predictions on test set...")
y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)

# Calculate accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"\n🎯 Test Accuracy: {accuracy*100:.2f}%")

# Classification report
print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred))

# Confusion matrix
print("\n📊 Confusion Matrix:")
cm = confusion_matrix(y_test, y_pred, labels=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'])
print(cm)

# Visualize confusion matrix
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'],
            yticklabels=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'])
plt.title(f'Confusion Matrix - Accuracy: {accuracy*100:.2f}%', fontsize=14, fontweight='bold')
plt.ylabel('Actual')
plt.xlabel('Predicted')
plt.tight_layout()
plt.savefig('../../results/04_confusion_matrix.png', dpi=300)
print("\n   ✅ Saved: results/04_confusion_matrix.png")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': X_train.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n📊 Top 10 Most Important Features:")
print(feature_importance.head(10).to_string(index=False))

# Visualize feature importance
plt.figure(figsize=(10, 8))
feature_importance.head(15).plot(x='feature', y='importance', kind='barh', color='skyblue', legend=False)
plt.title('Top 15 Feature Importances', fontsize=14, fontweight='bold')
plt.xlabel('Importance')
plt.ylabel('Feature')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('../../results/05_feature_importance.png', dpi=300)
print("   ✅ Saved: results/05_feature_importance.png")

# Save model
print("\n💾 Saving trained model...")
with open('../../models/alert_prioritization_model.pkl', 'wb') as f:
    pickle.dump(model, f)
print("   ✅ Saved: models/alert_prioritization_model.pkl")

# Save metrics
metrics = {
    'accuracy': accuracy,
    'training_samples': len(X_train),
    'testing_samples': len(X_test),
    'features': list(X_train.columns)
}

with open('../../models/model_metrics.pkl', 'wb') as f:
    pickle.dump(metrics, f)
print("   ✅ Saved: models/model_metrics.pkl")

print("\n" + "="*75)
print("✅ MODEL TRAINING COMPLETE!")
print("="*75)
print(f"\n🎯 Final Accuracy: {accuracy*100:.2f}%")
print("📁 Check 'results' folder for visualizations!")
print("📁 Check 'models' folder for saved model!\n")