# Adaptive Incident Correlation Metrics (Monitoring System)

**Module:** `aice_core.py`
**Objective:** False Positive Alert Grouping & Discard Workflow 
**Reduction Rate Metric:** 88.5% Base Drop

Unlike categorical ML models, the AICE Monitoring System acts to temporally map alerts and deduct noise. The correlation matrix yields the following performance scale when aggregating identical-device anomalies across 300-second windows.

| Incident Type | Raw ML Alerts Passed In | AICE Filtered Unified Incidents | Reduction Impact | Action Taken |
| :--- | :---: | :---: | :---: | :--- |
| **True Confirmed Attacks** | 39,050 | 485 (Correlated) | **98% (Duplication Drop)** | Escalated to AR System |
| **False Positives (Noise)** | 1,270 | 146 | **88.5% Total FPR Drop** | Logged as INFO/LOW |

*(Note: The adaptive heuristics operating in the AICE layer aggressively drop alarms under a confidence bound of 0.4 beforehand, meaning this matrix reflects the grouped performance post-filtration).*
