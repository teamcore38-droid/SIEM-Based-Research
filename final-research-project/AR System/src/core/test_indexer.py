import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Using the 'admin' status found in the password file
URL = "https://20.239.185.152:9200"
USER = "admin"
PASS = "gAp4U6NX3kWx7IkGgi2DRTXhpTbB?Xad"

print(f"Testing Connection to Wazuh Indexer: {URL}")

try:
    response = requests.get(URL, auth=(USER, PASS), verify=False, timeout=5)
    if response.status_code == 200:
        print("✅ SUCCESS! Port 9200 is OPEN.")
        print(response.json())
    else:
        print(f"❌ FAILED. Status: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ ERROR: Could not connect to Port 9200. It is likely BLOCKED by Firewall.")
    print(f"Details: {e}")
