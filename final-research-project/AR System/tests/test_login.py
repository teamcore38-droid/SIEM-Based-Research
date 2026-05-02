import requests
import json

url = "http://localhost:5000/api/login"
payload = {"username": "admin", "password": "medguard123"}
headers = {'Content-Type': 'application/json'}

try:
    print(f"Sending POST to {url}...")
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Login SUCCESS")
    else:
        print("❌ Login FAILED")
except Exception as e:
    print(f"❌ Connection Error: {e}")
