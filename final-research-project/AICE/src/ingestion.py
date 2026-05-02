import json
import csv
import logging
from typing import List, Union
from datetime import datetime

from src.models import Alert

# Set up simple logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class IngestionEngine:
    """
    Responsible for loading and normalizing alert data.
    """
    
    @staticmethod
    def load_alerts(file_path: str) -> List[Alert]:
        """
        Loads alerts from a JSON file (list or lines) or a CSV file.
        """
        alerts = []
        
        if file_path.lower().endswith('.csv'):
            return IngestionEngine._load_from_csv(file_path)

        try:
            with open(file_path, 'r') as f:
                content = f.read().strip()
                if not content:
                    return []
                
                # Try parsing as full JSON list
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        for item in data:
                            alert = IngestionEngine._parse_single_alert(item)
                            if alert:
                                alerts.append(alert)
                        return alerts
                except json.JSONDecodeError:
                    pass # Not a JSON list, try JSON lines

                # Try parsing as JSON lines
                f.seek(0)
                for line in f:
                    if line.strip():
                        try:
                            item = json.loads(line)
                            alert = IngestionEngine._parse_single_alert(item)
                            if alert:
                                alerts.append(alert)
                        except json.JSONDecodeError:
                            logging.warning(f"Skipping invalid JSON line: {line[:50]}...")
                            continue
                            
        except FileNotFoundError:
            logging.error(f"File not found at {file_path}")
        except Exception as e:
            logging.error(f"Error loading alerts: {e}")
            
        return alerts

    @staticmethod
    def _load_from_csv(file_path: str) -> List[Alert]:
        alerts = []
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Required by Alert mostly: device_id, timestamp
                    
                    if not all(k in row for k in ['device_id', 'timestamp']):
                        logging.warning(f"Skipping CSV row missing required keys: {row.keys()}")
                        continue
                        
                    try:
                        # Handle timestamp: "2024-02-05 13:35:44" -> ISO or numerical
                        ts_str = row['timestamp']
                        try:
                            ts = datetime.fromisoformat(ts_str)
                        except ValueError:
                            try:
                                # Try parsing "YYYY-MM-DD HH:MM:SS"
                                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                # Try parsing as numerical timestamp (e.g., seconds or ms from an epoch)
                                try:
                                    ts_num = float(ts_str)
                                    # Assuming ts_num might be milliseconds since some epoch or start
                                    # We treat ts_num as milliseconds off a base date (e.g. 1 year ago)
                                    from datetime import timedelta
                                    ts = datetime.now() - timedelta(days=365) + timedelta(milliseconds=ts_num)
                                except ValueError:
                                    ts = datetime.now() # Fallback

                        # prediction -> attack_type if available
                        prediction = row.get('attack_type') or row.get('prediction') or "Anomaly"
                        # some rows might have empty prediction string
                        if not prediction:
                            prediction = "Anomaly"
                            
                        # confidence_score
                        confidence_score = row.get('confidence_score')
                        if confidence_score:
                            confidence_score = float(confidence_score)
                        else:
                            # calculate a dummy confidence score if none available
                            is_attack = row.get('is_attack', '0')
                            has_attack_type = row.get('attack_type', '') != ''
                            if is_attack == '1' or has_attack_type:
                                confidence_score = 0.95
                            else:
                                confidence_score = 0.50
                        
                        # Note: We only append if it's considered an attack or anomaly to simulate AICE filtering?
                        # Actually AICE takes alerts, so we'll pass all or maybe filter out normal traffic.
                        # Usually, only alerts are sent to AICE. Assuming this CSV is all events, let's filter:
                        is_attack_flag = str(row.get('is_attack', '')).strip()
                        prediction_val = str(row.get('prediction', '')).strip()
                        anomaly_flag = str(row.get('anomaly_flag', '')).strip()
                        attack_type_val = str(row.get('attack_type', '')).strip()
                        
                        # Has attack flags?
                        is_attack = is_attack_flag == '1' or prediction_val == '1' or anomaly_flag == '1' or attack_type_val != ''
                        
                        # Is it a purely physiological dataset? (doesn't have standard alert fields)
                        is_physio = 'is_attack' not in row and 'anomaly_flag' not in row
                        
                        # Send to AICE if there's any indication of an issue OR if it's a physiological log
                        if is_attack or is_physio:
                            alert = Alert(
                                device_id=row['device_id'],
                                timestamp=ts,
                                prediction=prediction,
                                confidence_score=confidence_score,
                                device_type=row.get('device_type', 'unknown'),
                                raw_data=row  # Store all other fields including src_ip, etc.
                            )
                            alerts.append(alert)
                    except Exception as e:
                        logging.warning(f"Failed to parse CSV row: {e} | Row: {row}")
                        
        except FileNotFoundError:
            logging.error(f"File not found at {file_path}")
        except Exception as e:
            logging.error(f"Error loading CSV alerts: {e}")
            
        return alerts

    @staticmethod
    def _parse_single_alert(data: dict) -> Union[Alert, None]:
        """
        Validates and converts a dictionary to an Alert object.
        """
        required_fields = ["device_id", "timestamp", "prediction", "confidence_score"]
        for field in required_fields:
            if field not in data:
                logging.warning(f"Skipping alert missing required field '{field}': {data}")
                return None
        
        try:
            # Flexible timestamp parsing
            if isinstance(data["timestamp"], str):
                ts = datetime.fromisoformat(data["timestamp"])
            else:
                # Assume it's already datetime or fail
                ts = data["timestamp"]

            return Alert(
                device_id=data["device_id"],
                timestamp=ts,
                prediction=data["prediction"],
                confidence_score=float(data["confidence_score"]),
                device_type=data.get("device_type", "unknown"),
                raw_data=data
            )
        except Exception as e:
            logging.warning(f"Failed to parse alert data: {e} | Data: {data}")
            return None
