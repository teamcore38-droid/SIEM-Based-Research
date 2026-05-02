#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include <PubSubClient.h>
#include <ArduinoJson.h> // Ensure ArduinoJson is installed for command parsing

// --- 1. WI-FI CONFIGURATION ---
const char* ssid     = "Koshi";
const char* password = "123454321";

// --- MQTT CONFIGURATION ---
const char* mqtt_server = "10.86.251.69";
const int mqtt_port = 1883;
const char* telemetry_topic = "hospital/iomt/pulse";

// --- DEVICE METADATA ---
const char* device_id = "PULSE_ESP32_001";
const char* device_type = "ESP32_Pulse_Oximeter";
const char* ward = "ICU";
bool life_support = true;
int criticality_tier = 9;
const char* protocol = "MQTT";
const char* group_id = "GRP_001";

// Command topics
String command_topic = String("hospital/iomt/command/") + device_id;
const char* fleet_topic = "hospital/iomt/command/fleet";

WiFiClient espClient;
PubSubClient client(espClient);

// --- 2. GLOBAL OBJECTS ---
WebServer server(80);
MAX30105 particleSensor;

// --- 3. HEART RATE VARIABLES ---
const byte RATE_SIZE = 10;
byte rates[RATE_SIZE];
byte rateSpot = 0;
long lastBeat = 0;
float beatsPerMinute = 0;
int beatAvg = 0;
long irValue = 0;

bool fingerPresent = false;
bool monitoringStarted = false;

// --- AI/ML STATUS VARIABLES ---
String ml_label = "NORMAL";
int priority_score = 10;
String alert_group = "NO_THREAT";
String attack_type = "normal";

// --- STATE MANAGEMENT ---
bool is_isolated = false;   // Pauses transmission but keeps sensor running
bool is_quarantined = false; // Stops everything permanently

constexpr int SDA_PIN = 13;
constexpr int SCL_PIN = 12;

unsigned long lastPublish = 0;
const long publishInterval = 2000;

// --- 4. WEB PAGE ---
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <title>Heart Rate Monitor</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { background-color: #121212; color: white; font-family: sans-serif; text-align: center; padding-top: 50px; }
    .card { background: #1e1e1e; width: 300px; margin: 0 auto; padding: 40px; border-radius: 20px; border-top: 4px solid #e57373; }
    .bpm-value { font-size: 80px; font-weight: bold; margin: 10px 0; }
    .beating { color: #f44336; animation: beat 0.8s infinite alternate; }
    @keyframes beat { to { transform: scale(1.1); } }
  </style>
</head>
<body>
  <h1>HEART RATE MONITOR</h1>
  <div class="card">
    <div id="heartIcon" style="font-size:60px;">&#10084;</div>
    <div class="bpm-value" id="bpm">--</div>
    <div id="statusMsg">Initializing...</div>
  </div>
  <script>
    setInterval(function() {
      fetch('/readings').then(response => response.json()).then(data => {
        const bpmDisplay = document.getElementById("bpm");
        const heart = document.getElementById("heartIcon");
        const msg = document.getElementById("statusMsg");
        if (data.ir < 20000) {
          msg.innerText = "Place finger on sensor";
          heart.classList.remove("beating");
          bpmDisplay.innerText = "--";
        } else {
          msg.innerText = "Monitoring...";
          heart.classList.add("beating");
          bpmDisplay.innerText = (data.bpm > 0) ? data.bpm : "Wait...";
        }
      });
    }, 250);
  </script>
</body>
</html>
)rawliteral";

// ═══════════════════════════════════════════
// CLASSIFICATION LOGIC (For AI Pipeline)
// ═══════════════════════════════════════════
void classifyHeartRate() {
  if (!fingerPresent) {
    ml_label = "NORMAL";
    priority_score = 10;
    alert_group = "NO_THREAT";
    attack_type = "normal";
    return;
  }

  if (beatAvg > 120 || beatAvg < 40) { // Critical condition
    ml_label = "ANOMALY";
    priority_score = 90;
    alert_group = "DEVICE_ATTACK";
    attack_type = "abnormal_pulse";
  } else if (beatAvg > 100 || beatAvg < 60) { // Warning
    ml_label = "ANOMALY";
    priority_score = 60;
    alert_group = "DEVICE_ATTACK";
    attack_type = "elevated_pulse";
  } else {
    ml_label = "NORMAL";
    priority_score = 10;
    alert_group = "NO_THREAT";
    attack_type = "normal";
  }
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

  // Parse JSON command
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

void reconnectMQTT() {
  while (!client.connected() && !is_quarantined) { // Don't reconnect if quarantined
    Serial.print("Connecting MQTT...");
    if (client.connect(device_id)) {
      Serial.println("connected");
      
      // Subscribe to command topics
      client.subscribe(command_topic.c_str());
      client.subscribe(fleet_topic);
      Serial.println("Subscribed to command topics.");
    } 
    else {
      Serial.print("failed rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin(SDA_PIN, SCL_PIN);

  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("MAX3010x not found!");
    while (1);
  }

  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x0A);
  particleSensor.setPulseAmplitudeIR(0x0A);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nConnected! IP:");
  Serial.println(WiFi.localIP());

  client.setBufferSize(1024);
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback); // Set MQTT callback

  Serial.println("MQTT server:");
  Serial.println(mqtt_server);

  server.on("/", []() {
    server.send(200, "text/html", index_html);
  });

  server.on("/readings", []() {
    String json = "{\"bpm\": " + String(beatAvg) + ", \"ir\": " + String(irValue) + "}";
    server.send(200, "application/json", json);
  });

  server.begin();
}

void loop() {
  if (is_quarantined) {
    // If quarantined, do absolutely nothing (simulated device bricking for security)
    delay(1000);
    return;
  }

  server.handleClient();

  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  // Read sensor
  irValue = particleSensor.getIR();

  // Detect finger presence
  if (irValue > 20000) {
    if (!fingerPresent) {
      fingerPresent = true;
      monitoringStarted = true;
      Serial.println("Finger detected - Monitoring started");
      if (!is_isolated) client.publish("hospital/iomt/pulse/status", "START_MONITORING");
    }
  } else {
    if (fingerPresent) {
      fingerPresent = false;
      monitoringStarted = false;
      Serial.println("Finger removed - Monitoring stopped");
      beatAvg = 0;
      if (!is_isolated) client.publish("hospital/iomt/pulse/status", "STOP_MONITORING");
    }
  }

  // Heart rate calculation
  if (checkForBeat(irValue) == true) {
    long delta = millis() - lastBeat;
    lastBeat = millis();
    beatsPerMinute = 60.0 / (delta / 1000.0);

    if (beatsPerMinute < 255 && beatsPerMinute > 20) {
      rates[rateSpot++] = (byte)beatsPerMinute;
      rateSpot %= RATE_SIZE;
      int total = 0;
      for (byte x = 0; x < RATE_SIZE; x++)
        total += rates[x];
      beatAvg = total / RATE_SIZE;
    }
  }

  classifyHeartRate();

  // Publish every 2 seconds ONLY if not isolated
  if (millis() - lastPublish > publishInterval) {
    lastPublish = millis();

    if (is_isolated) {
       Serial.println("[ISOLATED] Transmission paused.");
       return; 
    }

    String src_ip = WiFi.localIP().toString();
    int heartRateValue = fingerPresent ? beatAvg : 0;

    StaticJsonDocument<512> doc;
    doc["timestamp"] = millis();
    doc["device_id"] = device_id;
    doc["device_type"] = device_type;
    doc["ward"] = ward;
    doc["life_support"] = life_support;
    doc["criticality_tier"] = criticality_tier;
    doc["protocol"] = protocol;
    doc["src_ip"] = src_ip;
    doc["dst_port"] = 1883;
    doc["heart_rate_bpm_pulse"] = heartRateValue;
    doc["ppg_raw_value"] = irValue;
    doc["ml_label"] = ml_label;
    doc["priority_score"] = priority_score;
    doc["alert_group"] = alert_group;
    doc["attack_type"] = attack_type;

    char jsonBuffer[512];
    serializeJson(doc, jsonBuffer);

    client.publish(telemetry_topic, jsonBuffer, true);
    Serial.println(jsonBuffer);
  }
}
