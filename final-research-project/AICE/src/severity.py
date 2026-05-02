from typing import List
from src.models import Incident

class SeverityEngine:
    """
    Assigns severity scores, compliance tags, and recommended actions to Incidents
    based purely on detection_results.csv schema.
    """

    def process_incident(self, incident: Incident) -> Incident:
        """
        Enriches the incident with severity, tags, and actions.
        Also aggregates key metrics for reporting.
        """
        # Collect metric data
        metrics = {
            "ward": "N/A",
            "src_ips": set(),
            "protocols": set(),
            "avg_heart_rate": 0.0,
            "max_temp": 0.0,
            "rhythms": set(),
            "postures": set(),
            "falls_count": 0,
            "attack_types": set(),
            "movement_spike": False,
            "raw_timestamps": []
        }
        
        hr_values = []
        temp_values = []
        
        for a in incident.alerts:
            raw = a.raw_data
            if metrics["ward"] == "N/A": metrics["ward"] = raw.get("ward", "N/A")
            if raw.get("src_ip"): metrics["src_ips"].add(raw.get("src_ip"))
            if raw.get("protocol"): metrics["protocols"].add(raw.get("protocol"))
            if raw.get("rhythm_label"): metrics["rhythms"].add(raw.get("rhythm_label"))
            if raw.get("posture_event"): metrics["postures"].add(raw.get("posture_event"))
            if str(raw.get("fall_detected", "")).upper() in ["1", "TRUE"]: metrics["falls_count"] += 1
            if raw.get("attack_type") and str(raw.get("attack_type")) not in ["0", "-1"]: 
                metrics["attack_types"].add(str(raw.get("attack_type")))

            # Physiological aggregation
            for k in ["heart_rate_bpm", "heart_rate_bpm_pulse"]:
                v = raw.get(k)
                if v and v != "-1":
                    try: hr_values.append(float(v))
                    except: pass
            
            t = raw.get("temperature_celsius")
            if t and t != "-1":
                try: temp_values.append(float(t))
                except: pass
            
            # Movement analysis (Accel/Gyro spikes)
            try:
                accel = [float(raw.get(f"accel_{c}", 0)) for c in ['x', 'y', 'z']]
                if any(abs(v) > 15 for v in accel): # High G-force spike
                    metrics["movement_spike"] = True
            except: pass

            # Timestamps
            raw_ts = raw.get('timestamp')
            if raw_ts:
                metrics["raw_timestamps"].append(str(raw_ts))

        avg_hr = round(sum(hr_values)/len(hr_values), 1) if hr_values else 0
        max_t = max(temp_values) if temp_values else 0
        
        first_raw = incident.alerts[0].raw_data
        
        # Finalize metrics for output using exact keys requested where possible
        incident.representative_metrics = {
            "ward": metrics["ward"],
            "life_support": first_raw.get("life_support", "unknown"),
            "criticality_tier": first_raw.get("criticality_tier", "0"),
            "protocol": ", ".join(metrics["protocols"]),
            "src_ip": ", ".join(list(metrics["src_ips"])[:3]),
            "dst_port": first_raw.get("dst_port", "N/A"),
            "heart_rate_bpm": avg_hr,
            "temperature_celsius": max_t,
            "rhythm_label": ", ".join(metrics["rhythms"]),
            "fall_detected": metrics["falls_count"] > 0,
            "posture_event": ", ".join(metrics["postures"]),
            "attack_type": ", ".join(metrics["attack_types"]) if metrics["attack_types"] else "None",
            "anomaly_flag": any(str(a.raw_data.get("anomaly_flag")).strip() == "1" for a in incident.alerts),
            "prediction": ", ".join(set(a.prediction for a in incident.alerts)),
            # Raw samples for CSV layout
            "ecg_raw_value": first_raw.get("ecg_raw_value", "0"),
            "accel_x": first_raw.get("accel_x", "0"),
            "gyro_x": first_raw.get("gyro_x", "0"),
            "label": first_raw.get("label", "N/A"),
            # Contextual stats
            "falls_count": metrics["falls_count"],
            "movement_anomaly": metrics["movement_spike"],
            "Source_Dataset_Timestamps": f"{min(metrics['raw_timestamps'])} - {max(metrics['raw_timestamps'])}" if metrics["raw_timestamps"] else "N/A"
        }

        incident.severity = self._calculate_severity_tier(incident)
        incident.compliance_tags = self._get_compliance_tags(incident)
        incident.recommended_action = self._generate_recommendation(incident)
        
        return incident

    def _calculate_severity_tier(self, incident: Incident) -> str:
        metrics = incident.representative_metrics
        alerts = incident.alerts
        
        first_raw = alerts[0].raw_data
        is_life_support = str(first_raw.get('life_support', 'False')).lower() == 'true'
        try:
            ctier = int(str(first_raw.get('criticality_tier', 0) or 0))
        except ValueError:
            ctier = 0
        is_critical_asset = is_life_support or ctier >= 7

        attack_active = metrics["attack_type"] != "None"
        
        # High physiological concern
        physio_danger = (
            metrics["falls_count"] > 0 or 
            metrics["movement_anomaly"] or
            any(r != "NORMAL_SINUS" for r in metrics.get("rhythm_label", "").split(", ") if r)
        )
        
        if metrics["heart_rate_bpm"] > 0 and (metrics["heart_rate_bpm"] < 50 or metrics["heart_rate_bpm"] > 130):
            physio_danger = True
            
        if metrics["temperature_celsius"] > 39.5 or (metrics["temperature_celsius"] > 0 and metrics["temperature_celsius"] < 34):
            physio_danger = True

        # 1. Critical
        if attack_active and physio_danger:
            return "Critical"
            
        # 2. High 
        if physio_danger:
            return "High"
        
        if attack_active and is_critical_asset:
            return "High"
            
        if incident.number_of_correlated_alerts > 20:
            return "High"

        # 3. Medium
        if attack_active or is_critical_asset:
            return "Medium"
            
        return "Low"

    def _get_compliance_tags(self, incident: Incident) -> List[str]:
        tags = []
        if incident.alerts:
            raw = incident.alerts[0].raw_data
            if str(raw.get('life_support', 'False')).lower() == 'true':
                tags.append("MEDICAL_LIFESUPPORT")
            if raw.get("ward"):
                tags.append(f"LOC_{raw.get('ward').upper()}")
        return tags

    def _generate_recommendation(self, incident: Incident) -> str:
        sev = incident.severity
        metrics = incident.representative_metrics
        
        if sev == "Critical":
            return f"EMERGENCY: Physical and Cyber threats correlated on {incident.affected_device} in {metrics['ward']}. Response required immediately."
        elif sev == "High":
            state = "Physical Anomaly" if metrics["falls_count"] > 0 else "Security Threat"
            return f"High Priority: {state} detected on {incident.affected_device}. Check patient status and secure network."
        elif sev == "Medium":
            return f"Investigate: Potential {metrics['attack_type']} or physiological drift in {metrics['ward']}."
        else:
            return "Routine maintenance: Minor anomalies detected."
