import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_iomt_analysis():
    print("🏥 STARTING IoMT ANALYSIS TEST\n")
    
    # 1. Login to get Token
    print("1. Authenticating...")
    session_token = None
    try:
        res = requests.post(f"{BASE_URL}/login", json={"username": "admin", "password": "medguard123"})
        if res.status_code == 200:
            session_token = res.json().get('token')
            print("   ✅ Login Successful")
        else:
            print("   ❌ Login Failed")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    # 2. Test Cases
    test_cases = [
        {
            "name": "Normal Pulse Oximeter",
            "data": {
                "device_type": "ESP32_Pulse_Oximeter",
                "ward": "General_Ward",
                "protocol": "MQTT",
                "criticality": 5, 
                "packet_rate": 50,
                "attack_type": "normal"
            },
            "expected_priority": ["LOW", "INFO"]
        },
        {
            "name": "Critical ICU Attack (DDoS)",
            "data": {
                "device_type": "ESP32_Pulse_Oximeter",
                "ward": "ICU",
                "protocol": "HTTP",
                "criticality": 10,
                "life_support": True,
                "packet_rate": 2000,
                "attack_type": "ddos",
                "attack_severity": 40
            },
            "expected_priority": ["CRITICAL", "HIGH"]
        }
    ]

    headers = {"Authorization": f"Bearer {session_token}"}

    print("\n2. Running Prediction Tests...")
    for case in test_cases:
        print(f"\n   🧪 Testing: {case['name']}")
        try:
            res = requests.post(f"{BASE_URL}/iomt/analyze", json=case['data'], headers=headers)
            if res.status_code == 200:
                result = res.json()
                priority = result.get('priority')
                conf = result.get('confidence')
                print(f"      Result: {priority} ({conf}%)")
                
                if priority in case['expected_priority']:
                     print(f"      ✅ Prediction Matches Expectation")
                else:
                     print(f"      ⚠️ Prediction Mismatch (Expected {case['expected_priority']}, Got {priority})")
            else:
                print(f"      ❌ API Error: {res.text}")
        except Exception as e:
            print(f"      ❌ Function Error: {e}")

    print("\n✨ IoMT VERIFICATION COMPLETE")

if __name__ == "__main__":
    test_iomt_analysis()
