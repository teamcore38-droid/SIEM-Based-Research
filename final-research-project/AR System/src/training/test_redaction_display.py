import re
import pickle

# Load the AI Model (To check IF we should redact)
print("Loading PHI Model...")
with open("ars_phi_model.pkl", "rb") as f:
    phi_bundle = pickle.load(f)
    model = phi_bundle["model"]
    vectorizer = phi_bundle["vectorizer"]

def redact_log(text):
    # 1. Ask AI: Is this sensitive?
    vec = vectorizer.transform([text.lower()])
    is_sensitive = model.predict(vec)[0] # 1 = Yes, 0 = No
    
    if is_sensitive == 0:
        return text # Return original if clean
        
    print(f"  [AI Alert] Sensitive Data Detected! scrubbing...")
    
    # 2. Logic: Regex Masking (The actual "Redaction")
    # Mask IDs (numbers 3+ digits long)
    redacted_text = re.sub(r'\b\d{3,}\b', '[REDACTED_ID]', text)
    
    # Mask Common Name patterns (Simple heuristic: Capitalized words after 'Patient')
    # Note: In production you would use spaCy for names, here is a simple regex for demo
    redacted_text = re.sub(r'(Patient\s+)([A-Z][a-z]+)', r'\1[REDACTED_NAME]', redacted_text)
    
    return redacted_text

# --- DEMO ---
sample_logs = [
    "System CPU load at 45% - Normal",
    "Patient John Doe ID 94321 reported high heart rate.",
    "User admin logged in successfully.",
    "Error in infusion pump for Patient Alice (ID: 8821)."
]

print("\n--- PHI REDACTION DEMO ---")
for log in sample_logs:
    print(f"\nOriginal: {log}")
    clean_log = redact_log(log)
    print(f"Final   : {clean_log}")
