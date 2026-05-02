# Temperature Sensor — ESP32 + DS18B20/DHT22
# This folder is reserved for the Temperature Machine firmware.
# Add your Temperature_ESP32.ino file here.
#
# Expected MQTT Topic: hospital/iomt/temperature
# Expected JSON payload should include:
#   - device_id, device_type, ward, life_support, criticality_tier
#   - protocol, src_ip, dst_port
#   - temperature_celsius, temperature_status, ml_label
#   - priority_score, alert_group, attack_type
