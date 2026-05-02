# IoMT Monitoring System — Alert Prioritization & Alert Grouping

**Student:** MMM Ukasha (IT22904232)
**Project ID:** 25-26J-70
**Supervisor:** Mr. Kanishka Yapa
**Co-Supervisor:** Mr. Deemantha Siriwardhana

---

## Project Overview
Real-Time SIEM-Based Monitoring System for IoMT Cybersecurity.
This component covers two novel features:
1. Alert Prioritization (CRITICAL / HIGH / MEDIUM / LOW)
2. Alert Grouping (cluster related alerts into one incident)

## Devices Monitored
| Device              | Ward         | Life Support | Criticality |
|---------------------|--------------|--------------|-------------|
| Pulse Oximeter      | ICU          | TRUE         | 9           |
| ECG Monitor         | Ward_02      | FALSE        | 7           |
| Temperature Sensor  | General_Ward | FALSE        | 6           |
| Motion Sensor       | Ward_01      | FALSE        | 5           |

## Attack Types in Dataset
- sensor_spoofing, mqtt_port_manipulation, device_identity_spoofing
- protocol_anomaly, flooding, ip_spoofing, data_tampering, ddos, normal

## Run Order
```
Step 1: python src/monitoring/01_merge_and_label.py
Step 2: python src/monitoring/02_preprocess.py
Step 3: python src/monitoring/03_train_prioritization.py
Step 4: python src/monitoring/04_alert_grouping.py
Step 5: python src/monitoring/05_demo.py
```