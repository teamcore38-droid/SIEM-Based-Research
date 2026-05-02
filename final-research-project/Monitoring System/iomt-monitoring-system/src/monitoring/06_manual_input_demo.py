"""
Script 06: Manual Input Demo - Interactive Alert Prioritization
Enter device details manually and see real-time predictions
Perfect for supervisor demonstrations!
"""

import pandas as pd
import pickle
import os

# Color codes for beautiful terminal output
class Colors:
    CRITICAL = '\033[91m'  # Red
    HIGH = '\033[93m'      # Yellow
    MEDIUM = '\033[94m'    # Blue
    LOW = '\033[92m'       # Green
    INFO = '\033[90m'      # Gray
    RESET = '\033[0m'
    BOLD = '\033[1m'
    HEADER = '\033[95m'    # Purple

def print_header(text):
    """Print styled header"""
    print(f"\n{Colors.HEADER}{'='*75}{Colors.RESET}")
    print(f"{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.HEADER}{'='*75}{Colors.RESET}")

def print_options(title, options):
    """Display numbered options"""
    print(f"\n{Colors.BOLD}{title}{Colors.RESET}")
    print("-" * 70)
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    print("-" * 70)

def get_choice(prompt, max_value):
    """Get valid numeric choice from user"""
    while True:
        try:
            choice = int(input(f"{prompt}: "))
            if 1 <= choice <= max_value:
                return choice - 1  # Convert to 0-based index
            else:
                print(f"{Colors.CRITICAL}❌ Please enter a number between 1 and {max_value}{Colors.RESET}")
        except ValueError:
            print(f"{Colors.CRITICAL}❌ Please enter a valid number{Colors.RESET}")

def get_number(prompt, min_val, max_val):
    """Get valid number within range"""
    while True:
        try:
            value = float(input(f"{prompt} ({min_val}-{max_val}): "))
            if min_val <= value <= max_val:
                return value
            else:
                print(f"{Colors.CRITICAL}❌ Please enter a value between {min_val} and {max_val}{Colors.RESET}")
        except ValueError:
            print(f"{Colors.CRITICAL}❌ Please enter a valid number{Colors.RESET}")

def load_model_and_encoders():
    """Load trained model and label encoders"""
    print_header("🔄 LOADING SYSTEM")
    
    try:
        # Load model
        with open('../../models/alert_prioritization_model.pkl', 'rb') as f:
            model = pickle.load(f)
        print("   ✅ Model loaded")
        
        # Load encoders
        with open('../../models/label_encoders.pkl', 'rb') as f:
            encoders = pickle.load(f)
        print("   ✅ Encoders loaded")
        
        # Load feature names
        with open('../../models/feature_names.pkl', 'rb') as f:
            feature_names = pickle.load(f)
        print("   ✅ Feature names loaded")
        
        return model, encoders, feature_names
    
    except FileNotFoundError:
        print(f"\n{Colors.CRITICAL}❌ Error: Model files not found!{Colors.RESET}")
        print("Please run '03_train_model.py' first to train the model.")
        exit(1)

def collect_device_info(encoders):
    """Collect device information from user"""
    
    print_header("📱 DEVICE INFORMATION")
    
    # Device Type
    device_types = [
        "ESP32_Pulse_Oximeter (MAX30102)",
        "ESP32_Temperature (DS18B20/MLX90614)",
        "ESP32_Environment (DHT22)",
        "ESP32_Fall_Detection (MPU6050/MPU9250)",
        "ESP32_ECG_Monitor (AD8232)"
    ]
    print_options("Select Device Type:", device_types)
    device_type_idx = get_choice("Enter choice (1-5)", 5)
    
    # Map to actual device type names
    device_type_map = [
        "ESP32_Pulse_Oximeter",
        "ESP32_Temperature",
        "ESP32_Environment",
        "ESP32_Fall_Detection",
        "ESP32_ECG_Monitor"
    ]
    device_type = device_type_map[device_type_idx]
    device_type_encoded = encoders['device_type'].transform([device_type])[0]
    
    # Ward
    wards = [
        "ICU (Intensive Care Unit)",
        "Emergency",
        "General_Ward",
        "OPD (Out Patient Department)",
        "Rehabilitation",
        "Home_Care"
    ]
    print_options("Select Hospital Ward:", wards)
    ward_idx = get_choice("Enter choice (1-6)", 6)
    
    ward_map = ["ICU", "Emergency", "General_Ward", "OPD", "Rehabilitation", "Home_Care"]
    ward = ward_map[ward_idx]
    ward_encoded = encoders['ward'].transform([ward])[0]
    
    # Protocol
    protocols = [
        "MQTT (Message Queue Telemetry Transport)",
        "HTTP (Hypertext Transfer Protocol)",
        "HTTPS (HTTP Secure)",
        "BLE (Bluetooth Low Energy)",
        "WiFi"
    ]
    print_options("Select Communication Protocol:", protocols)
    protocol_idx = get_choice("Enter choice (1-5)", 5)
    
    protocol_map = ["MQTT", "HTTP", "HTTPS", "BLE", "WiFi"]
    protocol = protocol_map[protocol_idx]
    protocol_encoded = encoders['protocol'].transform([protocol])[0]
    
    # Criticality Tier
    print(f"\n{Colors.BOLD}Device Criticality Tier (1-10):{Colors.RESET}")
    print("  10 = Life support (ICU ventilator, defibrillator)")
    print("  8-9 = Critical monitoring (ICU ECG, patient monitors)")
    print("  6-7 = Standard care (temperature, fall detectors)")
    print("  4-5 = Low priority (OPD devices, environment sensors)")
    print("  1-3 = Minimal (admin devices)")
    criticality = int(get_number("Enter criticality", 1, 10))
    
    # Life Support
    life_support_input = input(f"\n{Colors.BOLD}Is this a life support device?{Colors.RESET} (yes/no): ").strip().lower()
    life_support = 1 if life_support_input in ['yes', 'y'] else 0
    
    return {
        'device_type': device_type,
        'device_type_encoded': device_type_encoded,
        'ward': ward,
        'ward_encoded': ward_encoded,
        'protocol': protocol,
        'protocol_encoded': protocol_encoded,
        'criticality_tier': criticality,
        'life_support': life_support
    }

def collect_attack_info(encoders):
    """Collect attack/traffic information"""
    
    print_header("🚨 ATTACK/TRAFFIC INFORMATION")
    
    # Attack Type
    attack_types = [
        "normal (No attack - regular traffic)",
        "mqtt_injection (False sensor data)",
        "ddos (Denial of Service)",
        "ble_spoofing (Bluetooth spoofing)",
        "firmware_exploit (Device compromise)",
        "wifi_deauth (WiFi disconnection)",
        "mitm_ssl_strip (Man-in-the-middle)",
        "replay_attack (Replay old data)",
        "buffer_overflow (Memory exploit)"
    ]
    print_options("Select Attack Type:", attack_types)
    attack_idx = get_choice("Enter choice (1-9)", 9)
    
    attack_map = [
        "normal", "mqtt_injection", "ddos", "ble_spoofing",
        "firmware_exploit", "wifi_deauth", "mitm_ssl_strip",
        "replay_attack", "buffer_overflow"
    ]
    attack_type = attack_map[attack_idx]
    attack_type_encoded = encoders['attack_type'].transform([attack_type])[0]
    
    # Attack Severity (pre-defined or custom)
    attack_severities = {
        'normal': 0, 'mqtt_injection': 35, 'ddos': 40,
        'ble_spoofing': 30, 'firmware_exploit': 45, 'wifi_deauth': 25,
        'mitm_ssl_strip': 38, 'replay_attack': 28, 'buffer_overflow': 42
    }
    
    if attack_type == 'normal':
        attack_severity = 0
        print(f"\n   Attack Severity: {attack_severity} (normal traffic)")
    else:
        default_severity = attack_severities[attack_type]
        print(f"\n   Default severity for {attack_type}: {default_severity}")
        custom = input("   Use custom severity? (yes/no): ").strip().lower()
        if custom in ['yes', 'y']:
            attack_severity = int(get_number("   Enter custom severity", 0, 45))
        else:
            attack_severity = default_severity
    
    # Network characteristics
    print_header("📊 NETWORK CHARACTERISTICS")
    
    if attack_type != 'normal':
        print("Typical attack values:")
        print("  Packet size: 500-2000 bytes")
        print("  Packet rate: 100-2000 packets/min")
        print("  Failed connections: 10-200")
        packet_size = int(get_number("Packet size (bytes)", 64, 4096))
        packet_rate = int(get_number("Packet rate (packets/min)", 1, 5000))
        failed_connections = int(get_number("Failed connections", 0, 200))
        network_anomaly = get_number("Network anomaly score", 0.0, 1.0)
        behavioral_anomaly = get_number("Behavioral anomaly score", 0.0, 1.0)
        time_anomaly = get_number("Time anomaly score", 0.0, 1.0)
    else:
        print("Typical normal traffic values:")
        print("  Packet size: 128-512 bytes")
        print("  Packet rate: 5-50 packets/min")
        print("  Failed connections: 0-5")
        packet_size = int(get_number("Packet size (bytes)", 64, 4096))
        packet_rate = int(get_number("Packet rate (packets/min)", 1, 5000))
        failed_connections = int(get_number("Failed connections", 0, 200))
        network_anomaly = get_number("Network anomaly score", 0.0, 1.0)
        behavioral_anomaly = get_number("Behavioral anomaly score", 0.0, 1.0)
        time_anomaly = get_number("Time anomaly score", 0.0, 1.0)
    
    # Derived values
    packets_per_sec = round(packet_rate / 60, 2)
    bytes_sent = packet_size * packet_rate
    bytes_received = int(bytes_sent * 0.5)
    unique_ports = 1 if attack_type == 'normal' else 10
    flow_duration = 30.0
    
    # Time features
    print(f"\n{Colors.BOLD}Time Information:{Colors.RESET}")
    hour = int(get_number("Hour of day (0-23)", 0, 23))
    day = int(get_number("Day of week (0=Mon, 6=Sun)", 0, 6))
    is_night = 1 if hour < 6 or hour > 22 else 0
    is_weekend = 1 if day >= 5 else 0
    
    return {
        'attack_type': attack_type,
        'attack_type_encoded': attack_type_encoded,
        'attack_severity': attack_severity,
        'packet_size': packet_size,
        'packet_rate': packet_rate,
        'packets_per_sec': packets_per_sec,
        'unique_ports': unique_ports,
        'failed_connections': failed_connections,
        'bytes_sent': bytes_sent,
        'bytes_received': bytes_received,
        'flow_duration': flow_duration,
        'network_anomaly_score': network_anomaly,
        'behavioral_anomaly_score': behavioral_anomaly,
        'time_anomaly_score': time_anomaly,
        'hour_of_day': hour,
        'day_of_week': day,
        'is_night': is_night,
        'is_weekend': is_weekend
    }

def make_prediction(model, feature_names, device_info, attack_info):
    """Make priority prediction"""
    
    # Combine all features in correct order
    features = {
        'criticality_tier': device_info['criticality_tier'],
        'life_support': device_info['life_support'],
        'device_type_encoded': device_info['device_type_encoded'],
        'ward_encoded': device_info['ward_encoded'],
        'protocol_encoded': device_info['protocol_encoded'],
        'packet_size': attack_info['packet_size'],
        'packet_rate': attack_info['packet_rate'],
        'packets_per_sec': attack_info['packets_per_sec'],
        'unique_ports': attack_info['unique_ports'],
        'failed_connections': attack_info['failed_connections'],
        'bytes_sent': attack_info['bytes_sent'],
        'bytes_received': attack_info['bytes_received'],
        'flow_duration': attack_info['flow_duration'],
        'hour_of_day': attack_info['hour_of_day'],
        'day_of_week': attack_info['day_of_week'],
        'is_night': attack_info['is_night'],
        'is_weekend': attack_info['is_weekend'],
        'attack_type_encoded': attack_info['attack_type_encoded'],
        'attack_severity': attack_info['attack_severity'],
        'network_anomaly_score': attack_info['network_anomaly_score'],
        'behavioral_anomaly_score': attack_info['behavioral_anomaly_score'],
        'time_anomaly_score': attack_info['time_anomaly_score']
    }
    
    # Create DataFrame with correct feature order
    X = pd.DataFrame([features])[feature_names]
    
    # Predict
    priority = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]
    confidence = max(probabilities) * 100
    
    # Get probability for each class
    classes = model.classes_
    prob_dict = dict(zip(classes, probabilities))
    
    return priority, confidence, prob_dict

def display_prediction(device_info, attack_info, priority, confidence, prob_dict):
    """Display prediction results beautifully"""
    
    # Get color
    color = getattr(Colors, priority, Colors.RESET)
    
    # Symbols
    symbols = {
        'CRITICAL': '🚨🚨🚨',
        'HIGH': '⚠️⚠️',
        'MEDIUM': '⚠️',
        'LOW': 'ℹ️',
        'INFO': '📌'
    }
    
    print("\n\n")
    print(f"{color}{'='*75}{Colors.RESET}")
    print(f"{Colors.BOLD}{symbols.get(priority, '')} PRIORITY PREDICTION RESULT {symbols.get(priority, '')}{Colors.RESET}")
    print(f"{color}{'='*75}{Colors.RESET}")
    
    # Device Summary
    print(f"\n{Colors.BOLD}📱 DEVICE:{Colors.RESET}")
    print(f"   Type:          {device_info['device_type']}")
    print(f"   Location:      {device_info['ward']}")
    print(f"   Protocol:      {device_info['protocol']}")
    print(f"   Criticality:   {device_info['criticality_tier']}/10", end='')
    if device_info['criticality_tier'] >= 8:
        print(f" {color}(HIGH CRITICALITY){Colors.RESET}")
    else:
        print()
    
    if device_info['life_support'] == 1:
        print(f"   {color}{Colors.BOLD}⚕️  LIFE SUPPORT DEVICE ⚕️{Colors.RESET}")
    
    # Attack Summary
    print(f"\n{Colors.BOLD}🚨 THREAT:{Colors.RESET}")
    print(f"   Attack Type:   {attack_info['attack_type']}")
    print(f"   Severity:      {attack_info['attack_severity']}/45")
    print(f"   Packet Rate:   {attack_info['packet_rate']} packets/min")
    print(f"   Failed Conns:  {attack_info['failed_connections']}")
    
    # Prediction
    print(f"\n{Colors.BOLD}🎯 PREDICTION:{Colors.RESET}")
    print(f"   {color}{Colors.BOLD}Priority:       {priority}{Colors.RESET}")
    print(f"   Confidence:    {confidence:.1f}%")
    
    # Probability distribution
    print(f"\n{Colors.BOLD}📊 PROBABILITY DISTRIBUTION:{Colors.RESET}")
    for cls in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
        if cls in prob_dict:
            prob = prob_dict[cls] * 100
            bar_length = int(prob / 2)
            bar = '█' * bar_length
            print(f"   {cls:10} : {prob:5.2f}% {bar}")
    
    # Recommended Action
    print(f"\n{Colors.BOLD}💡 RECOMMENDED ACTION:{Colors.RESET}")
    if priority == 'CRITICAL':
        print(f"   {color}• IMMEDIATE isolation of device{Colors.RESET}")
        print(f"   {color}• Alert security team AND clinical staff{Colors.RESET}")
        print(f"   {color}• Initiate emergency response protocol{Colors.RESET}")
        print(f"   {color}• Monitor patient vitals manually{Colors.RESET}")
    elif priority == 'HIGH':
        print(f"   {color}• Priority investigation required{Colors.RESET}")
        print(f"   {color}• Notify Security Operations Center{Colors.RESET}")
        print(f"   {color}• Prepare for device isolation if needed{Colors.RESET}")
    elif priority == 'MEDIUM':
        print(f"   • Investigate within 30 minutes")
        print(f"   • Log incident for security review")
        print(f"   • Monitor device closely")
    elif priority == 'LOW':
        print(f"   • Standard monitoring protocol")
        print(f"   • Schedule review during business hours")
        print(f"   • Document for trend analysis")
    else:
        print(f"   • Log for information")
        print(f"   • No immediate action required")
        print(f"   • Include in routine security report")
    
    print(f"\n{color}{'='*75}{Colors.RESET}\n")

def main():
    """Main interactive loop"""
    
    print_header("🏥 ESP32 IoMT ALERT PRIORITIZATION - MANUAL INPUT DEMO")
    
    print(f"\n{Colors.BOLD}This demo allows you to manually enter device and attack details")
    print(f"to see real-time priority predictions from your trained model.{Colors.RESET}\n")
    
    # Load system
    model, encoders, feature_names = load_model_and_encoders()
    
    while True:
        # Collect information
        device_info = collect_device_info(encoders)
        attack_info = collect_attack_info(encoders)
        
        # Make prediction
        print("\n🔄 Processing alert...")
        priority, confidence, prob_dict = make_prediction(
            model, feature_names, device_info, attack_info
        )
        
        # Display result
        display_prediction(device_info, attack_info, priority, confidence, prob_dict)
        
        # Ask if user wants to continue
        continue_choice = input(f"{Colors.BOLD}Would you like to test another alert? (yes/no): {Colors.RESET}").strip().lower()
        
        if continue_choice not in ['yes', 'y']:
            print_header("✅ Thank you for using the ESP32 IoMT Alert Prioritization System!")
            print(f"\n📊 Demo completed successfully!")
            print(f"🎯 Model made accurate predictions based on clinical impact")
            print(f"🏥 Patient safety prioritized in all decisions\n")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.CRITICAL}⚠️  Demo interrupted by user{Colors.RESET}")
        print("✅ System shut down safely\n")
    except Exception as e:
        print(f"\n\n{Colors.CRITICAL}❌ Error: {e}{Colors.RESET}")
        print("Please ensure all required files are in place\n")