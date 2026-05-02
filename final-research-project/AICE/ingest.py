import csv
import json
from datetime import datetime
from aice_core import AICEngine, Alert

class IngestionEngine:
    def __init__(self, engine: AICEngine):
        self.engine = engine
        self.alerts_processed = 0

    def ingest_csv(self, file_path: str):
        print(f"[*] Starting ingestion from {file_path}...")
        
        try:
            with open(file_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Check for BOM or header issues if needed, but csv.DictReader usually handles it if formatted correctly
                
                for row in reader:
                    self.alerts_processed += 1
                    
                    # 1. Normalization
                    try:
                        # Extract fields based on provided CSV structure
                        # CSV Header reference: timestamp,alert_id,device_id,device_type,ward,criticality_tier,life_support...
                        
                        device_id = row.get('device_id')
                        timestamp_str = row.get('timestamp')
                        prediction = row.get('attack_type', row.get('prediction', 'Unknown'))
                        # Default to confidence_score column, else 0.5
                        conf_score_str = row.get('confidence_score', '0.5')
                        
                        # Handle potential empty strings or formatting issues
                        if not conf_score_str: conf_score_str = '0.0'
                        confidence_score = float(conf_score_str)

                        device_type = row.get('device_type', 'Unknown Device')
                        src_ip = row.get('src_ip')
                        
                        # Create Alert Object
                        alert = Alert(
                            device_id=device_id,
                            timestamp=timestamp_str,
                            prediction=prediction,
                            confidence_score=confidence_score,
                            device_type=device_type,
                            src_ip=src_ip
                        )
                        
                        # Feed to Engine
                        self.engine.ingest_alert(alert)
                        
                    except ValueError as e:
                        print(f"[!] Data normalization error on row {self.alerts_processed}: {e}")
                        continue
                    except Exception as e:
                        print(f"[!] Unexpected error on row {self.alerts_processed}: {e}")
                        continue

            print(f"[*] Ingestion complete. Processed {self.alerts_processed} alerts.")
            
        except FileNotFoundError:
            print(f"[!] Error: File not found at {file_path}")
        except Exception as e:
            print(f"[!] Critical Error during ingestion: {e}")

if __name__ == "__main__":
    # Test Run
    engine = AICEngine()
    ingestor = IngestionEngine(engine)
    # This path is just for testing, main run should be via run_aice.py
    # ingestor.ingest_csv("path/to/data.csv")
