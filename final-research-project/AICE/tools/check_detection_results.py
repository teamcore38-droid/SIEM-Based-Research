import sys
import os
import json
from collections import Counter

def check_results(incident_file="data/detection_incidents.json"):
    print("=== AICE Output Checker ===\n")

    if not os.path.exists(incident_file):
        print(f"[!] Target file '{incident_file}' not found. Have you successfully run AICE on detection_results.csv?")
        return

    try:
        with open(incident_file, 'r') as f:
            incidents = json.load(f)
    except Exception as e:
        print(f"[!] Error loading JSON file: {e}")
        return

    total_incidents = len(incidents)
    print(f"[*] Total Curated Incidents: {total_incidents}")

    if total_incidents == 0:
        print("[!] No incidents to summarize.")
        return

    # Statistics Tracking
    severity_counts = Counter()
    device_counts = Counter()
    total_alerts_correlated = 0

    print("\n--- High Severity Critical Incidents ---")
    for inc in incidents:
        severity = inc.get('severity', 'Unknown')
        severity_counts[severity] += 1
        
        device_id = inc.get('affected_device', 'Unknown')
        device_counts[device_id] += 1

        alerts_count = inc.get('number_of_correlated_alerts', 0)
        total_alerts_correlated += alerts_count

        # Print detailed view of High severity
        if severity == 'High':
            print(f"> Incident ID   : {inc.get('incident_id', 'N/A')}")
            print(f"  Device ID     : {device_id} (Type: {inc.get('device_type', 'N/A')})")
            print(f"  Alerts Grouped: {alerts_count}")
            print(f"  Action        : {inc.get('recommended_action', 'N/A')}")
            print(f"  Time Window   : {inc.get('start_time', 'N/A')} to {inc.get('end_time', 'N/A')}\n")

    print("--- General Statistics ---")
    print(f"Total Source Alerts Absorbed : {total_alerts_correlated}")
    print(f"Incident Breakdown by Severity:")
    for sev, count in severity_counts.items():
        print(f"   - {sev}: {count}")

    print("\nMost Affected Devices:")
    for dev, count in device_counts.most_common(5):
        print(f"   - Device {dev}: {count} total incidents generated")

    print("\n===========================")

if __name__ == "__main__":
    check_results()
