#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- 1. WI-FI CONFIGURATION ---
const char* ssid     = "Koshi";
const char* password = "123454321";

// --- MQTT CONFIGURATION ---
const char* mqtt_server = "10.86.251.69";
const int mqtt_port = 1883;
const char* telemetry_topic = "hospital/iomt/ecg";

// --- DEVICE METADATA ---
const char* device_id        = "ECG_ESP32_001";
const char* device_type      = "ESP32_ECG_Monitor";
const char* ward             = "Ward 01";
bool        life_support     = false;
int         criticality_tier = 10;
const char* protocol         = "MQTT";

// Command topics
String command_topic = String("hospital/iomt/command/") + device_id;
const char* fleet_topic = "hospital/iomt/command/fleet";

// --- ECG PIN DEFINITIONS ---
#define ECG_PIN   34
#define LO_PLUS   32
#define LO_MINUS  33

// --- HEART RATE VARIABLES ---
const byte    RATE_SIZE      = 10;
int           rates[10];
byte          rateSpot       = 0;
unsigned long lastBeat       = 0;
float         beatsPerMinute = 0;
int           beatAvg        = 0;
int           ecgRawValue    = 0;
int           prevValue      = 0;
bool          risingEdge     = false;

// --- STATUS VARIABLES ---
String        leadStatus     = "DISCONNECTED";
String        ecgStatus      = "WAITING";
String        ml_label       = "NORMAL";
int           priority_score = 10;
String        alert_group    = "NO_THREAT";
String        attack_type    = "normal";

// --- STATE MANAGEMENT ---
bool is_isolated = false;   // Pauses transmission
bool is_quarantined = false; // Stops everything permanently

// --- 2 SECOND LOG TIMER ---
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
// HEART RATE DETECTION
// ═══════════════════════════════════════════
void detectHeartRate(int value, unsigned long now) {
  int threshold = 2800;

  if (value > threshold && prevValue <= threshold) {
    risingEdge = true;
  }

  if (risingEdge && value < prevValue) {
    risingEdge = false;

    if (lastBeat > 0) {
      unsigned long rr = now - lastBeat;
      if (rr > 300 && rr < 2000) {
        beatsPerMinute = 60000.0 / rr;

        if (beatsPerMinute > 20 && beatsPerMinute < 255) {
          rates[rateSpot++] = (int)beatsPerMinute;
          rateSpot %= RATE_SIZE;

          int total = 0;
          for (byte x = 0; x < RATE_SIZE; x++) total += rates[x];
          beatAvg = total / RATE_SIZE;
        }
      }
    }
    lastBeat = now;
  }
  prevValue = value;
}

// ═══════════════════════════════════════════
// ECG CLASSIFICATION
// ═══════════════════════════════════════════
void classifyECG() {

  // ── Electrodes NOT on body ────────────────
  if (leadStatus == "DISCONNECTED") {
    ecgStatus      = "LEAD_OFF";
    ecgRawValue    = 0;      // force 0 when not connected
    beatAvg        = 0;      // force 0 when not connected
    ml_label       = "ANOMALY";
    priority_score = 95;
    alert_group    = "DEVICE_ATTACK";
    attack_type    = "lead_disconnected";
    return;
  }

  // ── Electrodes ON body ────────────────────
  if (beatAvg == 0) {
    ecgStatus      = "INITIALIZING";
    ml_label       = "NORMAL";
    priority_score = 10;
    alert_group    = "NO_THREAT";
    attack_type    = "normal";
    return;
  }

  if (beatAvg > 150) {
    ecgStatus      = "TACHYCARDIA";
    ml_label       = "ANOMALY";
    priority_score = 95;
    alert_group    = "DEVICE_ATTACK";
    attack_type    = "abnormal_ecg";
  } else if (beatAvg < 40) {
    ecgStatus      = "BRADYCARDIA";
    ml_label       = "ANOMALY";
    priority_score = 95;
    alert_group    = "DEVICE_ATTACK";
    attack_type    = "abnormal_ecg";
  } else if (beatAvg > 100) {
    ecgStatus      = "ELEVATED_HR";
    ml_label       = "ANOMALY";
    priority_score = 70;
    alert_group    = "DEVICE_ATTACK";
    attack_type    = "abnormal_ecg";
  } else {
    ecgStatus      = "NORMAL_SINUS";
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

  pinMode(LO_PLUS,  INPUT);
  pinMode(LO_MINUS, INPUT);

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

  // Print CSV header
  Serial.println();
  Serial.println("timestamp,device_id,device_type,ward,life_support,criticality_tier,protocol,src_ip,dst_port,heart_rate_bpm_ecg,ecg_raw_value,lead_status,ecg_status,ml_label,priority_score,alert_group,attack_type");
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

  // ── Step 1: Check electrodes every loop ──
  if (digitalRead(LO_PLUS) || digitalRead(LO_MINUS)) {

    // Electrodes NOT connected to body
    leadStatus  = "DISCONNECTED";
    ecgRawValue = 0;    // ← show 0 when not on body
    beatAvg     = 0;    // ← show 0 when not on body

  } else {

    // Electrodes connected to body
    leadStatus  = "CONNECTED";
    ecgRawValue = analogRead(ECG_PIN);   // ← real ECG value
    detectHeartRate(ecgRawValue, now);
  }

  // ── Step 2: Classify ECG status ──────────
  classifyECG();

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
    doc["heart_rate_bpm_ecg"] = beatAvg;
    doc["ecg_raw_value"] = ecgRawValue;
    doc["lead_status"] = leadStatus;
    doc["ecg_status"] = ecgStatus;
    doc["ml_label"] = ml_label;
    doc["priority_score"] = priority_score;
    doc["alert_group"] = alert_group;
    doc["attack_type"] = attack_type;

    char jsonBuffer[512];
    serializeJson(doc, jsonBuffer);

    // Publish to MQTT
    client.publish(telemetry_topic, jsonBuffer);

    // Print CSV row to Serial Monitor
    Serial.print(now);              Serial.print(",");
    Serial.print(device_id);        Serial.print(",");
    Serial.print(device_type);      Serial.print(",");
    Serial.print(ward);             Serial.print(",");
    Serial.print(life_support);     Serial.print(",");
    Serial.print(criticality_tier); Serial.print(",");
    Serial.print(protocol);         Serial.print(",");
    Serial.print(src_ip);           Serial.print(",");
    Serial.print(mqtt_port);        Serial.print(",");
    Serial.print(beatAvg);          Serial.print(",");
    Serial.print(ecgRawValue);      Serial.print(",");
    Serial.print(leadStatus);       Serial.print(",");
    Serial.print(ecgStatus);        Serial.print(",");
    Serial.print(ml_label);         Serial.print(",");
    Serial.print(priority_score);   Serial.print(",");
    Serial.print(alert_group);      Serial.print(",");
    Serial.println(attack_type);
  }
}
