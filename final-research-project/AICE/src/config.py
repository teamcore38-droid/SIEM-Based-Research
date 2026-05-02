import os

# --- Temporal Correlation Configuration ---
TIME_WINDOW_MINUTES = 5  # Time window to group alerts into a single incident

# --- Confidence Thresholds ---
MIN_CONFIDENCE_THRESHOLD = 0.3  # Ignore alerts below this confidence
HIGH_CONFIDENCE_THRESHOLD = 0.8 # Alerts above this are considered high confidence

# --- Severity & Scoring ---
# Base scores for device criticality
DEVICE_CRIT_SCORES = {
    "ventilator": 10,
    "infusion_pump": 9,
    "cardiac_monitor": 8,
    "mri_scanner": 7,
    "gateway": 6,
    "workstation": 4,
    "admin_pc": 3,
    "printer": 1,
    "unknown": 2
}

# Weights for severity calculation
WEIGHT_CONFIDENCE = 0.4
WEIGHT_CRITICALITY = 0.4
WEIGHT_FREQUENCY = 0.2

# Severity Label Thresholds (0-100 scale)
SEV_CRITICAL_THRESHOLD = 80
SEV_HIGH_THRESHOLD = 60
SEV_MEDIUM_THRESHOLD = 40
# Below 40 is Low

# --- Compliance ---
COMPLIANCE_MAPPINGS = {
    "HIPAA": ["ventilator", "infusion_pump", "cardiac_monitor", "mri_scanner", "gateway"],
    "SL-DPA": ["workstation", "admin_pc", "gateway"]  # Generalized for personal data/admin access
}
