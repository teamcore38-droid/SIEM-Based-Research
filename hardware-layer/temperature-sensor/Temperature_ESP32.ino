#include <WiFi.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ArduinoJson.h>

// --- 1. WI-FI CONFIGURATION ---
const char* ssid     = "Firaz";
const char* password = "poiuytrew";

// --- MQTT CONFIGURATION ---
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* telemetry_topic = "hospital/iomt/temperature";

// --- DEVICE METADATA ---
const char* device_id        = "TEMP_ESP32_003";
const char* device_type      = "ESP32_Temperature_Sensor";
const char* ward             = "General Ward";
bool        life_support     = false;
int         criticality_tier = 5;
const char* protocol         = "MQTT";

// Command topics
String command_topic = String("hospital/iomt/command/") + device_id;
const char* fleet_topic = "hospital/iomt/command/fleet";

// --- TEMPERATURE PIN ---
#define ONE_WIRE_BUS 4
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// --- SENSOR VARIABLES ---
float temperature_celsius = 0.0;

// --- STATUS VARIABLES ---
String        ml_label       = "NORMAL";
int           priority_score = 10;
String        alert_group    = "NO_THREAT";
String        attack_type    = "normal";

// --- STATE MANAGEMENT ---
bool is_isolated = false;   // Pauses transmission
bool is_quarantined = false; // Stops everything permanently

// --- LOG TIMER ---
unsigned long lastLogTime  = 0;
const int     LOG_INTERVAL = 2000;

WiFiClient   espClient;
PubSubClient client(espClient);

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
// CLASSIFICATION LOGIC
// ═══════════════════════════════════════════
void classifyTemperature() {
  if (temperature_celsius < -100 || temperature_celsius == 85.0 || temperature_celsius == -127.0) {
    // Sensor error values
    ml_label       = "ANOMALY";
    priority_score = 90;
    alert_group    = "DEVICE_ATTACK";
    attack_type    = "sensor_malfunction";
    return;
  }

  if (temperature_celsius > 40.0) { // High Fever
    ml_label       = "ANOMALY";
    priority_score = 80;
    alert_group    = "DEVICE_ATTACK";
    attack_type    = "high_temperature";
  } else if (temperature_celsius < 35.0) { // Hypothermia
    ml_label       = "ANOMALY";
    priority_score = 80;
    alert_group    = "DEVICE_ATTACK";
    attack_type    = "low_temperature";
  } else {
    ml_label       = "NORMAL";
    priority_score = 10;
    alert_group    = "NO_THREAT";
    attack_type    = "normal";
  }
}

// ═══════════════════════════════════════════
// SETUP
// ═══════════════════════════════════════════
void setup() {
  Serial.begin(115200);

  sensors.begin();

  // Connect WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected! IP: " + WiFi.localIP().toString());

  // MQTT setup
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

// ═══════════════════════════════════════════
// LOOP
// ═══════════════════════════════════════════
void loop() {
  if (is_quarantined) {
    delay(1000);
    return;
  }

  unsigned long now = millis();

  // ── Step 1: Read Sensor ──────────
  sensors.requestTemperatures();
  temperature_celsius = sensors.getTempCByIndex(0);

  // ── Step 2: Classify Status ──────────
  classifyTemperature();

  // ── Step 3: MQTT keep alive ──────────────
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  // ── Step 4: Log every 2 seconds ──────────
  if (now - lastLogTime >= LOG_INTERVAL) {
    lastLogTime = now;

    if (is_isolated) {
       Serial.println("[ISOLATED] Transmission paused.");
       return; 
    }

    String src_ip = WiFi.localIP().toString();

    StaticJsonDocument<512> doc;
    doc["timestamp"] = now;
    doc["device_id"] = device_id;
    doc["device_type"] = device_type;
    doc["ward"] = ward;
    doc["life_support"] = life_support;
    doc["criticality_tier"] = criticality_tier;
    doc["protocol"] = protocol;
    doc["src_ip"] = src_ip;
    doc["dst_port"] = mqtt_port;
    doc["temperature_celsius"] = temperature_celsius;
    doc["ml_label"] = ml_label;
    doc["priority_score"] = priority_score;
    doc["alert_group"] = alert_group;
    doc["attack_type"] = attack_type;

    char jsonBuffer[512];
    serializeJson(doc, jsonBuffer);

    // Publish to MQTT
    client.publish(telemetry_topic, jsonBuffer);
    Serial.println(jsonBuffer);
  }
}
