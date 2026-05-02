from typing import List, Dict
from datetime import timedelta
import uuid
from src.models import Alert, Incident
from src.config import TIME_WINDOW_MINUTES

class CorrelationEngine:
    """
    Core engine to correlate alerts based on Device ID and Time Windows.
    """

    def correlate(self, alerts: List[Alert]) -> List[Incident]:
        """
        Groups alerts into Incidents.
        
        Logic:
        1. Sort alerts by timestamp.
        2. Group by Device ID.
        3. Within each device, group alerts that occur within TIME_WINDOW_MINUTES of the first alert in the group.
        """
        if not alerts:
            return []

        # 1. Sort by timestamp (essential for time-based correlation)
        sorted_alerts = sorted(alerts, key=lambda x: x.timestamp)

        # 2. Group by Device ID
        device_groups: Dict[str, List[Alert]] = {}
        for alert in sorted_alerts:
            if alert.device_id not in device_groups:
                device_groups[alert.device_id] = []
            device_groups[alert.device_id].append(alert)

        incidents: List[Incident] = []

        # 3. Apply Time Window Correlation per device
        for device_id, device_alerts in device_groups.items():
            current_group: List[Alert] = []
            
            for alert in device_alerts:
                if not current_group:
                    current_group.append(alert)
                    continue
                
                # Check time difference from the FIRST alert in the current group
                start_time = current_group[0].timestamp
                time_diff = alert.timestamp - start_time
                
                if time_diff <= timedelta(minutes=TIME_WINDOW_MINUTES):
                    current_group.append(alert)
                else:
                    # Window exceeded, finalize current group as an incident candidate
                    incidents.append(self._create_incident_skeleton(current_group))
                    # Start new group
                    current_group = [alert]
            
            # Don't forget the last group
            if current_group:
                 incidents.append(self._create_incident_skeleton(current_group))

        return incidents

    def _create_incident_skeleton(self, alerts: List[Alert]) -> Incident:
        """
        Creates an Incident object from a group of alerts.
        Severity and detailed fields will be calculated by the SeverityEngine.
        """
        first_alert = alerts[0]
        start_time = alerts[0].timestamp
        end_time = alerts[-1].timestamp
        
        # Basic aggregation
        confidences = [a.confidence_score for a in alerts]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return Incident(
            incident_id=f"INC-{uuid.uuid4().hex[:8].upper()}",
            affected_device=first_alert.device_id,
            device_type=first_alert.device_type,
            severity="Pending", # To be calculated
            confidence_summary=round(avg_confidence, 2),
            number_of_correlated_alerts=len(alerts),
            time_window=f"{TIME_WINDOW_MINUTES} minutes",
            compliance_tags=[], # To be calculated
            recommended_action="Pending Analysis",
            timestamp=end_time, # Incident time is usually the time of the latest activity or detection
            start_time=start_time,
            end_time=end_time,
            alerts=alerts
        )
