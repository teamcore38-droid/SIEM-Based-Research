# Intelligent Classification Confusion Matrices (AI Threat Intel)

This layer implements both supervised classification and unsupervised zero-day anomaly detection.

## 1. Supervised Threat Prediction 
**Model:** `random_forest_model.pkl` | **Accuracy:** 98.50%
**Scope:** Binary classification on 47 parameters for recognized network attacks (DDoS, Spoofing, Tampering).

| Actual \ Predicted | ATTACK (Threat) | BENIGN (Normal) |
| :--- | :---: | :---: |
| **Actual ATTACK** | True Positive = 34,300 | False Negative = 700 |
| **Actual BENIGN** | False Positive = 800 | True Negative = 64,200 |

#### Metrics
| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **BENIGN** | 0.99 | 0.99 | 0.99 | 65,000 |
| **ATTACK** | 0.98 | 0.98 | 0.98 | 35,000 |

---

## 2. Baseline Anomaly Detection
**Model:** `isolation_forest_model.pkl` | **Scope:** Target 5% Anomaly Distribution threshold (`n_estimators=100`, `contamination=0.05`).

| Actual \ Predicted | ANOMALY (-1) | NORMAL (1) |
| :--- | :---: | :---: |
| **Actual ANOMALY** | True Positive = 4,750 | False Negative = 250 |
| **Actual NORMAL** | False Positive = 470 | True Negative = 94,530 |

#### Metrics
| Class | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: |
| **NORMAL (1)** | 0.97 | 0.96 | 0.96 | 
| **ANOMALY (-1)** | 0.91 | 0.95 | 0.93 |
