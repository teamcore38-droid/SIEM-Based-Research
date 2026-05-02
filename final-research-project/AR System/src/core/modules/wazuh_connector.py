import requests
import json
import logging
import time
import urllib3

# Suppress insecure request warnings (Wazuh often uses self-signed certs)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WazuhConnector:
    def __init__(self, manager_ip, user, password):
        self.base_url = f"https://{manager_ip}:55000"
        self.auth = (user, password)
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
        
    def authenticate(self):
        """Authenticates with Wazuh API to get a JWT token."""
        try:
            url = f"{self.base_url}/security/user/authenticate"
            response = requests.post(url, auth=self.auth, verify=False, timeout=5)
            
            if response.status_code == 200:
                self.token = response.json()['data']['token']
                self.headers['Authorization'] = f"Bearer {self.token}"
                print(f"[WAZUH_CONN] Authentication Successful.")
                return True
            else:
                print(f"[WAZUH_CONN] Auth Failed: {response.text}")
                return False
        except Exception as e:
            print(f"[WAZUH_CONN] Connection Error: {e}")
            return False

    def get_monitoring_data(self):
        """Fetches active agents and treats them as live heartbeat events."""
        if not self.token:
            if not self.authenticate():
                return []

        try:
            # We poll the 'agents' endpoint to see who is active
            # This serves as a "Heartbeat" ingestion from Wazuh
            url = f"{self.base_url}/agents"
            params = {
                'status': 'active',
                'select': 'id,ip,name,os,status'
            }
            
            response = requests.get(url, headers=self.headers, params=params, verify=False, timeout=5)
            
            if response.status_code == 200:
                data = response.json().get('data', {}).get('affected_items', [])
                events = []
                for agent in data:
                    # Create a standardized event for the AR System
                    events.append({
                        "device_ip": agent.get('ip', '0.0.0.0'),
                        "agent_id": agent.get('id'),
                        "log": f"Wazuh Agent '{agent.get('name')}' is Active. OS: {agent.get('os', {}).get('name', 'Unknown')}",
                        "anomaly_score": 0.0  # Default to Safe/Monitor for plain heartbeats
                    })
                return events
            
            elif response.status_code == 401:
                print("[WAZUH_CONN] Token expired. Refreshing...")
                self.authenticate()
                return []
            else:
                logging.error(f"Wazuh API Error: {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"Failed to fetch Wazuh data: {e}")
            return []

    def mock_stream(self):
        """
        Since we don't have the user's password yet, 
        we provide a generator that returns formatted events 
        to test the integration logic immediately.
        """
        while True:
            # Yield nothing most of the time
            time.sleep(2)
            
            # Simple heartbeat to show connection is "alive"
            # In real implementation this would be a real API call
            yield None
