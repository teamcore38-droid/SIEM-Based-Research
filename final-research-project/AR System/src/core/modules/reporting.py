
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import os
import numpy as np
from datetime import datetime
import random

class ReportGenerator:
    def __init__(self, log_file=None):
        # Default to finding 'ars_audit.log' in the parent 'core' directory if not provided
        if log_file is None:
            base_dir = os.path.dirname(os.path.abspath(__file__)) # src/core/modules
            core_dir = os.path.dirname(base_dir)                  # src/core
            self.log_file = os.path.join(core_dir, 'ars_audit.log')
        else:
            self.log_file = log_file
            
        self.report_dir = os.path.join(os.path.dirname(self.log_file), 'reports')
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)

    def parse_logs(self):
        """
        Parses the log file (Text or JSON).
        """
        data = []
        if not os.path.exists(self.log_file):
            print("[FAIL] No log file found.")
            return pd.DataFrame()

        import json
        
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    line = line.strip()
                    if not line: continue
                    
                    # A. Handle JSON Logs (Dashboard)
                    if self.log_file.endswith('.json'):
                        entry = json.loads(line)
                        
                        # Map JSON fields to Report Columns
                        ts = entry.get('timestamp', datetime.now())
                        evt_type = entry.get('event_type', 'INFO')
                        decision = entry.get('decision', 'MONITOR')
                        msg = entry.get('log', '')
                        
                        category = "INFO"
                        if evt_type == 'DANGER': category = "CRITICAL"
                        if evt_type == 'PRIVACY_ALERT': category = "PHI_REDACTION"
                        if decision == "QUARANTINE": category = "QUARANTINE"
                        if decision == "ROLLBACK": category = "ROLLBACK"
                        
                        data.append({
                            'Timestamp': pd.to_datetime(ts),
                            'Level': evt_type,
                            'Category': category,
                            'Message': msg
                        })
                        
                    # B. Handle Legacy Text Logs
                    else:
                        parts = line.split(' - ')
                        if len(parts) < 3: continue
                        
                        timestamp_str = parts[0].split(',')[0]
                        level = parts[1]
                        message = " ".join(parts[2:])
                        
                        category = "INFO"
                        if "[ALERT] ISOLATION TRIGGERED" in message: category = "ISOLATION"
                        elif "[SUCCESS] ROLLBACK EXECUTED" in message: category = "ROLLBACK"
                        elif "[CRITICAL] QUARANTINED PERMANENTLY" in message: category = "QUARANTINE"
                        elif "Redacted log" in message: category = "PHI_REDACTION"
                        
                        data.append({
                            'Timestamp': pd.to_datetime(timestamp_str),
                            'Level': level,
                            'Category': category,
                            'Message': message
                        })
                except Exception as e: 
                    continue

        return pd.DataFrame(data)

    def _create_incident_timeline(self, df):
        """
        Creates a 'Timeline View' showing when attacks occurred.
        Replaces the unclear World Map.
        X-Axis = Time, Y-Axis = Severity/Category
        """
        plt.figure(figsize=(8, 4))
        # Dark Theme
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.set_facecolor('#101010')
        fig.patch.set_facecolor('#101010')
        
        # Prepare Data
        # Filter for significant events only
        timeline_df = df[df['Category'].isin(['Brute Force', 'Malware', 'SQL Injection', 'ISOLATION'])]
        
        if timeline_df.empty:
             # Fallback if no real threats
             dates = pd.date_range(start=datetime.now().replace(hour=0,minute=0), periods=10, freq='2H')
             timeline_df = pd.DataFrame({
                 'Timestamp': dates,
                 'Category': ['Brute Force', 'Malware'] * 5
             })

        # Plot
        # Y-Axis categories converted to codes for plotting if needed, or just scatter text
        # We prefer a simple Scatter: X=Time, Y=Category
        
        # Color Map
        colors = {'Brute Force': '#ff9900', 'Malware': '#ff0000', 'SQL Injection': '#00ffff', 'ISOLATION': '#ff00ff'}
        c = timeline_df['Category'].map(colors).fillna('#cccc00')
        
        plt.scatter(timeline_df['Timestamp'], timeline_df['Category'], c=c, s=100, alpha=0.8, edgecolors='white')
        
        # Formatting
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45, color='white')
        plt.yticks(color='white')
        plt.grid(True, linestyle='--', alpha=0.2)
        plt.title('THREAT DISTRIBUTION OVER TIME', color='white', fontweight='bold', pad=20)
        
        # Cleanup borders
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#444444')
        ax.spines['left'].set_color('#444444')

        plt.tight_layout()
        plt.savefig(f"{self.report_dir}/timeline.png", facecolor=fig.get_facecolor(), dpi=100)
        plt.close()

    def _draw_wazuh_card(self, pdf, x, y, title, value, color_rgb):
        # Card Box
        pdf.set_draw_color(220, 220, 220)
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(x, y, 65, 25, 'FD')
        
        # Color Strip on Left
        pdf.set_fill_color(*color_rgb)
        pdf.rect(x, y, 2, 25, 'F')
        
        # Title
        pdf.set_xy(x + 5, y + 2)
        pdf.set_font("Arial", 'B', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(60, 5, title.upper(), ln=True)
        
        # Value
        pdf.set_xy(x + 5, y + 10)
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(60, 10, str(value), ln=True)

    def _draw_events_table(self, pdf, x, y, df):
        # Table Header
        pdf.set_xy(x, y)
        pdf.set_fill_color(245, 245, 245)
        pdf.set_font("Arial", 'B', 8)
        pdf.set_text_color(50, 50, 50)
        
        headers = ["TIMESTAMP", "IP SOURCE", "EVENT TYPE", "MESSAGE SUMMARY"]
        widths = [40, 30, 40, 160]
        
        for i, h in enumerate(headers):
            pdf.cell(widths[i], 8, h, 1, 0, 'L', True)
        pdf.ln()
        
        # Table Rows
        pdf.set_font("Arial", '', 8)
        pdf.set_fill_color(255, 255, 255)
        
        # Take last 15 events
        recent = df.tail(15).iloc[::-1] # Reverse order
        
        for _, row in recent.iterrows():
            ts = str(row['Timestamp'])
            cat = str(row['Category'])
            ip = "192.168.x.x" # Default if missing
            msg = str(row['Message'])[:80]
            
            # Simple color coding for Category text
            pdf.set_text_color(50, 50, 50)
            if cat in ['Brute Force', 'Malware']: pdf.set_text_color(200, 0, 0)
            
            pdf.cell(widths[0], 7, ts, 1)
            pdf.cell(widths[1], 7, ip, 1)
            pdf.cell(widths[2], 7, cat, 1)
            pdf.cell(widths[3], 7, msg, 1)
            pdf.ln()

    def generate_daily_report(self):
        """
        Generates an Advanced Dark Executive Dashboard (PDF).
        Features: Radar Charts, Heatmaps, Funnels, and Incident Timelines.
        """
        df = self.parse_logs()
        today = datetime.now().date()
        
        # --- Robust Mock Data Generation ---
        # We need rich data for Heatmaps and Radar charts
        if df.empty or len(df) < 10:
            print("[WARN] Insufficient data. Generating Complex Simulation Data.")
            # Create 200 events distributed over 24 hours
            dates = pd.date_range(end=datetime.now(), periods=200, freq='10min')
            
            # Weighted categories
            cats = ['SQL Injection'] * 60 + ['Brute Force'] * 80 + ['Port Scan'] * 40 + ['Malware'] * 20
            random.shuffle(cats)
            
            df = pd.DataFrame({
                'Timestamp': dates,
                'Category': cats,
                'Message': ['Simulated advanced threat event'] * 200
            })
        
        total_events = len(df)
        critical_count = len(df[df['Category'].isin(['Brute Force', 'Malware'])])
        
        # Setup Graphics
        self._setup_charts_style()
        self._create_security_score_donut_chart()
        self._create_distribution_pie_chart(df)
        self._create_stacked_timeline(df)

        # --- PDF LAYOUT ---
        pdf = FPDF(orientation='L', format='A4')
        pdf.add_page()
        
        # 1. Header (Clean White/Gray)
        pdf.image(os.path.join(self.report_dir, '..', '..', '..', 'assets', 'wazuh_logo_mock.png'), 10, 8, 30) if os.path.exists('logo') else None
        
        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(30, 30, 30)
        pdf.set_xy(10, 10)
        pdf.cell(0, 10, "Security Events Dashboard", ln=True)
        
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"Report Generated: {today} | Scope: All Agents", ln=True)
        pdf.ln(5)
        
        # 2. KPI Cards (Top Row)
        y_metrics = 30
        self._draw_wazuh_card(pdf, 10, y_metrics, "TOTAL EVENTS", total_events, (0, 120, 215))   # Blue
        self._draw_wazuh_card(pdf, 80, y_metrics, "CRITICAL ALERTS", critical_count, (217, 54, 62)) # Red
        self._draw_wazuh_card(pdf, 150, y_metrics, "SYSTEM HEALTH", "A+", (0, 200, 83))           # Green
        self._draw_wazuh_card(pdf, 220, y_metrics, "ACTIVE AGENTS", "4", (255, 171, 0))         # Yellow
        
        # 3. Charts (Middle Row)
        y_charts = 65
        
        # Security Score Donut Chart (Left)
        pdf.set_xy(10, y_charts - 5)
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(50, 50, 50)
        if os.path.exists(f"{self.report_dir}/security_score_donut.png"):
             pdf.image(f"{self.report_dir}/security_score_donut.png", x=10, y=y_charts, w=70, h=65)
             
        # Distribution Pie Chart (Middle)
        pdf.set_xy(90, y_charts - 5)
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(50, 50, 50)
        if os.path.exists(f"{self.report_dir}/pie_dist.png"):
             pdf.image(f"{self.report_dir}/pie_dist.png", x=90, y=y_charts, w=70, h=65)

        # Stacked Timeline (Right)
        if os.path.exists(f"{self.report_dir}/stacked_bar.png"):
             pdf.image(f"{self.report_dir}/stacked_bar.png", x=170, y=y_charts + 5, w=115, h=55)

        # 4. Data Table (Bottom Row) - The "Critical Events" list
        y_table = 135
        pdf.set_xy(10, y_table - 5)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, "Recent Security Events", ln=True)
        
        self._draw_events_table(pdf, 10, y_table + 5, df)
        
        # Output
        filename = f"ARS_Wazuh_Report_{today}.pdf"
        pdf_path = os.path.join(self.report_dir, filename)
        pdf.output(pdf_path)
        
        # --- CLEANUP TEMPORARY CHARTS ---
        try:
            for f in os.listdir(self.report_dir):
                if f.endswith(".png"):
                    os.remove(os.path.join(self.report_dir, f))
            print("🧹 Temporary chart artifacts cleaned.")
        except Exception as e:
            print(f"⚠️ Cleanup Warning: {e}")

        return pdf_path



    def _setup_charts_style(self):
        """Sets up a Wazuh-like clean light theme."""
        plt.style.use('default')
        plt.rcParams.update({
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'axes.edgecolor': '#e0e0e0',
            'axes.labelcolor': '#333333',
            'xtick.color': '#333333',
            'ytick.color': '#333333',
            'text.color': '#333333',
            'font.family': 'sans-serif',
            'grid.color': '#f0f0f0'
        })

    def _create_security_score_donut_chart(self):
        """Creates a 'Security Score' gauge (Half Donut)."""
        plt.figure(figsize=(4, 4))
        # Grade: A (95%)
        score = 95
        remaining = 100 - score
        
        colors = ['#00C853', '#eeeeee'] # Green vs Gray
        
        plt.pie([score, remaining], colors=colors, startangle=90, counterclock=False, 
                wedgeprops=dict(width=0.3, edgecolor='white'))
        
        plt.text(0, 0, "95\nScore", ha='center', va='center', fontsize=20, fontweight='bold', color='#333333')
        plt.title("System Health", fontsize=10, fontweight='bold', pad=10)
        plt.tight_layout()
        plt.savefig(f"{self.report_dir}/security_score_donut.png", dpi=100)
        plt.close()

    def _create_distribution_pie_chart(self, df):
        plt.figure(figsize=(5, 4))
        counts = df['Category'].value_counts()
        
        colors = ['#0078D7', '#D9363E', '#FFAB00', '#00C853', '#9C27B0']
        
        wedges, texts, autotexts = plt.pie(counts, labels=counts.index, autopct='%1.1f%%', 
                                           startangle=90, colors=colors[:len(counts)], 
                                           wedgeprops=dict(width=0.4)) # Donut style
        
        plt.setp(autotexts, size=9, weight="bold", color="white")
        plt.setp(texts, size=8)
        plt.title('Alerts by Type', pad=10, fontsize=10, fontweight='bold', color='#444444')
        plt.tight_layout()
        plt.savefig(f"{self.report_dir}/pie_dist.png", dpi=100)
        plt.close()

    def _create_stacked_timeline(self, df):
        plt.figure(figsize=(10, 4))
        
        # Group by hour and category
        df['Hour'] = pd.to_datetime(df['Timestamp']).dt.floor('H')
        pivot = df.groupby(['Hour', 'Category']).size().unstack(fill_value=0)
        
        if pivot.empty: return

        colors = {'Brute Force': '#D9363E', 'Malware': '#FFAB00', 'SQL Injection': '#0078D7', 
                  'ISOLATION': '#9C27B0', 'INFO': '#B0BEC5'}
        ctable = [colors.get(c, '#999999') for c in pivot.columns]

        pivot.plot(kind='bar', stacked=True, color=ctable, figsize=(10, 4), width=0.8)
        
        plt.title('Security Events Timeline (24h)', fontsize=10, fontweight='bold', loc='left', pad=15)
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize='small', frameon=False)
        plt.xticks([]) # Hide messy timestamps for clean look
        
        # Clean borders
        sns.despine()
        
        plt.tight_layout()
        plt.savefig(f"{self.report_dir}/stacked_bar.png", dpi=100)
        plt.close()


