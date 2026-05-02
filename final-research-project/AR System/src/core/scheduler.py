
import time
import schedule
import logging
import os
import sys

# Add the 'modules' directory to path so we can import reporting
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
from reporting import ReportGenerator

# Configuration
REPORT_DESTINATION = r"c:\Users\yasim\OneDrive - Sri Lanka Institute of Information Technology (1)\Desktop\AR System\Wazuh_Admin_Portal_Reports"

def job():
    print("\n[INFO] SCHEDULER: Starting Daily Report Generation...")
    try:
        # Initialize compiler
        # Note: We need to ensure it finds the audit log correctly from src/core/scheduler.py -> src/core/ars_audit.log
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(base_dir, '..', '..', 'logs', 'ars_audit.log')
        
        reporter = ReportGenerator(log_file=log_path)
        
        # Override the report directory to the "Wazuh Portal" folder
        reporter.report_dir = REPORT_DESTINATION
        if not os.path.exists(reporter.report_dir):
            os.makedirs(reporter.report_dir)
            
        pdf_path = reporter.generate_daily_report()
        
        if pdf_path:
            print(f"[SUCCESS] UPLOAD: Report delivered to Wazuh Portal Folder: {pdf_path}")
            # Here you would add the API call to push to real Wazuh API if credentials provided
    except Exception as e:
        print(f"[ERROR] SCHEDULER ERROR: {e}")

def run_scheduler():
    print("[INFO] ARS AUTOMATION SERVICE STARTED")
    print("   Task: Generate PDF Report")
    print("   Schedule: Every 24 Hours (Daily @ 23:59)")
    
    # Schedule the job
    schedule.every().day.at("23:59").do(job)
    
    # Also run once immediately for verification if needed (Uncomment to test)
    job()

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # We need to install 'schedule' lib first normally, but assuming user has standard libs or we ask to install
    # For now, we will assume standard simple loop if schedule missing, but let's try to include it.
    run_scheduler() 
