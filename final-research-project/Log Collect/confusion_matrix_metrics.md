# Privacy Scanner PHI Detection Confusion Matrix (Log Collect)

**Model:** `ars_phi_model.pkl`
**Overall Accuracy:** 96.00%
**Objective:** NLP-based entity detector parsing raw logs and telemetry strings to redact patient identifiers (HIPAA/GDPR compliance).

| Actual \ Predicted | PHI Detected | PHI Not Detected |
| :--- | :---: | :---: |
| **Actual PHI Present** | True Positive = 19,150 | False Negative = 800 |
| **Actual No PHI** | False Positive = 1,200 | True Negative = 28,850 |

## Class Performance Metrics
| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **SAFE** | 0.97 | 0.96 | 0.97 | 30,050 |
| **PHI_DETECTED** | 0.94 | 0.96 | 0.95 | 19,950 |
