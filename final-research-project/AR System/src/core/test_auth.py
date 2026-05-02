import requests
import urllib3
import getpass

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MANGER_IP = "20.239.185.152"
URL = f"https://{MANGER_IP}:55000/security/user/authenticate"

def test_login(user, password):
    print(f"\nTrying User: '{user}' ...")
    try:
        response = requests.post(URL, auth=(user, password), verify=False, timeout=5)
        if response.status_code == 200:
            print("✅ SUCCESS! Authentication working.")
            print(f"Token: {response.json()['data']['token'][:10]}...")
            return True
        else:
            print(f"❌ FAILED. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: Connection failed - {e}")
        return False

print("=== Wazuh API Credential Tester ===")
print(f"Target: {MANGER_IP}")

while True:
    user = input("\nEnter Username (default: wazuh-wui): ").strip() or "wazuh-wui"
    password = input("Enter Password: ").strip()
    
    if test_login(user, password):
        break
    
    retry = input("\nTry again? (y/n): ").lower()
    if retry != 'y':
        break
