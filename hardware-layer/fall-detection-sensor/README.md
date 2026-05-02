# Fall Detection Sensor — ESP32 + MPU6050

## Hardware
- **MCU:** ESP32
- **Sensor:** MPU6050 (6-axis Accelerometer + Gyroscope)
- **I2C Pins:** SDA=GPIO21, SCL=GPIO23

## MQTT
- **Topic:** `hospital/iomt/fall`
- **Interval:** Every 1 second
- **Buffer:** 1024 bytes

## Fall Detection Algorithm
Two-phase detection:
1. **Free-fall phase:** Total acceleration drops below 0.5g
2. **Impact phase:** Within 1 second, spike above 2.2g confirms fall
3. **Auto-reset:** Fall flag clears after 3 seconds

## Classification Logic
| Condition | Posture Event | Severity |
|-----------|--------------|----------|
| Free-fall → Impact spike | `FALL_DETECTED` | 🔴 95 |
| Free-fall (no impact yet) | `FREE_FALL` | 🔴 80 |
| Accel > 15g on any axis | `MOVEMENT_SPIKE` | 🟡 60 |
| 1.5g < Total < 2.2g | `TILTED` | 🟢 30 |
| Normal range | `STABLE` | 🟢 10 |

## JSON Payload
```json
{
  "timestamp": 12345,
  "device_id": "FALL_ESP32_004",
  "device_type": "ESP32_Fall_Detector",
  "ward": "ICU",
  "life_support": false,
  "criticality_tier": 9,
  "accel_x": 0.123, "accel_y": -0.456, "accel_z": 0.987,
  "gyro_x": 1.23, "gyro_y": -2.34, "gyro_z": 0.56,
  "total_acceleration": 1.082,
  "fall_detected": false,
  "posture_event": "STABLE",
  "ml_label": "NORMAL",
  "priority_score": 10,
  "alert_group": "NO_THREAT",
  "attack_type": "normal"
}
```

## Arduino Libraries Required
- `WiFi.h`, `WebServer.h`, `Wire.h`
- `PubSubClient.h`
- `MPU6050.h`
