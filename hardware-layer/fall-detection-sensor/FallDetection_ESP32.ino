#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <PubSubClient.h>
#include <MPU6050.h>
#include <math.h>
#include <ArduinoJson.h>

// ═══════════════════════════════════════════
// WI-FI CONFIGURATION
// ═══════════════════════════════════════════
const char* ssid     = "Koshi";
const char* password = "123454321";

// ═══════════════════════════════════════════
// MQTT CONFIGURATION
// ═══════════════════════════════════════════
const char* mqtt_server = "10.86.251.69";
const int   mqtt_port   = 1883;
const char* telemetry_topic  = "hospital/iomt/fall";

// ═══════════════════════════════════════════
// DEVICE METADATA
// ═══════════════════════════════════════════
const char* device_id        = "FALL_ESP32_004";
const char* device_type      = "ESP32_Fall_Detector";
const char* ward             = "ICU";
bool        life_support     = false;
int         criticality_tier = 9;
const char* protocol         = "MQTT";
const char* group_id         = "GRP_001";

// Command topics
String command_topic = String("hospital/iomt/command/") + device_id;
const char* fleet_topic = "hospital/iomt/command/fleet";

// ═══════════════════════════════════════════
// CLASSIFICATION LABELS (for AI/ML pipeline)
// ═══════════════════════════════════════════
String posture_event   = "STABLE";
String ml_label        = "NORMAL";
int    priority_score  = 10;
String alert_group     = "NO_THREAT";
String attack_type     = "normal";

// ═══════════════════════════════════════════
// HARDWARE & STATE
// ═══════════════════════════════════════════
WiFiClient   espClient;
PubSubClient client(espClient);
WebServer    server(80);
MPU6050      mpu;

// STATE MANAGEMENT
bool is_isolated = false;   // Pauses transmission
bool is_quarantined = false; // Stops everything permanently

// I2C PINS
#define SDA_PIN 21
#define SCL_PIN 23

// SENSOR VARIABLES
int16_t ax, ay, az, gx, gy, gz;
float accelX, accelY, accelZ;
float gyroX, gyroY, gyroZ;
float totalAccel;

bool fallDetected  = false;
bool lowerDetected = false;

unsigned long lastPublish = 0;
unsigned long fallTime    = 0;
unsigned long lowerTime   = 0;

// FALL DETECTION THRESHOLDS
const float IMPACT_THRESHOLD     = 2.2;   // g-force spike = impact
const float LOWER_THRESHOLD      = 0.5;   // free-fall (near 0g)
const float MOVEMENT_SPIKE_THRESH = 15.0; // raw accel spike for anomaly

// ═══════════════════════════════════════════
// CLASSIFY MOTION STATE
// ═══════════════════════════════════════════
void classifyMotion() {
  if (fallDetected) {
    posture_event  = "FALL_DETECTED";
    ml_label       = "ANOMALY";
    priority_score = 95;
    alert_group    = "DEVICE_ATTACK";
    attack_type    = "fall_event";
    return;
  }
  if (lowerDetected) {
    posture_event  = "FREE_FALL";
    ml_label       = "ANOMALY";
    priority_score = 80;
    alert_group    = "DEVICE_ATTACK";
    attack_type    = "free_fall";
    return;
  }
  if (abs(accelX) > MOVEMENT_SPIKE_THRESH || 
      abs(accelY) > MOVEMENT_SPIKE_THRESH || 
      abs(accelZ) > MOVEMENT_SPIKE_THRESH) {
    posture_event  = "MOVEMENT_SPIKE";
    ml_label       = "ANOMALY";
    priority_score = 60;
    alert_group    = "DEVICE_ATTACK";
    attack_type    = "abnormal_movement";
    return;
  }
  if (totalAccel > 1.5 && totalAccel < IMPACT_THRESHOLD) {
    posture_event  = "TILTED";
    ml_label       = "NORMAL";
    priority_score = 30;
    alert_group    = "NO_THREAT";
    attack_type    = "normal";
    return;
  }
  posture_event  = "STABLE";
  ml_label       = "NORMAL";
  priority_score = 10;
  alert_group    = "NO_THREAT";
  attack_type    = "normal";
}

// ═══════════════════════════════════════════
// MQTT COMMAND HANDLER
// ═══════════════════════════════════════════
void callback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.println(message);

  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, message);
  if (error) {
    Serial.println("Failed to parse command JSON");
    return;
  }

  const char* cmd = doc["command"];
  if (cmd) {
    String commandStr = String(cmd);
    
    if (commandStr == "TEMPORARY_ISOLATE") {
      is_isolated = true;
      Serial.println("[ACTION] TEMPORARY ISOLATION ACTIVATED. Pausing transmission.");
    } 
    else if (commandStr == "PERMANENT_QUARANTINE" || commandStr == "BLOCK_COMMUNICATION") {
      is_quarantined = true;
      Serial.println("[ACTION] 🔴 PERMANENT QUARANTINE ACTIVATED. Stopping operations.");
    }
    else if (commandStr == "ROLLBACK" || commandStr == "ALL_CLEAR") {
      is_isolated = false;
      Serial.println("[ACTION] 🟢 ROLLBACK. Resuming normal operations.");
    }
    else if (commandStr == "MONITOR") {
      Serial.println("[ACTION] ⚪ MONITOR mode confirmed.");
    }
  }
}

// ═══════════════════════════════════════════
// MQTT RECONNECT
// ═══════════════════════════════════════════
void reconnectMQTT() {
  while (!client.connected() && !is_quarantined) {
    Serial.print("Connecting MQTT...");
    if (client.connect(device_id)) {
      Serial.println("connected");
      client.subscribe(command_topic.c_str());
      client.subscribe(fleet_topic);
      Serial.println("Subscribed to command topics.");
    } else {
      Serial.print("failed rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

// ═══════════════════════════════════════════
// SETUP
// ═══════════════════════════════════════════
void setup() {
  Serial.begin(115200);

  Wire.begin(SDA_PIN, SCL_PIN);
  Serial.println("Initializing MPU6050...");
  mpu.initialize();
  Serial.println("MPU6050 initialized");

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi connection failed");
    while (1);
  }

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  server.on("/", []() {
    server.send(200, "text/plain", "Fall Detection ESP32 Running");
  });
  server.begin();

  Serial.println("\ntimestamp,device_id,device_type,ward,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z,total_accel,fall_detected,posture_event,ml_label,priority_score,alert_group,attack_type");
}

// ═══════════════════════════════════════════
// LOOP
// ═══════════════════════════════════════════
void loop() {
  if (is_quarantined) {
    delay(1000);
    return;
  }

  server.handleClient();

  // ── Read MPU6050 ─────────────────────────
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  accelX = ax / 16384.0;
  accelY = ay / 16384.0;
  accelZ = az / 16384.0;
  gyroX  = gx / 131.0;
  gyroY  = gy / 131.0;
  gyroZ  = gz / 131.0;

  totalAccel = sqrt(accelX * accelX + accelY * accelY + accelZ * accelZ);

  // ── Fall Detection Logic ─────────────────
  if (totalAccel < LOWER_THRESHOLD) {
    lowerDetected = true;
    lowerTime = millis();
  }
  if (lowerDetected && (millis() - lowerTime < 1000) && totalAccel > IMPACT_THRESHOLD) {
    fallDetected = true;
    fallTime = millis();
  }
  if (lowerDetected && (millis() - lowerTime > 1000) && !fallDetected) {
    lowerDetected = false;
  }
  if (fallDetected && (millis() - fallTime > 3000)) {
    fallDetected = false;
    lowerDetected = false;
  }

  // ── Classify motion state ────────────────
  classifyMotion();

  // ── MQTT Keepalive ───────────────────────
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  // ── Publish every 1 second ───────────────
  if (millis() - lastPublish > 1000) {
    lastPublish = millis();

    if (is_isolated) {
       Serial.println("[ISOLATED] Transmission paused.");
       return; 
    }

    String src_ip = WiFi.localIP().toString();

    StaticJsonDocument<1024> doc;
    doc["timestamp"] = millis();
    doc["device_id"] = device_id;
    doc["device_type"] = device_type;
    doc["ward"] = ward;
    doc["life_support"] = life_support;
    doc["criticality_tier"] = criticality_tier;
    doc["protocol"] = protocol;
    doc["group_id"] = group_id;
    doc["src_ip"] = src_ip;
    doc["dst_port"] = mqtt_port;
    doc["accel_x"] = round(accelX * 1000.0) / 1000.0;
    doc["accel_y"] = round(accelY * 1000.0) / 1000.0;
    doc["accel_z"] = round(accelZ * 1000.0) / 1000.0;
    doc["gyro_x"] = round(gyroX * 1000.0) / 1000.0;
    doc["gyro_y"] = round(gyroY * 1000.0) / 1000.0;
    doc["gyro_z"] = round(gyroZ * 1000.0) / 1000.0;
    doc["total_acceleration"] = round(totalAccel * 1000.0) / 1000.0;
    doc["fall_detected"] = fallDetected;
    doc["posture_event"] = posture_event;
    doc["ml_label"] = ml_label;
    doc["priority_score"] = priority_score;
    doc["alert_group"] = alert_group;
    doc["attack_type"] = attack_type;

    char jsonBuffer[1024];
    serializeJson(doc, jsonBuffer);

    bool ok = client.publish(telemetry_topic, jsonBuffer);

    // CSV serial output
    Serial.print(millis());           Serial.print(",");
    Serial.print(device_id);          Serial.print(",");
    Serial.print(device_type);        Serial.print(",");
    Serial.print(ward);               Serial.print(",");
    Serial.print(accelX, 3);          Serial.print(",");
    Serial.print(accelY, 3);          Serial.print(",");
    Serial.print(accelZ, 3);          Serial.print(",");
    Serial.print(gyroX, 3);           Serial.print(",");
    Serial.print(gyroY, 3);           Serial.print(",");
    Serial.print(gyroZ, 3);           Serial.print(",");
    Serial.print(totalAccel, 3);      Serial.print(",");
    Serial.print(fallDetected);       Serial.print(",");
    Serial.print(posture_event);      Serial.print(",");
    Serial.print(ml_label);           Serial.print(",");
    Serial.print(priority_score);     Serial.print(",");
    Serial.print(alert_group);        Serial.print(",");
    Serial.println(attack_type);

    if (!ok) {
      Serial.println("MQTT publish FAILED");
    }
  }

  delay(100);
}
