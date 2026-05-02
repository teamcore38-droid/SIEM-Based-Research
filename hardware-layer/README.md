# Hardware Layer — IoMT Telemetry / Sensors

This layer contains the ESP32 firmware for all IoMT medical devices that generate telemetry data and send it to the AI/ML Layer via MQTT.

## Devices

| Device | Folder | Sensor | MQTT Topic | Status |
|--------|--------|--------|------------|--------|
| Heart Rate Monitor | `heart-rate-sensor/` | MAX30105 | `hospital/iomt/pulse` | ✅ Implemented |
| ECG Monitor | `ecg-sensor/` | AD8232 | `hospital/iomt/ecg` | ✅ Implemented |
| Temperature Monitor | `temperature-sensor/` | DS18B20/DHT22 | `hospital/iomt/temperature` | ✅ Implemented |
| Fall Detection | `fall-detection-sensor/` | MPU6050 | `hospital/iomt/fall` | ✅ Implemented |

## Data Flow
```
ESP32 Sensor → WiFi → MQTT Broker (Mosquitto) → AI/ML Layer (mqtt_to_mongodb.py)
```

## Helper Scripts
Each device folder may include Python helper scripts:
- `MQTT_LOGS.py` — Subscribes to MQTT and logs data to CSV
- `Real_Time.py` — Real-time MQTT data viewer

## Control Path
Each ESP32 sketch subscribes to a device-specific command topic and the fleet topic. That makes the hardware layer compatible with:
- direct MQTT publishing from the backend
- a Node-RED bridge that accepts HTTP or MQTT from the backend and republishes control commands to the device topic
