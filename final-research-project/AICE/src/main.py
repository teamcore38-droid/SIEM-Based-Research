import json
import os
from typing import List, Union
from src.ingestion import IngestionEngine
from src.correlation import CorrelationEngine
from src.severity import SeverityEngine
from src.models import Incident

class AICE:
    """
    Adaptive Incident Correlation Engine (AICE) Main Controller.
    """
    def __init__(self):
        self.ingestion = IngestionEngine()
        self.correlation = CorrelationEngine()
        self.severity = SeverityEngine()

    def run(self, input_files: Union[str, List[str]], output_file: str):
        """
        Runs the full AICE pipeline.
        1. Ingest Alerts
        2. Correlate into Incidents
        3. Assess Severity & Compliance
        4. Output Results
        """
        if isinstance(input_files, str):
            input_files = [input_files]
            
        print(f"[*] Starting AICE Pipeline...")
        alerts = []
        for file_path in input_files:
            print(f"[*] Loading alerts from {file_path}...")
            file_alerts = self.ingestion.load_alerts(file_path)
            alerts.extend(file_alerts)
            print(f"[*] Loaded {len(file_alerts)} alerts from {file_path}.")
        
        print(f"[*] Total loaded: {len(alerts)} alerts.")

        if not alerts:
            print("[!] No alerts found. Exiting.")
            return

        print(f"[*] Correlating alerts...")
        incidents = self.correlation.correlate(alerts)
        print(f"[*] Generated {len(incidents)} candidate incidents.")

        print(f"[*] Calculating severity and compliance...")
        final_incidents = []
        for inc in incidents:
            processed_inc = self.severity.process_incident(inc)
            final_incidents.append(processed_inc)

        print(f"[*] Saving output to {output_file}...")
        self._save_output(final_incidents, output_file)
        print(f"[*] Done. Processed {len(final_incidents)} incidents.")

    def _save_output(self, incidents: List[Incident], output_file: str):
        data = [inc.to_dict() for inc in incidents]
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    # Default behavior for testing
    aice = AICE()
    aice.run("data/alerts.json", "data/incidents.json")
