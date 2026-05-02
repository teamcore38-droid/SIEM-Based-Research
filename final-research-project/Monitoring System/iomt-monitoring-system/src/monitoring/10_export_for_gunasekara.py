"""
Export HIGH + CRITICAL alerts for Automated Response System
"""

import pandas as pd

# Load all predictions
df = pd.read_csv('../../data/processed/predictions_with_results.csv')

# Filter for HIGH and CRITICAL only
high_critical = df[df['predicted_priority'].isin(['HIGH', 'CRITICAL'])].copy()

# Save for Gunasekara
output_path = '../../data/processed/alerts_for_response_system.csv'
high_critical.to_csv(output_path, index=False)

print(f"✅ Exported {len(high_critical):,} HIGH/CRITICAL alerts")
print(f"📁 Saved: {output_path}")

# Summary
print(f"\nBreakdown:")
print(f"  CRITICAL: {(high_critical['predicted_priority'] == 'CRITICAL').sum():,}")
print(f"  HIGH:     {(high_critical['predicted_priority'] == 'HIGH').sum():,}")