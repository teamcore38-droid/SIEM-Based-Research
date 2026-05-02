import requests
import time

URL = "http://localhost:5000/api/traffic"

def verify_stream():
    print("🔄 Verifying Automated IoMT Stream...")
    try:
        res = requests.get(URL)
        if res.status_code == 200:
            data = res.json()
            print("   ✅ API traffic endpoint reachable")
            
            if 'iomt' in data:
                prio = data['iomt'].get('priority')
                conf = data['iomt'].get('confidence')
                print(f"   ✅ IoMT Field Found: Priority={prio}, Confidence={conf}%")
                
                if prio in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO', 'MONITORING']:
                    print("   ✅ Priority Value is Valid")
                else:
                    print(f"   ⚠️ Unexpected Priority Value: {prio}")
            else:
                 print("   ❌ 'iomt' field missing in response")
        else:
             print(f"   ❌ API connect failed: {res.status_code}")
             
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    verify_stream()
