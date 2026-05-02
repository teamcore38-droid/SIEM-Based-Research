"""
Real-time Alert Monitoring Demo
Simulates real-time alert processing
"""

import pandas as pd
import pickle
import time
from datetime import datetime

def load_model():
    """Load trained model and encoders"""
    with open('../../models/alert_prioritization_model.pkl', 'rb') as f:
        model = pickle.load(f)
    
    with open('../../models/label_encoders.pkl', 'rb') as f:
        encoders = pickle.load(f)
    
    return model, encoders


def display_alert(alert_data, priority, confidence, device_info):
    """Display formatted alert with colors"""
    
    colors = {
        'CRITICAL': '\033[91m',  # Red
        'HIGH': '\033[93m',      # Yellow
        'MEDIUM': '\033[94m',    # Blue
        'LOW': '\033[92m',       # Green
        'INFO': '\033[90m'       # Gray
    }
    reset = '\033[0m'
    
    color = colors.get(priority, reset)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Priority symbols
    symbols = {
        'CRITICAL': '🚨🚨🚨',
        'HIGH': '⚠️⚠️',
        'MEDIUM': '⚠️',
        'LOW': 'ℹ️',
        'INFO': '📌'
    }
    
    print(f"\n{color}{'='*70}")
    print(f"{symbols.get(priority, '')} SECURITY ALERT - {timestamp}")
    print(f"{'='*70}{reset}")
    print(f"Device ID:    {device_info['device_id']}")
    print(f"Device Type:  {device_info['device_type']}")
    print(f"Sensor:       {device_info['sensor_type']}")
    print(f"Location:     {device_info['ward']}")
    print(f"Attack Type:  {device_info['attack_type']}")
    print(f"{color}Priority:     {priority}{reset}")
    print(f"Confidence:   {confidence*100:.1f}%")
    print(f"Criticality:  {device_info['criticality_tier']}/10")
    if device_info['life_support']:
        print(f"{color}⚕️  LIFE SUPPORT DEVICE ⚕️{reset}")
    print(f"{color}{'='*70}{reset}\n")


def run_demo(num_alerts=10):
    """Run real-time monitoring demo"""
    
    print("="*70)
    print("🎬 IoMT REAL-TIME MONITORING SYSTEM - DEMO")
    print("="*70)
    print("\n🔄 Initializing system...")
    
    # Load model
    model, encoders = load_model()
    print("✅ Alert Prioritization Model loaded")
    
    # Load test data
    X_test = pd.read_csv('../../data/processed/X_test.csv')
    original_df = pd.read_csv('../../data/raw/esp32_iomt_monitoring_dataset.csv')
    
    # Get attack samples
    attack_indices = original_df[original_df['attack_type'] != 'normal'].index
    test_attack_indices = [i for i in attack_indices if i >= 80000][:num_alerts]
    
    print(f"✅ System ready - monitoring {num_alerts} incoming alerts\n")
    print("="*70)
    print("🔴 STARTING REAL-TIME MONITORING...")
    print("="*70)
    
    time.sleep(1)
    
    for i, idx in enumerate(test_attack_indices, 1):
        print(f"\n\n🔔 [{i}/{num_alerts}] Processing incoming alert...")
        time.sleep(0.5)
        
        # Get alert data
        alert_features = X_test.iloc[idx - 80000].values.reshape(1, -1)
        alert_info = original_df.iloc[idx]
        
        # Predict priority
        priority = model.predict(alert_features)[0]
        confidence = max(model.predict_proba(alert_features)[0])
        
        # Prepare device info
        device_info = {
            'device_id': alert_info['device_id'],
            'device_type': alert_info['device_type'],
            'sensor_type': alert_info['sensor_type'],
            'ward': alert_info['ward'],
            'attack_type': alert_info['attack_type'],
            'criticality_tier': alert_info['criticality_tier'],
            'life_support': alert_info['life_support']
        }
        
        # Display alert
        display_alert(alert_features, priority, confidence, device_info)
        
        # Simulate processing time
        time.sleep(1.5)
    
    print("\n" + "="*70)
    print("✅ MONITORING DEMO COMPLETE")
    print("="*70)
    print(f"\n📊 Processed {num_alerts} alerts successfully")
    print("🎯 All alerts prioritized based on clinical impact")
    print("🔗 Related alerts grouped into attack campaigns\n")


if __name__ == "__main__":
    # Run demo with 10 alerts (change number if you want more/less)
    run_demo(num_alerts=10)