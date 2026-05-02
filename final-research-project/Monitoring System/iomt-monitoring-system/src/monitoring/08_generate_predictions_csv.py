"""
Script 08: Generate Detailed Predictions CSV
Creates a comprehensive CSV file with all predictions after model training
Saves to data/processed/ folder for easy access
"""

import pandas as pd
import pickle
from datetime import datetime
import os

print("="*75)
print("📊 GENERATING DETAILED PREDICTIONS CSV")
print("="*75)

# Create output directory if it doesn't exist
os.makedirs('../../data/processed', exist_ok=True)

# Load model and data
print("\n🔄 Loading model and data...")

# Load trained model
with open('../../models/alert_prioritization_model.pkl', 'rb') as f:
    model = pickle.load(f)
print("   ✅ Model loaded")

# Load test data
X_test = pd.read_csv('../../data/processed/X_test.csv')
y_test = pd.read_csv('../../data/processed/y_test.csv').values.ravel()
print(f"   ✅ Test data loaded ({len(X_test):,} samples)")

# Load original dataset to get device details
df_original = pd.read_csv('../../data/raw/esp32_iomt_dataset_realistic.csv')
print("   ✅ Original dataset loaded")

# Make predictions
print("\n🔮 Making predictions on test set...")
y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)

# Get confidence scores for each prediction
confidence_scores = []
for proba in y_pred_proba:
    confidence_scores.append(max(proba))

print(f"   ✅ Predictions complete")

# Create results DataFrame
print("\n📦 Creating detailed output DataFrame...")

# Get test sample indices (take last samples as test set)
test_indices = df_original.tail(len(X_test)).index

# Extract relevant columns from original data
results_df = df_original.loc[test_indices].copy()

# Add prediction columns
results_df['predicted_priority'] = y_pred
results_df['actual_priority'] = y_test
results_df['confidence_score'] = [f"{conf:.6f}" for conf in confidence_scores]
results_df['prediction_correct'] = (y_pred == y_test).astype(int)
results_df['match_status'] = results_df['prediction_correct'].apply(
    lambda x: 'CORRECT' if x == 1 else 'INCORRECT'
)

# Reorder columns for better readability
output_columns = [
    'timestamp',
    'alert_id',
    'device_id',
    'device_type',
    'ward',
    'criticality_tier',
    'life_support',
    'src_ip',
    'dst_ip',
    'src_port',
    'dst_port',
    'protocol',
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
    'attack_type',
    'attack_severity',
    'network_anomaly_score',
    'behavioral_anomaly_score',
    'time_anomaly_score',
    'group_id',
    'campaign_id',
    'actual_priority',           # Ground truth
    'predicted_priority',        # Model prediction
    'confidence_score',          # Prediction confidence
    'prediction_correct',        # 1 if correct, 0 if wrong
    'match_status'               # CORRECT or INCORRECT
]

# Ensure all columns exist
for col in output_columns:
    if col not in results_df.columns:
        results_df[col] = None

# Select and reorder columns
output_df = results_df[output_columns].copy()

# Reset index
output_df.reset_index(drop=True, inplace=True)

# Save to data/processed/ folder
print("\n💾 Saving predictions to data/processed/ folder...")

# Main predictions file
predictions_path = '../../data/processed/predictions_with_results.csv'
output_df.to_csv(predictions_path, index=False)
print(f"   ✅ Saved: {predictions_path}")
print(f"   📊 Total predictions: {len(output_df):,}")

# Calculate summary statistics
print("\n📊 Generating prediction summary...")
summary = {
    'total_predictions': len(output_df),
    'correct_predictions': (output_df['prediction_correct'] == 1).sum(),
    'incorrect_predictions': (output_df['prediction_correct'] == 0).sum(),
    'accuracy': (output_df['prediction_correct'] == 1).sum() / len(output_df) * 100
}

print(f"\n   Total Predictions:     {summary['total_predictions']:,}")
print(f"   Correct Predictions:   {summary['correct_predictions']:,}")
print(f"   Incorrect Predictions: {summary['incorrect_predictions']:,}")
print(f"   Accuracy:              {summary['accuracy']:.2f}%")

# Priority-wise breakdown
print("\n📊 Priority-wise Prediction Accuracy:")
print(f"   {'Priority':<12} {'Correct':<10} {'Total':<10} {'Accuracy':<10}")
print(f"   {'-'*45}")
for priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
    priority_mask = output_df['actual_priority'] == priority
    if priority_mask.sum() > 0:
        correct = ((output_df['actual_priority'] == priority) & 
                   (output_df['predicted_priority'] == priority)).sum()
        total = priority_mask.sum()
        accuracy = correct / total * 100
        print(f"   {priority:<12} {correct:<10,} {total:<10,} {accuracy:>6.2f}%")

# Save misclassifications separately
print("\n❌ Extracting misclassifications...")
misclassified = output_df[output_df['prediction_correct'] == 0].copy()
misclassified_path = '../../data/processed/misclassified_predictions.csv'
misclassified.to_csv(misclassified_path, index=False)
print(f"   ✅ Saved: {misclassified_path}")
print(f"   📊 Misclassifications: {len(misclassified):,}")

# Save only correct predictions
print("\n✅ Extracting correct predictions...")
correct_preds = output_df[output_df['prediction_correct'] == 1].copy()
correct_path = '../../data/processed/correct_predictions.csv'
correct_preds.to_csv(correct_path, index=False)
print(f"   ✅ Saved: {correct_path}")
print(f"   📊 Correct predictions: {len(correct_preds):,}")

# Display sample of output
print("\n👀 Sample Output (first 10 rows):")
sample_cols = ['alert_id', 'device_id', 'ward', 'attack_type', 
               'actual_priority', 'predicted_priority', 'match_status']
print(output_df[sample_cols].head(10).to_string(index=False))

# Create a detailed statistics file
print("\n📊 Creating detailed statistics report...")
stats_lines = []
stats_lines.append("="*75)
stats_lines.append("DETAILED PREDICTION STATISTICS REPORT")
stats_lines.append("="*75)
stats_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
stats_lines.append(f"Model: Random Forest Classifier")
stats_lines.append(f"Dataset: ESP32 IoMT Realistic Dataset")
stats_lines.append(f"Output Location: data/processed/")
stats_lines.append(f"\n{'='*75}")
stats_lines.append("OVERALL PERFORMANCE")
stats_lines.append(f"{'='*75}")
stats_lines.append(f"Total Test Samples:       {summary['total_predictions']:,}")
stats_lines.append(f"Correct Predictions:      {summary['correct_predictions']:,}")
stats_lines.append(f"Incorrect Predictions:    {summary['incorrect_predictions']:,}")
stats_lines.append(f"Overall Accuracy:         {summary['accuracy']:.2f}%")

stats_lines.append(f"\n{'='*75}")
stats_lines.append("PRIORITY-WISE ACCURACY")
stats_lines.append(f"{'='*75}")
for priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
    priority_mask = output_df['actual_priority'] == priority
    if priority_mask.sum() > 0:
        correct = ((output_df['actual_priority'] == priority) & 
                   (output_df['predicted_priority'] == priority)).sum()
        total = priority_mask.sum()
        accuracy = correct / total * 100
        stats_lines.append(f"{priority:10} : {correct:5,} / {total:5,} ({accuracy:5.2f}%)")

stats_lines.append(f"\n{'='*75}")
stats_lines.append("DEVICE TYPE PERFORMANCE")
stats_lines.append(f"{'='*75}")
for device_type in sorted(output_df['device_type'].unique()):
    device_mask = output_df['device_type'] == device_type
    if device_mask.sum() > 0:
        correct = (output_df[device_mask]['prediction_correct'] == 1).sum()
        total = device_mask.sum()
        accuracy = correct / total * 100
        stats_lines.append(f"{device_type:30} : {correct:4,} / {total:4,} ({accuracy:5.2f}%)")

stats_lines.append(f"\n{'='*75}")
stats_lines.append("WARD-WISE PERFORMANCE")
stats_lines.append(f"{'='*75}")
for ward in sorted(output_df['ward'].unique()):
    ward_mask = output_df['ward'] == ward
    if ward_mask.sum() > 0:
        correct = (output_df[ward_mask]['prediction_correct'] == 1).sum()
        total = ward_mask.sum()
        accuracy = correct / total * 100
        stats_lines.append(f"{ward:20} : {correct:4,} / {total:4,} ({accuracy:5.2f}%)")

stats_lines.append(f"\n{'='*75}")
stats_lines.append("ATTACK TYPE PERFORMANCE")
stats_lines.append(f"{'='*75}")
for attack in sorted(output_df['attack_type'].unique()):
    attack_mask = output_df['attack_type'] == attack
    if attack_mask.sum() > 0:
        correct = (output_df[attack_mask]['prediction_correct'] == 1).sum()
        total = attack_mask.sum()
        accuracy = correct / total * 100
        stats_lines.append(f"{attack:20} : {correct:4,} / {total:4,} ({accuracy:5.2f}%)")

stats_lines.append(f"\n{'='*75}")
stats_lines.append("FILE LOCATIONS")
stats_lines.append(f"{'='*75}")
stats_lines.append(f"All Predictions:          {predictions_path}")
stats_lines.append(f"Correct Only:             {correct_path}")
stats_lines.append(f"Misclassified Only:       {misclassified_path}")

# Save statistics report
stats_path = '../../data/processed/prediction_statistics.txt'
with open(stats_path, 'w') as f:
    f.write('\n'.join(stats_lines))
print(f"   ✅ Saved: {stats_path}")

print("\n" + "="*75)
print("✅ DETAILED PREDICTIONS CSV GENERATION COMPLETE!")
print("="*75)
print(f"\n📁 Output Files in data/processed/:")
print(f"\n   1. predictions_with_results.csv")
print(f"      → All predictions with results ({len(output_df):,} rows)")
print(f"\n   2. correct_predictions.csv")
print(f"      → Correct predictions only ({len(correct_preds):,} rows)")
print(f"\n   3. misclassified_predictions.csv")
print(f"      → Misclassified samples only ({len(misclassified):,} rows)")
print(f"\n   4. prediction_statistics.txt")
print(f"      → Detailed statistics report")
print(f"\n🎯 Overall Accuracy: {summary['accuracy']:.2f}%")
print(f"📊 Open the CSV files in Excel or VS Code to view!\n")