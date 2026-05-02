import joblib
import pandas as pd
import os
import logging

class InferenceEngine:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        # Navigate up two levels from src/core to root, then to models
        self.root_path = os.path.abspath(os.path.join(self.base_path, '..', '..'))
        self.defense_model_path = os.path.join(self.root_path, 'models', 'ars_decision_model_final.pkl')
        self.phi_model_path = os.path.join(self.root_path, 'models', 'ars_phi_model.pkl')
        
        self.defense_model = self._load_model(self.defense_model_path)
        self.phi_model = self._load_model(self.phi_model_path)

    def _load_model(self, path):
        if os.path.exists(path):
            try:
                model = joblib.load(path)
                logging.info(f"✅ Loaded Model: {path}")
                return model
            except Exception as e:
                logging.error(f"[ERROR] Failed to load model {path}: {e}")
                return None
        else:
            logging.warning(f"⚠️ Model not found at {path}. Using fallback logic.")
            return None

    def predict_action(self, event_dict):
        """
        Input: Dict containing Vitals + Network Stats
        Output: 'QUARANTINE', 'ROLLBACK', 'MONITOR', 'no_action'
        """
        if not self.defense_model:
            return "MONITOR" # Fallback

        try:
            # High-Fidelity Model Features (must match training exactly)
            data = {
                'heart_rate': event_dict.get('heart_rate', 75),
                'spo2': event_dict.get('spo2', 98),
                'sys_bp': event_dict.get('sys_bp', 120), # Using sys_bp as per training
                'network_latency': event_dict.get('network_latency', 20),
                'packet_size': event_dict.get('packet_size', 500),
                'anomaly_score': event_dict.get('anomaly_score', 0.0)
            }
            
            # Map any legacy keys if they exist in event_dict
            if 'bp_sys' in event_dict: data['sys_bp'] = event_dict['bp_sys']
            
            # Create DataFrame with specific column order
            columns = ['heart_rate', 'spo2', 'sys_bp', 'network_latency', 'packet_size', 'anomaly_score']
            df = pd.DataFrame([data], columns=columns)
            
            return self.defense_model.predict(df)[0]

        except Exception as e:
            logging.error(f"Prediction Error: {e}")
            # Fail-safe logic
            if event_dict.get('anomaly_score', 0) > 0.8: return "QUARANTINE"
            return "MONITOR"

    def detect_phi(self, log_text):
        """
        Returns True if log contains PHI, False otherwise
        """
        if not self.phi_model:
            return False
            
        try:
            # Handle case where pickle is a Dict containing the model
            model_to_use = self.phi_model
            if isinstance(self.phi_model, dict):
                # Try to find the actual estimator key, usually 'model' or 'pipeline'
                if 'model' in self.phi_model:
                    model_to_use = self.phi_model['model']
                elif 'pipeline' in self.phi_model:
                    model_to_use = self.phi_model['pipeline']
            
            # Ensure it has a predict method
            if hasattr(model_to_use, 'predict'):
                prediction = model_to_use.predict([log_text])[0]
                return bool(prediction)
            else:
                logging.error(f"PHI Model object {type(model_to_use)} has no predict method.")
                return False
                
        except Exception as e:
            logging.error(f"PHI Detection Error: {e}")
            return False
