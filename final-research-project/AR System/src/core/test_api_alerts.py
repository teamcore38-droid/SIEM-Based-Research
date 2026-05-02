import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

IP = "20.239.185.152"
USER = "wazuh-wui"
PASS = "Yw+.Oh8drXkX+Z6x72M7E?10lYDj3jDU"

URL_AUTH = f"https://{IP}:55000/security/user/authenticate"
URL_ALERTS = f"https://{IP}:55000/security/alerts" # This might not exist in all versions, verifying.

def test():
    print("1. Authenticating...")
    try:
        resp = requests.post(URL_AUTH, auth=(USER, PASS), verify=False, timeout=5)
        if resp.status_code != 200:
            print(f"Auth failed: {resp.text}")
            return
        
        token = resp.json()['data']['token']
        headers = {'Authorization': f"Bearer {token}"}
        print("   Auth OK.")

        print("2. Trying endpoint: GET /security/alerts ...")
        # In some versions, it's GET /manager/logs or we have to query indexer.
        # Let's try to find a way to get logs/alerts from API.
        
        # NOTE: Standard Wazuh API is for configuration. 
        # Real-time alerts are usually via Filebeat -> Indexer.
        # But let's check if there is ANY access.
        
        resp_alerts = requests.get(URL_ALERTS, headers=headers, verify=False, params={'limit': 1})
        print(f"   Status: {resp_alerts.status_code}")
        print(f"   Response: {resp_alerts.text[:500]}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
