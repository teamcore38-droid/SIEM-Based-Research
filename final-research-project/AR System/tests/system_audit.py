import requests
import json
import time

BASE_URL = "http://localhost:5000/api"
TOKEN = None

def print_status(component, status, message=""):
    icon = "✅" if status == "PASS" else "❌"
    print(f"{icon} [{component: <20}] {status} {message}")

def login():
    global TOKEN
    try:
        url = f"{BASE_URL}/login"
        payload = {"username": "admin", "password": "medguard123"}
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            TOKEN = data.get("token")
            print_status("Authentication", "PASS", "Admin logged in successfully")
            return True
        else:
            print_status("Authentication", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_status("Authentication", "FAIL", f"Connection refused: {e}")
        return False

def check_endpoint(name, endpoint, method="GET"):
    headers = {}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # Basic validation
            count = len(data) if isinstance(data, list) else len(data.keys())
            print_status(name, "PASS", f"Returned {count} items/keys")
        else:
            print_status(name, "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        print_status(name, "FAIL", str(e))

def run_audit():
    print("\nXXX MEDGUARD-X SYSTEM DIAGNOSTIC XXX")
    print("="*50)
    
    # 1. Auth
    if not login():
        print("!!! Critical Failure: Cannot Login. Aborting Deep Checks !!!")
        return

    # 2. Core Dashboard
    check_endpoint("System Stats", "/stats")
    check_endpoint("Traffic & IoMT", "/traffic")
    
    # 3. Device Management
    check_endpoint("Device Inventory", "/devices")
    
    # 4. New Modules
    check_endpoint("Privacy Vault", "/privacy")
    check_endpoint("Incident History", "/history")
    check_endpoint("IoMT Alerts", "/iomt/alerts")

    print("="*50)
    print("System Audit Complete.")

if __name__ == "__main__":
    run_audit()
