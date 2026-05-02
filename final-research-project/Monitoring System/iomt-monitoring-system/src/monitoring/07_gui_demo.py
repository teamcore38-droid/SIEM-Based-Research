"""
Script 07: GUI Demo - Visual Alert Prioritization System
Beautiful graphical interface for demonstrations
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import pickle
from datetime import datetime

class AlertPrioritizationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 IoMT Alert Prioritization System")
        self.root.geometry("1000x800")
        self.root.configure(bg='#f0f0f0')
        
        # Load model and encoders
        self.load_model()
        
        # Color scheme
        self.colors = {
            'CRITICAL': '#FF0000',
            'HIGH': '#FFA500',
            'MEDIUM': '#0066CC',
            'LOW': '#00CC00',
            'INFO': '#808080',
            'bg': '#f0f0f0',
            'header': '#2c3e50',
            'button': '#3498db'
        }
        
        # Create UI
        self.create_header()
        self.create_input_section()
        self.create_result_section()
        self.create_footer()
    
    def load_model(self):
        """Load trained model and encoders"""
        try:
            with open('../../models/alert_prioritization_model.pkl', 'rb') as f:
                self.model = pickle.load(f)
            
            with open('../../models/label_encoders.pkl', 'rb') as f:
                self.encoders = pickle.load(f)
            
            with open('../../models/feature_names.pkl', 'rb') as f:
                self.feature_names = pickle.load(f)
            
            print("✅ Model and encoders loaded successfully")
        
        except FileNotFoundError:
            messagebox.showerror("Error", "Model files not found!\nPlease run 03_train_model.py first.")
            self.root.destroy()
    
    def create_header(self):
        """Create header section"""
        header_frame = tk.Frame(self.root, bg=self.colors['header'], height=80)
        header_frame.pack(fill='x', pady=(0, 20))
        
        title = tk.Label(
            header_frame,
            text="🏥 ESP32 IoMT Alert Prioritization System",
            font=('Arial', 20, 'bold'),
            bg=self.colors['header'],
            fg='white',
            pady=20
        )
        title.pack()
        
        subtitle = tk.Label(
            header_frame,
            text="Real-time SIEM-Based Monitoring with Clinical Impact Assessment",
            font=('Arial', 10),
            bg=self.colors['header'],
            fg='#ecf0f1'
        )
        subtitle.pack()
    
    def create_input_section(self):
        """Create input form section"""
        # Main container
        input_container = tk.Frame(self.root, bg=self.colors['bg'])
        input_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Left column - Device Info
        left_frame = tk.LabelFrame(
            input_container,
            text="📱 Device Information",
            font=('Arial', 12, 'bold'),
            bg='white',
            fg=self.colors['header'],
            padx=15,
            pady=15
        )
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Device Type
        tk.Label(left_frame, text="Device Type:", font=('Arial', 10, 'bold'), bg='white').grid(row=0, column=0, sticky='w', pady=5)
        self.device_type_var = tk.StringVar()
        device_types = [
            "ESP32_Pulse_Oximeter (MAX30102)",
            "ESP32_Temperature (DS18B20/MLX90614)",
            "ESP32_Environment (DHT22)",
            "ESP32_Fall_Detection (MPU6050/MPU9250)",
            "ESP32_ECG_Monitor (AD8232)"
        ]
        self.device_type_combo = ttk.Combobox(left_frame, textvariable=self.device_type_var, values=device_types, state='readonly', width=35)
        self.device_type_combo.grid(row=0, column=1, pady=5, padx=5)
        self.device_type_combo.current(0)
        
        # Ward
        tk.Label(left_frame, text="Hospital Ward:", font=('Arial', 10, 'bold'), bg='white').grid(row=1, column=0, sticky='w', pady=5)
        self.ward_var = tk.StringVar()
        wards = ["ICU", "Emergency", "General_Ward", "OPD", "Rehabilitation", "Home_Care"]
        self.ward_combo = ttk.Combobox(left_frame, textvariable=self.ward_var, values=wards, state='readonly', width=35)
        self.ward_combo.grid(row=1, column=1, pady=5, padx=5)
        self.ward_combo.current(0)
        
        # Protocol
        tk.Label(left_frame, text="Protocol:", font=('Arial', 10, 'bold'), bg='white').grid(row=2, column=0, sticky='w', pady=5)
        self.protocol_var = tk.StringVar()
        protocols = ["MQTT", "HTTP", "HTTPS", "BLE", "WiFi"]
        self.protocol_combo = ttk.Combobox(left_frame, textvariable=self.protocol_var, values=protocols, state='readonly', width=35)
        self.protocol_combo.grid(row=2, column=1, pady=5, padx=5)
        self.protocol_combo.current(0)
        
        # Criticality
        tk.Label(left_frame, text="Criticality (1-10):", font=('Arial', 10, 'bold'), bg='white').grid(row=3, column=0, sticky='w', pady=5)
        self.criticality_var = tk.IntVar(value=8)
        criticality_scale = tk.Scale(left_frame, from_=1, to=10, orient='horizontal', variable=self.criticality_var, length=250, bg='white')
        criticality_scale.grid(row=3, column=1, pady=5, padx=5)
        
        # Life Support
        tk.Label(left_frame, text="Life Support:", font=('Arial', 10, 'bold'), bg='white').grid(row=4, column=0, sticky='w', pady=5)
        self.life_support_var = tk.BooleanVar(value=True)
        life_support_check = tk.Checkbutton(left_frame, variable=self.life_support_var, bg='white', text="This is a life-critical device")
        life_support_check.grid(row=4, column=1, sticky='w', pady=5, padx=5)
        
        # Right column - Attack Info
        right_frame = tk.LabelFrame(
            input_container,
            text="🚨 Attack Information",
            font=('Arial', 12, 'bold'),
            bg='white',
            fg=self.colors['header'],
            padx=15,
            pady=15
        )
        right_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Attack Type
        tk.Label(right_frame, text="Attack Type:", font=('Arial', 10, 'bold'), bg='white').grid(row=0, column=0, sticky='w', pady=5)
        self.attack_type_var = tk.StringVar()
        attack_types = [
            "normal",
            "mqtt_injection",
            "ddos",
            "ble_spoofing",
            "firmware_exploit",
            "wifi_deauth",
            "mitm_ssl_strip",
            "replay_attack",
            "buffer_overflow"
        ]
        self.attack_type_combo = ttk.Combobox(right_frame, textvariable=self.attack_type_var, values=attack_types, state='readonly', width=35)
        self.attack_type_combo.grid(row=0, column=1, pady=5, padx=5)
        self.attack_type_combo.current(4)  # firmware_exploit
        
        # Attack Severity
        tk.Label(right_frame, text="Attack Severity:", font=('Arial', 10, 'bold'), bg='white').grid(row=1, column=0, sticky='w', pady=5)
        self.attack_severity_var = tk.IntVar(value=45)
        severity_scale = tk.Scale(right_frame, from_=0, to=45, orient='horizontal', variable=self.attack_severity_var, length=250, bg='white')
        severity_scale.grid(row=1, column=1, pady=5, padx=5)
        
        # Packet Rate
        tk.Label(right_frame, text="Packet Rate:", font=('Arial', 10, 'bold'), bg='white').grid(row=2, column=0, sticky='w', pady=5)
        self.packet_rate_var = tk.IntVar(value=1500)
        packet_rate_scale = tk.Scale(right_frame, from_=1, to=5000, orient='horizontal', variable=self.packet_rate_var, length=250, bg='white')
        packet_rate_scale.grid(row=2, column=1, pady=5, padx=5)
        
        # Failed Connections
        tk.Label(right_frame, text="Failed Connections:", font=('Arial', 10, 'bold'), bg='white').grid(row=3, column=0, sticky='w', pady=5)
        self.failed_conn_var = tk.IntVar(value=150)
        failed_scale = tk.Scale(right_frame, from_=0, to=200, orient='horizontal', variable=self.failed_conn_var, length=250, bg='white')
        failed_scale.grid(row=3, column=1, pady=5, padx=5)
        
        # Network Anomaly
        tk.Label(right_frame, text="Network Anomaly:", font=('Arial', 10, 'bold'), bg='white').grid(row=4, column=0, sticky='w', pady=5)
        self.network_anomaly_var = tk.DoubleVar(value=0.95)
        network_scale = tk.Scale(right_frame, from_=0.0, to=1.0, resolution=0.01, orient='horizontal', variable=self.network_anomaly_var, length=250, bg='white')
        network_scale.grid(row=4, column=1, pady=5, padx=5)
        
        # Analyze Button
        analyze_btn = tk.Button(
            input_container,
            text="🎯 ANALYZE ALERT",
            command=self.analyze_alert,
            font=('Arial', 14, 'bold'),
            bg=self.colors['button'],
            fg='white',
            padx=30,
            pady=15,
            relief='raised',
            cursor='hand2'
        )
        analyze_btn.pack(pady=20)
    
    def create_result_section(self):
        """Create result display section"""
        result_frame = tk.LabelFrame(
            self.root,
            text="🎯 Prediction Results",
            font=('Arial', 12, 'bold'),
            bg='white',
            fg=self.colors['header'],
            padx=20,
            pady=20
        )
        result_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Priority Display
        priority_container = tk.Frame(result_frame, bg='white')
        priority_container.pack(pady=10)
        
        tk.Label(priority_container, text="PRIORITY:", font=('Arial', 12, 'bold'), bg='white').pack(side='left', padx=5)
        
        self.priority_label = tk.Label(
            priority_container,
            text="---",
            font=('Arial', 24, 'bold'),
            bg='white',
            fg='gray',
            width=12
        )
        self.priority_label.pack(side='left', padx=10)
        
        # Confidence Display
        confidence_container = tk.Frame(result_frame, bg='white')
        confidence_container.pack(pady=5)
        
        tk.Label(confidence_container, text="Confidence:", font=('Arial', 10), bg='white').pack(side='left', padx=5)
        
        self.confidence_label = tk.Label(
            confidence_container,
            text="---%",
            font=('Arial', 14, 'bold'),
            bg='white',
            fg='gray'
        )
        self.confidence_label.pack(side='left', padx=5)
        
        # Probability Bars
        self.prob_frame = tk.Frame(result_frame, bg='white')
        self.prob_frame.pack(pady=15, fill='x')
        
        # Recommendation Display
        self.recommendation_text = tk.Text(
            result_frame,
            height=6,
            font=('Arial', 10),
            bg='#f9f9f9',
            relief='sunken',
            borderwidth=2,
            wrap='word'
        )
        self.recommendation_text.pack(fill='x', pady=10)
        self.recommendation_text.insert('1.0', 'Click "ANALYZE ALERT" to see predictions and recommendations...')
        self.recommendation_text.config(state='disabled')
    
    def create_footer(self):
        """Create footer section"""
        footer = tk.Frame(self.root, bg=self.colors['header'], height=40)
        footer.pack(fill='x')
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info = tk.Label(
            footer,
            text=f"ESP32 IoMT Monitoring System | Model: Random Forest (~90% accuracy) | Last Updated: {timestamp}",
            font=('Arial', 8),
            bg=self.colors['header'],
            fg='white',
            pady=10
        )
        info.pack()
    
    def analyze_alert(self):
        """Analyze the alert and display prediction"""
        try:
            # Extract device type
            device_type_full = self.device_type_var.get()
            device_type = device_type_full.split(' ')[0]
            device_type_encoded = self.encoders['device_type'].transform([device_type])[0]
            
            # Extract other inputs
            ward = self.ward_var.get()
            ward_encoded = self.encoders['ward'].transform([ward])[0]
            
            protocol = self.protocol_var.get()
            protocol_encoded = self.encoders['protocol'].transform([protocol])[0]
            
            criticality = self.criticality_var.get()
            life_support = 1 if self.life_support_var.get() else 0
            
            attack_type = self.attack_type_var.get()
            attack_type_encoded = self.encoders['attack_type'].transform([attack_type])[0]
            
            attack_severity = self.attack_severity_var.get()
            packet_rate = self.packet_rate_var.get()
            failed_connections = self.failed_conn_var.get()
            network_anomaly = self.network_anomaly_var.get()
            
            # Calculate derived features
            packet_size = 1500  # Default
            packets_per_sec = round(packet_rate / 60, 2)
            bytes_sent = packet_size * packet_rate
            bytes_received = int(bytes_sent * 0.5)
            unique_ports = 10 if attack_type != 'normal' else 1
            flow_duration = 30.0
            behavioral_anomaly = 0.85
            time_anomaly = 0.35
            hour_of_day = 14
            day_of_week = 2
            is_night = 0
            is_weekend = 0
            
            # Create feature vector
            features = {
                'criticality_tier': criticality,
                'life_support': life_support,
                'device_type_encoded': device_type_encoded,
                'ward_encoded': ward_encoded,
                'protocol_encoded': protocol_encoded,
                'packet_size': packet_size,
                'packet_rate': packet_rate,
                'packets_per_sec': packets_per_sec,
                'unique_ports': unique_ports,
                'failed_connections': failed_connections,
                'bytes_sent': bytes_sent,
                'bytes_received': bytes_received,
                'flow_duration': flow_duration,
                'hour_of_day': hour_of_day,
                'day_of_week': day_of_week,
                'is_night': is_night,
                'is_weekend': is_weekend,
                'attack_type_encoded': attack_type_encoded,
                'attack_severity': attack_severity,
                'network_anomaly_score': network_anomaly,
                'behavioral_anomaly_score': behavioral_anomaly,
                'time_anomaly_score': time_anomaly
            }
            
            # Create DataFrame
            X = pd.DataFrame([features])[self.feature_names]
            
            # Predict
            priority = self.model.predict(X)[0]
            probabilities = self.model.predict_proba(X)[0]
            confidence = max(probabilities) * 100
            
            # Get probability dict
            classes = self.model.classes_
            prob_dict = dict(zip(classes, probabilities))
            
            # Update display
            self.update_display(priority, confidence, prob_dict, device_type, ward, attack_type, life_support)
        
        except Exception as e:
            messagebox.showerror("Error", f"Prediction failed:\n{str(e)}")
    
    def update_display(self, priority, confidence, prob_dict, device_type, ward, attack_type, life_support):
        """Update the result display"""
        # Update priority label
        color = self.colors.get(priority, 'gray')
        self.priority_label.config(text=priority, fg=color)
        
        # Update confidence
        self.confidence_label.config(text=f"{confidence:.1f}%", fg=color)
        
        # Clear and redraw probability bars
        for widget in self.prob_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.prob_frame, text="Probability Distribution:", font=('Arial', 10, 'bold'), bg='white').pack(anchor='w', pady=5)
        
        for cls in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
            if cls in prob_dict:
                prob = prob_dict[cls] * 100
                
                bar_container = tk.Frame(self.prob_frame, bg='white')
                bar_container.pack(fill='x', pady=2)
                
                label = tk.Label(bar_container, text=f"{cls:10}", font=('Arial', 9), bg='white', width=12, anchor='w')
                label.pack(side='left')
                
                bar_bg = tk.Frame(bar_container, bg='#e0e0e0', height=20, width=400)
                bar_bg.pack(side='left', padx=5)
                
                bar_width = int(prob * 4)
                bar_color = self.colors.get(cls, 'gray')
                bar = tk.Frame(bar_bg, bg=bar_color, height=20, width=bar_width)
                bar.place(x=0, y=0)
                
                prob_label = tk.Label(bar_container, text=f"{prob:5.2f}%", font=('Arial', 9), bg='white')
                prob_label.pack(side='left', padx=5)
        
        # Update recommendations
        self.recommendation_text.config(state='normal')
        self.recommendation_text.delete('1.0', 'end')
        
        recommendations = self.get_recommendations(priority, device_type, ward, attack_type, life_support)
        self.recommendation_text.insert('1.0', recommendations)
        self.recommendation_text.config(state='disabled')
    
    def get_recommendations(self, priority, device_type, ward, attack_type, life_support):
        """Generate recommendations based on priority"""
        recommendations = f"📋 RECOMMENDED ACTIONS FOR {priority} PRIORITY ALERT\n\n"
        recommendations += f"Device: {device_type} | Ward: {ward} | Attack: {attack_type}\n"
        
        if life_support:
            recommendations += "⚕️ LIFE SUPPORT DEVICE - Extra caution required!\n\n"
        else:
            recommendations += "\n"
        
        if priority == 'CRITICAL':
            recommendations += "🚨 IMMEDIATE ACTIONS REQUIRED:\n"
            recommendations += "• IMMEDIATELY isolate the device from network\n"
            recommendations += "• Alert Security Operations Center (SOC)\n"
            recommendations += "• Notify clinical staff and IT security team\n"
            recommendations += "• Initiate emergency response protocol\n"
            recommendations += "• Monitor patient vitals manually if life support\n"
            recommendations += "• Document all actions in incident log\n"
        
        elif priority == 'HIGH':
            recommendations += "⚠️ PRIORITY INVESTIGATION:\n"
            recommendations += "• Investigate within 15 minutes\n"
            recommendations += "• Notify Security Operations Center\n"
            recommendations += "• Prepare device isolation if threat escalates\n"
            recommendations += "• Review device logs and network traffic\n"
            recommendations += "• Inform ward supervisor\n"
        
        elif priority == 'MEDIUM':
            recommendations += "📊 STANDARD RESPONSE:\n"
            recommendations += "• Investigate within 30 minutes\n"
            recommendations += "• Log incident for security review\n"
            recommendations += "• Monitor device activity closely\n"
            recommendations += "• Check for similar alerts on other devices\n"
        
        elif priority == 'LOW':
            recommendations += "ℹ️ ROUTINE MONITORING:\n"
            recommendations += "• Standard monitoring protocol\n"
            recommendations += "• Schedule review during business hours\n"
            recommendations += "• Document for trend analysis\n"
            recommendations += "• No immediate action required\n"
        
        else:  # INFO
            recommendations += "📝 INFORMATIONAL:\n"
            recommendations += "• Log for information only\n"
            recommendations += "• Include in routine security report\n"
            recommendations += "• No action required\n"
        
        return recommendations


def main():
    """Main function to run the GUI"""
    root = tk.Tk()
    app = AlertPrioritizationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()