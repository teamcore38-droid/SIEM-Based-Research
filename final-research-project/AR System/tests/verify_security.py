import requests
import json
import os
import time

BASE_URL = "http://localhost:5000/api"
INVENTORY_FILE = "logs/inventory.json"

def test_security_flow():
    print("🔒 STARTING SECURITY & PERSISTENCE VERIFICATION\n")
    
    # 1. Try to access protected endpoint WITHOUT token
    print("1. Testing Unauthorized Access (Should Fail)...")
    try:
        res = requests.post(f"{BASE_URL}/devices/add", json={"ip": "1.1.1.1"})
        if res.status_code == 401:
            print("   ✅ Protected Endpoint blocked unauthorized request (401)")
        else:
            print(f"   ❌ FAILED: Endpoint allowed request with status {res.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 2. Login to get Token
    print("\n2. Testing Admin Login...")
    session_token = None
    try:
        res = requests.post(f"{BASE_URL}/login", json={"username": "admin", "password": "medguard123"})
        if res.status_code == 200:
            data = res.json()
            session_token = data.get('token')
            print(f"   ✅ Login Successful. Token received: {session_token[:15]}...")
        else:
            print("   ❌ Login Failed")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    # 3. Add Device WITH Token
    print("\n3. Testing Authorized Action (Add Device)...")
    test_ip = f"10.0.0.{int(time.time()) % 100}"
    headers = {"Authorization": f"Bearer {session_token}"}
    try:
        res = requests.post(f"{BASE_URL}/devices/add", 
                          json={"ip": test_ip, "type": "Security Test Node"},
                          headers=headers)
        if res.status_code == 200:
            print(f"   ✅ Device {test_ip} added successfully.")
        else:
            print(f"   ❌ Failed to add device: {res.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 4. Verify Persistence
    print("\n4. Verifying Data Persistence (inventory.json)...")
    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, 'r') as f:
            data = json.load(f)
            found = any(d['ip'] == test_ip for d in data)
            if found:
                 print("   ✅ Persistence Verified: Device found in JSON file.")
            else:
                 print("   ❌ Persistence Failed: Device not found in JSON file.")
    else:
        print("   ❌ Error: inventory.json not found.")

    print("\n✨ VERIFICATION COMPLETE")

if __name__ == "__main__":
    test_security_flow()
