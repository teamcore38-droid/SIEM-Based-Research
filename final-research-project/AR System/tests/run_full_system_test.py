import time
import requests
import os
import sys
import pandas as pd
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))

from inference_engine import InferenceEngine
from modules.redaction import PHIRedactor
from modules.reporting import ReportGenerator

def run_tests():
    print("🏥 ARS MASTER SYSTEM VALIDATION")
    print("=================================")
    print(f"🕒 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = {"PASS": 0, "FAIL": 0}

    # ==================================================
    # TEST 1: THREAT DETECTION (AI Brain)
    # ==================================================
    print("\n🔍 TEST 1: THREAT INTELLIGENCE (Threat vs Clean)")
    try:
        engine = InferenceEngine()
        
        # Case A: Normal Vitals
        normal_event = {"heart_rate": 70, "spo2": 98, "sys_bp": 120, "anomaly_score": 0.1, "packet_size": 500, "network_latency": 20}
        pred_normal = engine.predict_action(normal_event)
        
        # Case B: Ransomware Pattern
        danger_event = {"heart_rate": 150, "spo2": 85, "sys_bp": 180, "anomaly_score": 0.95, "packet_size": 15000, "network_latency": 1500}
        pred_danger = engine.predict_action(danger_event)
        
        if pred_normal in ["NO_ACTION", "MONITOR"] and pred_danger == "QUARANTINE":
            print("   ✅ PASS: Correctly differentiated Safe vs Attack.")
            results["PASS"] += 1
        else:
            print(f"   [ERROR] FAIL: AI Confusion. Normal={pred_normal}, Attack={pred_danger} (Expected QUARANTINE)")
            results["FAIL"] += 1
            
    except Exception as e:
        print(f"   [ERROR] FAIL: Exception {e}")
        results["FAIL"] += 1


    # ==================================================
    # TEST 2: PRIVACY GUARD (PHI Redaction)
    # ==================================================
    print("\n🔒 TEST 2: PHI REDACTION (Privacy)")
    try:
        redactor = PHIRedactor()
        
        # Case A: Sensitive Log
        sensitive_msg = "Patient John Silva (ID: P-999) has critical vitals."
        # We need to simulate the Main Loop logic: Check IF sensitive, THEN redact
        is_sensitive = redactor.has_regex_phi(sensitive_msg)
        redacted_msg = redactor.redact_log(sensitive_msg)
        
        # Case B: Harmless Log (System Error)
        safe_msg = "System Error 505: Connection Timeout."
        is_safe_flagged = redactor.has_regex_phi(safe_msg)
        
        if is_sensitive and "[REDACTED_NAME]" in redacted_msg and not is_safe_flagged:
            print(f"   ✅ PASS: Redacted PHI and Ignored System Error.")
            print(f"      Input:  {sensitive_msg}")
            print(f"      Output: {redacted_msg}")
            results["PASS"] += 1
        else:
            print(f"   [ERROR] FAIL: Privacy Logic Flaw.")
            print(f"      Sensitive Detected? {is_sensitive}")
            print(f"      Safe Flagged? {is_safe_flagged}")
            print(f"      Redacted Output: {redacted_msg}")
            results["FAIL"] += 1

    except Exception as e:
         print(f"   [ERROR] FAIL: Exception {e}")
         results["FAIL"] += 1


    # ==================================================
    # TEST 3: COMPLIANCE (Report Generation)
    # ==================================================
    print("\n📝 TEST 3: COMPLIANCE REPORTING (Daily Dashboard)")
    try:
        # Create a dummy log file if not exists
        log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'ars_audit.log')
        if not os.path.exists(log_path):
             with open(log_path, 'w') as f:
                 f.write("2026-01-01 10:00:00 - INFO - ARS Started")
        
        reporter = ReportGenerator(log_file=log_path)
        output_folder = os.path.join(os.path.dirname(__file__), '..', 'Wazuh_Admin_Portal_Reports')
        if not os.path.exists(output_folder): os.makedirs(output_folder)
        reporter.report_dir = output_folder
        
        pdf_file = reporter.generate_daily_report()
        
        if pdf_file and os.path.exists(pdf_file):
            print(f"   ✅ PASS: Report Generated Successfully.")
            print(f"      File: {pdf_file}")
            results["PASS"] += 1
        else:
             print("   [ERROR] FAIL: Report Not Created.")
             results["FAIL"] += 1

    except Exception as e:
         print(f"   [ERROR] FAIL: {e}")
         results["FAIL"] += 1

    # ==================================================
    # SUMMARY
    # ==================================================
    print("\n📊 SYSTEM HEALTH SUMMARY")
    print("-----------------------")
    print(f"TOTAL TESTS: {results['PASS'] + results['FAIL']}")
    print(f"PASSED:      {results['PASS']} 🟢")
    print(f"FAILED:      {results['FAIL']} 🔴")
    
    if results['FAIL'] == 0:
        print("\n🚀 SYSTEM STATUS: [OPERATIONAL] - Ready for Deployment.")
    else:
        print("\n⚠️ SYSTEM STATUS: [DEGRADED] - Check logs.")

if __name__ == "__main__":
    run_tests()
