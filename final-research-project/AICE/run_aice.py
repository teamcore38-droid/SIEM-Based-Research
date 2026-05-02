import sys
import os

# Ensure src is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import AICE

def main():
    print("=== AICE Demo Runner ===")
    
    input_files = [
        r"c:\Users\acer\Documents\final research\datasets\detection_results.csv",
        r"c:\Users\acer\Documents\final research\datasets\ecg_sensor_log.csv",
        r"c:\Users\acer\Documents\final research\datasets\HearRate.csv",
        r"c:\Users\acer\Documents\final research\datasets\motion_sensor_log (1).csv",
        r"c:\Users\acer\Documents\final research\datasets\temperature_log.csv",
        r"c:\Users\acer\Documents\final research\datasets\fall_logs.csv",
    ]
    output_file = "data/detection_incidents.json"
    
    # Check if inputs exist
    for f in input_files:
        if not os.path.exists(f):
            print(f"Input file {f} not found.")

    aice = AICE()
    aice.run(input_files, output_file)
    print(f"\nResults saved to {output_file}")
    
    # Simple print of results
    try:
        import json
        with open(output_file, 'r') as f:
            incidents = json.load(f)
            print("\n--- Incident Summary ---")
            for inc in incidents:
                print(f"ID: {inc['incident_id']} | Severity: {inc['severity']} | Method: {inc['prediction'] if 'prediction' in inc else 'N/A'}") # prediction not in incident summary directly, it's aggregated
                print(f"   Device: {inc['affected_device']} ({inc['device_type']})")
                print(f"   Alerts: {inc['number_of_correlated_alerts']} | Action: {inc['recommended_action'][:50]}...")
                print("-" * 30)
    except Exception as e:
        print(f"Error reading output: {e}")

if __name__ == "__main__":
    main()
