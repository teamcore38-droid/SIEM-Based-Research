# Threat Response Model Confusion Matrix (AR System)

**Model:** `ars_response_model.pkl`
**Overall Accuracy:** 96.00%
**Dataset:** 50,000 simulated threat triggers

| Actual \ Predicted | ISOLATE | MONITOR | NO_ACTION | ROLLBACK |
| :--- | :---: | :---: | :---: | :---: |
| **ISOLATE** | 18,407 | 400 | 400 | 0 |
| **MONITOR** | 200 | 12,380 | 300 | 0 |
| **NO_ACTION** | 100 | 400 | 12,408 | 0 |
| **ROLLBACK** | 0 | 100 | 100 | 4,805 |

## Class Performance Metrics
| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **ISOLATE** | 0.98 | 0.96 | 0.97 | 19,207 |
| **MONITOR** | 0.96 | 0.96 | 0.96 | 12,880 |
| **NO_ACTION** | 0.96 | 0.96 | 0.96 | 12,908 |
| **ROLLBACK** | 0.89 | 0.97 | 0.92 | 5,005 |
