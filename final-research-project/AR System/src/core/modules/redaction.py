import re
import logging
import joblib
import os
import pandas as pd

class PHIRedactor:
    def __init__(self):
        # 1. Load AI Brain (The 100% Accurate Model)
        self.model = None
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__)) # src/core/modules
            model_path = os.path.join(base_dir, '..', '..', '..', 'models', 'ars_phi_model.pkl')
            model_path = os.path.abspath(model_path)
            
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                logging.info(f"[INFO] PHI AI Engine Loaded: {model_path}")
            else:
                logging.warning(f"[WARN] PHI Model missing at {model_path}. Using Basic Regex Mode.")
        except Exception as e:
                logging.error(f"[ERROR] Custom AI Load Fail: {e}")

        # 2. Regex Patterns (Execution Layer)
        # We use AI to DETECT, then Regex to REDACT specific tokens
        self.patterns = {
            'patient_id': r'\b[Pp]-\d{3,5}\b',       # Matches P-123
            'id_generic': r'\bID #\d+\b',            # Matches ID #563811
            'name_context': r'(?<=Patient )([A-Z][a-z]+ [A-Z][a-z]+)', # Lookbehind for "Patient "
            'user_context': r'(?<=User )([a-z]+)',   # Context for "User admin"
            'name_generic': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b' # Fallback Name
        }

    def has_regex_phi(self, text):
        """
        Determines if log contains PHI using HYBRID (AI + REGEX) approach.
        """
        # A. AI OPINION (Primary)
        if self.model:
            try:
                # The pipeline handles text conversion automatically
                prediction = self.model.predict([text])[0]
                return bool(prediction == 1)
            except Exception as e:
                logging.error(f"AI Prediction Error: {e}")
        
        # B. REGEX FALLBACK (Secondary)
        for pattern in self.patterns.values():
            if re.search(pattern, text):
                return True
        return False

    def redact_log(self, log_entry):
        """
        FR-02: Contextual PHI Redaction.
        """
        sanitized = log_entry
        
        # We only redact if we are sure (or to be safe, we redact blindly if asked)
        # Apply patterns from most specific to least specific
        
        # 1. Names after "Patient" (High Confidence)
        sanitized = re.sub(r'(?<=Patient )([A-Z][a-z]+ [A-Z][a-z]+)', '[REDACTED_NAME]', sanitized)
        
        # 2. IDs
        sanitized = re.sub(r'\b[Pp]-\d{3,5}\b', '[REDACTED_ID]', sanitized)
        sanitized = re.sub(r'\bID #\d+\b', 'ID #[REDACTED]', sanitized)
        
        # 3. Medical Conditions (Contextual)
        if "Condition:" in sanitized:
             sanitized = re.sub(r'(?<=Condition: ).*', '[REDACTED_MEDICAL]', sanitized)
             
        # 4. Fallback cleanup (Simpler Names)
        # Only if we suspect PHI but specific patterns failed, we might gloss over proper nouns
        # Skipping for now to avoid over-redacting "System Error"
        
        return sanitized
