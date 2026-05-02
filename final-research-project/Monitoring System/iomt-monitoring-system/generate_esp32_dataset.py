import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

class CustomIoMTDatasetGenerator:
    """
    Custom IoMT Dataset Generator for MMM Ukasha's Project
    Based on actual ESP32-based IoMT devices being used
    """
    
    def __init__(self, num_samples=100000):
        self.num_samples = num_samples
        self.current_time = datetime(2024, 1, 15, 8, 0, 0)
        
        # YOUR ACTUAL DEVICES - Based on your project specification
        self.devices = [
            # ICU - Critical Care Monitoring
            {'id': 'ICU_ESP32_HR_001', 'type': 'ESP32_Pulse_Oximeter', 'sensor': 'MAX30102', 'ward': 'ICU', 'criticality': 10, 'life_support': True, 'ip': '192.168.1.50', 'protocol': 'MQTT'},
            {'id': 'ICU_ESP32_HR_002', 'type': 'ESP32_Pulse_Oximeter', 'sensor': 'MAX30102', 'ward': 'ICU', 'criticality': 10, 'life_support': True, 'ip': '192.168.1.51', 'protocol': 'MQTT'},
            {'id': 'ICU_ESP32_ECG_001', 'type': 'ESP32_ECG_Monitor', 'sensor': 'AD8232', 'ward': 'ICU', 'criticality': 10, 'life_support': True, 'ip': '192.168.1.52', 'protocol': 'MQTT'},
            {'id': 'ICU_ESP32_ECG_002', 'type': 'ESP32_ECG_Monitor', 'sensor': 'AD8232', 'ward': 'ICU', 'criticality': 10, 'life_support': True, 'ip': '192.168.1.53', 'protocol': 'BLE'},
            {'id': 'ICU_ESP32_TEMP_001', 'type': 'ESP32_Temperature', 'sensor': 'DS18B20', 'ward': 'ICU', 'criticality': 9, 'life_support': False, 'ip': '192.168.1.54', 'protocol': 'MQTT'},
            {'id': 'ICU_ESP32_TEMP_002', 'type': 'ESP32_Temperature', 'sensor': 'MLX90614', 'ward': 'ICU', 'criticality': 9, 'life_support': False, 'ip': '192.168.1.55', 'protocol': 'HTTP'},
            
            # Emergency Department
            {'id': 'ER_ESP32_HR_001', 'type': 'ESP32_Pulse_Oximeter', 'sensor': 'MAX30102', 'ward': 'Emergency', 'criticality': 9, 'life_support': False, 'ip': '192.168.1.60', 'protocol': 'MQTT'},
            {'id': 'ER_ESP32_ECG_001', 'type': 'ESP32_ECG_Monitor', 'sensor': 'AD8232', 'ward': 'Emergency', 'criticality': 9, 'life_support': False, 'ip': '192.168.1.61', 'protocol': 'MQTT'},
            {'id': 'ER_ESP32_FALL_001', 'type': 'ESP32_Fall_Detection', 'sensor': 'MPU6050', 'ward': 'Emergency', 'criticality': 8, 'life_support': False, 'ip': '192.168.1.62', 'protocol': 'MQTT'},
            {'id': 'ER_ESP32_TEMP_001', 'type': 'ESP32_Temperature', 'sensor': 'DS18B20', 'ward': 'Emergency', 'criticality': 8, 'life_support': False, 'ip': '192.168.1.63', 'protocol': 'MQTT'},
            
            # General Ward - Patient Monitoring
            {'id': 'WARD_ESP32_HR_001', 'type': 'ESP32_Pulse_Oximeter', 'sensor': 'MAX30102', 'ward': 'General_Ward', 'criticality': 7, 'life_support': False, 'ip': '192.168.1.70', 'protocol': 'MQTT'},
            {'id': 'WARD_ESP32_HR_002', 'type': 'ESP32_Pulse_Oximeter', 'sensor': 'MAX30102', 'ward': 'General_Ward', 'criticality': 7, 'life_support': False, 'ip': '192.168.1.71', 'protocol': 'BLE'},
            {'id': 'WARD_ESP32_TEMP_001', 'type': 'ESP32_Temperature', 'sensor': 'MLX90614', 'ward': 'General_Ward', 'criticality': 6, 'life_support': False, 'ip': '192.168.1.72', 'protocol': 'HTTP'},
            {'id': 'WARD_ESP32_TEMP_002', 'type': 'ESP32_Temperature', 'sensor': 'DS18B20', 'ward': 'General_Ward', 'criticality': 6, 'life_support': False, 'ip': '192.168.1.73', 'protocol': 'MQTT'},
            {'id': 'WARD_ESP32_FALL_001', 'type': 'ESP32_Fall_Detection', 'sensor': 'MPU9250', 'ward': 'General_Ward', 'criticality': 7, 'life_support': False, 'ip': '192.168.1.74', 'protocol': 'WiFi'},
            {'id': 'WARD_ESP32_FALL_002', 'type': 'ESP32_Fall_Detection', 'sensor': 'MPU6050', 'ward': 'General_Ward', 'criticality': 7, 'life_support': False, 'ip': '192.168.1.75', 'protocol': 'MQTT'},
            
            # OPD - Outpatient Monitoring
            {'id': 'OPD_ESP32_HR_001', 'type': 'ESP32_Pulse_Oximeter', 'sensor': 'MAX30102', 'ward': 'OPD', 'criticality': 5, 'life_support': False, 'ip': '192.168.1.100', 'protocol': 'BLE'},
            {'id': 'OPD_ESP32_TEMP_001', 'type': 'ESP32_Temperature', 'sensor': 'MLX90614', 'ward': 'OPD', 'criticality': 4, 'life_support': False, 'ip': '192.168.1.101', 'protocol': 'HTTP'},
            {'id': 'OPD_ESP32_TEMP_002', 'type': 'ESP32_Temperature', 'sensor': 'DS18B20', 'ward': 'OPD', 'criticality': 4, 'life_support': False, 'ip': '192.168.1.102', 'protocol': 'HTTPS'},
            
            # Elderly Care / Rehabilitation
            {'id': 'REHAB_ESP32_FALL_001', 'type': 'ESP32_Fall_Detection', 'sensor': 'MPU6050', 'ward': 'Rehabilitation', 'criticality': 6, 'life_support': False, 'ip': '192.168.1.110', 'protocol': 'WiFi'},
            {'id': 'REHAB_ESP32_FALL_002', 'type': 'ESP32_Fall_Detection', 'sensor': 'MPU9250', 'ward': 'Rehabilitation', 'criticality': 6, 'life_support': False, 'ip': '192.168.1.111', 'protocol': 'MQTT'},
            
            # Home Care / Remote Monitoring
            {'id': 'HOME_ESP32_HR_001', 'type': 'ESP32_Pulse_Oximeter', 'sensor': 'MAX30102', 'ward': 'Home_Care', 'criticality': 5, 'life_support': False, 'ip': '10.0.0.50', 'protocol': 'HTTPS'},
            {'id': 'HOME_ESP32_ECG_001', 'type': 'ESP32_ECG_Monitor', 'sensor': 'AD8232', 'ward': 'Home_Care', 'criticality': 6, 'life_support': False, 'ip': '10.0.0.51', 'protocol': 'HTTPS'},
            {'id': 'HOME_ESP32_TEMP_001', 'type': 'ESP32_Temperature', 'sensor': 'DS18B20', 'ward': 'Home_Care', 'criticality': 4, 'life_support': False, 'ip': '10.0.0.52', 'protocol': 'HTTP'},
            {'id': 'HOME_ESP32_FALL_001', 'type': 'ESP32_Fall_Detection', 'sensor': 'MPU6050', 'ward': 'Home_Care', 'criticality': 5, 'life_support': False, 'ip': '10.0.0.53', 'protocol': 'WiFi'},
        ]
        
        # Attack types targeting ESP32 IoMT devices
        self.attack_types = {
            'normal': {
                'severity': 0,
                'packet_size_range': (128, 512),  # Smaller packets for ESP32
                'packet_rate_range': (5, 30),
                'unique_ports': 1,
                'failed_connections': 0,
                'description': 'Normal device operation'
            },
            'mqtt_injection': {
                'severity': 35,
                'packet_size_range': (256, 1024),
                'packet_rate_range': (10, 50),
                'unique_ports': 1,
                'failed_connections': 0,
                'description': 'Malicious MQTT data injection (false vitals)'
            },
            'ble_spoofing': {
                'severity': 30,
                'packet_size_range': (64, 256),
                'packet_rate_range': (20, 80),
                'unique_ports': 1,
                'failed_connections': 0,
                'description': 'BLE MAC address spoofing attack'
            },
            'wifi_deauth': {
                'severity': 25,
                'packet_size_range': (60, 128),
                'packet_rate_range': (100, 500),
                'unique_ports': 1,
                'failed_connections': (50, 200),
                'description': 'WiFi deauthentication attack'
            },
            'ddos': {
                'severity': 40,
                'packet_size_range': (1400, 1500),
                'packet_rate_range': (500, 2000),
                'unique_ports': 1,
                'failed_connections': 0,
                'description': 'DDoS attack on ESP32 device'
            },
            'firmware_exploit': {
                'severity': 45,
                'packet_size_range': (512, 2048),
                'packet_rate_range': (10, 40),
                'unique_ports': (2, 5),
                'failed_connections': 0,
                'description': 'ESP32 firmware exploitation'
            },
            'mitm_ssl_strip': {
                'severity': 38,
                'packet_size_range': (256, 1024),
                'packet_rate_range': (15, 60),
                'unique_ports': 2,
                'failed_connections': 0,
                'description': 'MITM SSL stripping on HTTPS connections'
            },
            'replay_attack': {
                'severity': 28,
                'packet_size_range': (128, 512),
                'packet_rate_range': (30, 100),
                'unique_ports': 1,
                'failed_connections': 0,
                'description': 'Replay attack on sensor data'
            },
            'buffer_overflow': {
                'severity': 42,
                'packet_size_range': (2048, 4096),
                'packet_rate_range': (5, 20),
                'unique_ports': 1,
                'failed_connections': (2, 10),
                'description': 'Buffer overflow attempt on ESP32'
            },
        }
        
        self.attacker_ips = [
            '203.94.50.15',
            '198.51.100.42',
            '10.0.0.88',
            '45.33.32.156',
        ]
    
    def generate_sensor_data(self, device):
        """Generate realistic sensor readings based on device type"""
        sensor_data = {}
        
        if device['type'] == 'ESP32_Pulse_Oximeter':
            sensor_data['heart_rate_bpm'] = random.randint(60, 100)
            sensor_data['spo2_percentage'] = random.randint(95, 100)
            sensor_data['ppg_signal_quality'] = random.uniform(0.7, 1.0)
            
        elif device['type'] == 'ESP32_Temperature':
            sensor_data['body_temp_celsius'] = round(random.uniform(36.5, 37.5), 1)
            if 'DHT22' in device.get('sensor', ''):
                sensor_data['ambient_temp_celsius'] = round(random.uniform(20, 28), 1)
                sensor_data['humidity_percentage'] = random.randint(40, 70)
                
        elif device['type'] == 'ESP32_Fall_Detection':
            sensor_data['accel_x'] = round(random.uniform(-2.0, 2.0), 3)
            sensor_data['accel_y'] = round(random.uniform(-2.0, 2.0), 3)
            sensor_data['accel_z'] = round(random.uniform(8.0, 11.0), 3)
            sensor_data['gyro_x'] = round(random.uniform(-10, 10), 2)
            sensor_data['gyro_y'] = round(random.uniform(-10, 10), 2)
            sensor_data['gyro_z'] = round(random.uniform(-10, 10), 2)
            sensor_data['fall_detected'] = False
            
        elif device['type'] == 'ESP32_ECG_Monitor':
            sensor_data['heart_rate_bpm'] = random.randint(60, 100)
            sensor_data['r_peak_detected'] = True
            sensor_data['ecg_signal_quality'] = random.uniform(0.6, 1.0)
        
        return sensor_data
    
    def generate_normal_traffic(self, num_samples):
        """Generate normal ESP32 IoMT device traffic"""
        data = []
        
        for _ in range(num_samples):
            device = random.choice(self.devices)
            attack_config = self.attack_types['normal']
            
            timestamp = self.current_time + timedelta(seconds=random.randint(0, 86400))
            
            packet_size = random.randint(*attack_config['packet_size_range'])
            packet_rate = random.randint(*attack_config['packet_rate_range'])
            
            # Generate sensor readings
            sensor_data = self.generate_sensor_data(device)
            
            row = {
                'timestamp': timestamp,
                'alert_id': f"A_{len(data):06d}",
                'device_id': device['id'],
                'device_type': device['type'],
                'sensor_type': device['sensor'],
                'ward': device['ward'],
                'criticality_tier': device['criticality'],
                'life_support': device['life_support'],
                'src_ip': device['ip'],
                'dst_ip': '192.168.1.1',  # Gateway/MQTT broker
                'src_port': random.randint(40000, 60000),
                'dst_port': 1883 if device['protocol'] == 'MQTT' else (443 if device['protocol'] == 'HTTPS' else 80),
                'protocol': device['protocol'],
                'packet_size': packet_size,
                'packet_rate': packet_rate,
                'packets_per_sec': round(packet_rate / 60, 2),
                'unique_ports': attack_config['unique_ports'],
                'failed_connections': attack_config['failed_connections'],
                'bytes_sent': packet_size * packet_rate,
                'bytes_received': int(packet_size * packet_rate * 0.3),
                'flow_duration': random.uniform(0.01, 2.0),
                'hour_of_day': timestamp.hour,
                'day_of_week': timestamp.weekday(),
                'is_night': 1 if timestamp.hour < 6 or timestamp.hour > 22 else 0,
                'is_weekend': 1 if timestamp.weekday() >= 5 else 0,
                'attack_type': 'normal',
                'attack_severity': 0,
                **sensor_data
            }
            
            data.append(row)
        
        return data
    
    def generate_attack_traffic(self, attack_type, num_samples, target_devices=None):
        """Generate attack traffic targeting ESP32 devices"""
        data = []
        attack_config = self.attack_types[attack_type]
        
        if target_devices is None:
            target_devices = random.sample(self.devices, min(5, len(self.devices)))
        
        campaign_id = f"CAMP_{attack_type[:4].upper()}_{random.randint(1000, 9999)}"
        attacker_ip = random.choice(self.attacker_ips)
        base_time = self.current_time + timedelta(hours=random.randint(0, 24))
        
        for i in range(num_samples):
            device = random.choice(target_devices)
            
            timestamp = base_time + timedelta(seconds=random.randint(0, 300))
            
            if isinstance(attack_config['packet_size_range'], tuple):
                packet_size = random.randint(*attack_config['packet_size_range'])
            else:
                packet_size = attack_config['packet_size_range']
            
            if isinstance(attack_config['packet_rate_range'], tuple):
                packet_rate = random.randint(*attack_config['packet_rate_range'])
            else:
                packet_rate = attack_config['packet_rate_range']
            
            if isinstance(attack_config['unique_ports'], tuple):
                unique_ports = random.randint(*attack_config['unique_ports'])
            else:
                unique_ports = attack_config['unique_ports']
            
            if isinstance(attack_config['failed_connections'], tuple):
                failed_connections = random.randint(*attack_config['failed_connections'])
            else:
                failed_connections = attack_config['failed_connections']
            
            # Generate malicious sensor data for injection attacks
            sensor_data = {}
            if attack_type == 'mqtt_injection' and device['type'] == 'ESP32_Pulse_Oximeter':
                sensor_data['heart_rate_bpm'] = random.randint(200, 250)  # Abnormally high
                sensor_data['spo2_percentage'] = random.randint(50, 70)   # Dangerously low
                sensor_data['ppg_signal_quality'] = 0.0
            elif attack_type == 'mqtt_injection' and device['type'] == 'ESP32_Temperature':
                sensor_data['body_temp_celsius'] = round(random.uniform(40.0, 42.0), 1)  # Fever
            else:
                sensor_data = self.generate_sensor_data(device)
            
            row = {
                'timestamp': timestamp,
                'alert_id': f"A_{len(data) + 100000:06d}",
                'device_id': device['id'],
                'device_type': device['type'],
                'sensor_type': device['sensor'],
                'ward': device['ward'],
                'criticality_tier': device['criticality'],
                'life_support': device['life_support'],
                'src_ip': attacker_ip,
                'dst_ip': device['ip'],
                'src_port': random.randint(40000, 60000),
                'dst_port': 1883 if attack_type in ['mqtt_injection'] else random.randint(1, 65535),
                'protocol': device['protocol'],
                'packet_size': packet_size,
                'packet_rate': packet_rate,
                'packets_per_sec': round(packet_rate / 60, 2),
                'unique_ports': unique_ports,
                'failed_connections': failed_connections,
                'bytes_sent': packet_size * packet_rate,
                'bytes_received': 0 if attack_type in ['ddos', 'wifi_deauth'] else int(packet_size * packet_rate * 0.2),
                'flow_duration': random.uniform(0.001, 0.1) if attack_type == 'ddos' else random.uniform(0.1, 2.0),
                'hour_of_day': timestamp.hour,
                'day_of_week': timestamp.weekday(),
                'is_night': 1 if timestamp.hour < 6 or timestamp.hour > 22 else 0,
                'is_weekend': 1 if timestamp.weekday() >= 5 else 0,
                'attack_type': attack_type,
                'attack_severity': attack_config['severity'],
                'attack_description': attack_config['description'],
                'campaign_id': campaign_id,
                **sensor_data
            }
            
            data.append(row)
        
        return data
    
    def calculate_priority_label(self, row):
        """Calculate priority label based on multiple factors"""
        score = 0
        
        score += row['criticality_tier'] * 5
        score += row['attack_severity']
        
        if row['life_support']:
            score += 15  # Higher bonus for life support ESP32 devices
        
        # ESP32-specific adjustments
        if row['device_type'] in ['ESP32_ECG_Monitor', 'ESP32_Pulse_Oximeter']:
            score *= 1.3  # Vital signs monitoring is critical
        
        if row['attack_type'] in ['mqtt_injection', 'firmware_exploit']:
            score *= 1.2  # These attacks can cause direct patient harm
        
        ward_multiplier = {
            'ICU': 1.3,
            'Emergency': 1.2,
            'General_Ward': 1.0,
            'OPD': 0.9,
            'Rehabilitation': 0.9,
            'Home_Care': 0.8
        }
        score *= ward_multiplier.get(row['ward'], 1.0)
        
        if score >= 85:
            return 'CRITICAL'
        elif score >= 65:
            return 'HIGH'
        elif score >= 45:
            return 'MEDIUM'
        elif score >= 25:
            return 'LOW'
        else:
            return 'INFO'
    
    def assign_group_ids(self, df):
        """Assign group IDs for alert grouping"""
        df['time_window'] = pd.to_datetime(df['timestamp']).dt.floor('5min')
        
        df['group_key'] = (
            df['attack_type'].astype(str) + '_' +
            df['src_ip'].astype(str) + '_' +
            df['time_window'].astype(str) + '_' +
            df['ward'].astype(str)
        )
        
        attack_mask = df['attack_type'] != 'normal'
        unique_groups = df[attack_mask]['group_key'].unique()
        group_mapping = {key: f"GRP_{i:04d}" for i, key in enumerate(unique_groups)}
        
        df.loc[attack_mask, 'group_id'] = df.loc[attack_mask, 'group_key'].map(group_mapping)
        df.loc[~attack_mask, 'group_id'] = None
        
        df = df.drop(['group_key', 'time_window'], axis=1)
        
        return df
    
    def generate_complete_dataset(self):
        """Generate complete dataset"""
        print("🚀 Generating ESP32 IoMT Monitoring Dataset...")
        print("=" * 70)
        print("📱 ESP32 Devices: Pulse Oximeter, Temperature, Fall Detection, ECG")
        print("=" * 70)
        
        all_data = []
        
        normal_samples = int(self.num_samples * 0.60)
        print(f"\n📊 Generating {normal_samples:,} normal traffic samples...")
        normal_data = self.generate_normal_traffic(normal_samples)
        all_data.extend(normal_data)
        print(f"   ✅ Normal traffic: {len(normal_data):,} samples")
        
        attack_distribution = {
            'mqtt_injection': 0.10,
            'ddos': 0.08,
            'firmware_exploit': 0.05,
            'ble_spoofing': 0.06,
            'wifi_deauth': 0.05,
            'mitm_ssl_strip': 0.03,
            'replay_attack': 0.02,
            'buffer_overflow': 0.01,
        }
        
        for attack_type, percentage in attack_distribution.items():
            attack_samples = int(self.num_samples * percentage)
            print(f"🔴 Generating {attack_samples:,} {attack_type} samples...")
            
            if attack_type in ['firmware_exploit', 'mqtt_injection', 'ddos']:
                critical_devices = [d for d in self.devices if d['criticality'] >= 8]
                target_devices = critical_devices if random.random() < 0.7 else None
            else:
                target_devices = None
            
            attack_data = self.generate_attack_traffic(attack_type, attack_samples, target_devices)
            all_data.extend(attack_data)
            print(f"   ✅ {attack_type}: {len(attack_data):,} samples")
        
        print("\n🔄 Creating DataFrame...")
        df = pd.DataFrame(all_data)
        
        print("🏷️  Calculating priority labels...")
        df['priority_label'] = df.apply(self.calculate_priority_label, axis=1)
        
        print("🔗 Assigning group IDs...")
        df = self.assign_group_ids(df)
        
        print("⚙️  Adding anomaly scores...")
        df['network_anomaly_score'] = np.where(
            df['attack_type'] == 'normal',
            np.random.uniform(0, 0.2, len(df)),
            np.random.uniform(0.6, 1.0, len(df))
        )
        
        df['behavioral_anomaly_score'] = np.where(
            df['attack_type'] == 'normal',
            np.random.uniform(0, 0.15, len(df)),
            np.random.uniform(0.5, 0.95, len(df))
        )
        
        df['time_anomaly_score'] = np.where(
            (df['is_night'] == 1) & (df['attack_type'] != 'normal'),
            np.random.uniform(0.3, 0.6, len(df)),
            np.where(
                df['attack_type'] != 'normal',
                np.random.uniform(0.1, 0.4, len(df)),
                np.random.uniform(0, 0.1, len(df))
            )
        )
        
        print("🔀 Shuffling dataset...")
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        df['alert_id'] = [f"A_{i:06d}" for i in range(len(df))]
        
        print("\n" + "=" * 70)
        print("✅ ESP32 Dataset Generation Complete!")
        print("=" * 70)
        
        return df
    
    def print_dataset_summary(self, df):
        """Print comprehensive dataset summary"""
        print("\n📊 ESP32 IOMT DATASET SUMMARY")
        print("=" * 70)
        print(f"Total Samples: {len(df):,}")
        print(f"Total Features: {len(df.columns)}")
        
        print("\n📱 ESP32 DEVICE TYPE DISTRIBUTION:")
        print(df['device_type'].value_counts())
        
        print("\n🔬 SENSOR TYPE DISTRIBUTION:")
        print(df['sensor_type'].value_counts())
        
        print("\n🏢 WARD DISTRIBUTION:")
        print(df['ward'].value_counts())
        
        print("\n🌐 PROTOCOL DISTRIBUTION:")
        print(df['protocol'].value_counts())
        
        print("\n🚨 ATTACK TYPE DISTRIBUTION:")
        print(df['attack_type'].value_counts())
        
        print("\n🎯 PRIORITY LABEL DISTRIBUTION:")
        priority_counts = df['priority_label'].value_counts()
        for priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
            count = priority_counts.get(priority, 0)
            percentage = count / len(df) * 100
            print(f"{priority:10} : {count:6,} ({percentage:5.2f}%)")
        
        print("\n" + "=" * 70)


if __name__ == "__main__":
    generator = CustomIoMTDatasetGenerator(num_samples=100000)
    
    df = generator.generate_complete_dataset()
    
    generator.print_dataset_summary(df)
    
    output_file = 'esp32_iomt_monitoring_dataset.csv'
    print(f"\n💾 Saving dataset to '{output_file}'...")
    df.to_csv(output_file, index=False)
    print(f"✅ Dataset saved successfully!")
    
    sample_file = 'esp32_iomt_sample_1000.csv'
    df.sample(n=min(1000, len(df)), random_state=42).to_csv(sample_file, index=False)
    print(f"✅ Sample dataset saved to '{sample_file}'")
    
    print("\n👀 FIRST 5 ROWS:")
    print(df.head(5)[['alert_id', 'device_id', 'device_type', 'sensor_type', 'attack_type', 'priority_label']])
    
    print("\n🎉 Your custom ESP32 IoMT dataset is ready!")
