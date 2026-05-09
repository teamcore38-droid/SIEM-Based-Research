#include <WiFi.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ArduinoJson.h>
#include <time.h>

// ===================== Wi-Fi Details =====================
const char* WIFI_SSID = "Firaz";
const char* WIFI_PASSWORD = "poiuytrew";

// ===================== MQTT Broker Details =====================
// Local Mosquitto broker running on your PC
const char* MQTT_BROKER = "10.121.216.182";
const int MQTT_PORT = 1883;
const char* MQTT_TOPIC = "hospital/iomt/temperature";

// ===================== Device Metadata =====================
const char* DEVICE_ID = "TEMP_ESP32_001";
const char* DEVICE_TYPE = "ESP32_Temperature_Monitor";
const char* WARD = "General_Ward";
const bool LIFE_SUPPORT = false;
const int CRITICALITY_TIER = 5;
const char* PROTOCOL = "MQTT";
const int DST_PORT = 1883;

// ===================== MQTT Command Topics =====================
String COMMAND_TOPIC = String("hospital/iomt/command/") + DEVICE_ID;
const char* FLEET_TOPIC = "hospital/iomt/command/fleet";

// ===================== NTP Time Configuration =====================
// Sri Lanka time = UTC + 5:30
const char* NTP_SERVER = "pool.ntp.org";
const long GMT_OFFSET_SEC = 19800;
const int DAYLIGHT_OFFSET_SEC = 0;

// ===================== DS18B20 Sensor Pin =====================
#define ONE_WIRE_BUS 4

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

WiFiClient espClient;
PubSubClient mqttClient(espClient);

// ===================== Publish Timer =====================
unsigned long lastPublishTime = 0;
const unsigned long publishInterval = 5000;

// ===================== Device State Management =====================
bool is_isolated = false;      // Temporarily pauses data publishing
bool is_quarantined = false;   // Stops device operation until reset/reprogrammed

// ===================== Wi-Fi Connection =====================
void connectWiFi() {
  Serial.println();
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Wi-Fi connected successfully.");
  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());
}

// ===================== Time Synchronization =====================
void setupTime() {
  configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, NTP_SERVER);

  Serial.println("Synchronizing time with NTP server...");

  struct tm timeinfo;
  int retryCount = 0;

  while (!getLocalTime(&timeinfo) && retryCount < 20) {
    Serial.print(".");
    delay(500);
    retryCount++;
  }

  Serial.println();

  if (getLocalTime(&timeinfo)) {
    Serial.println("Time synchronized successfully.");
    Serial.print("Current time: ");
    Serial.println(&timeinfo, "%Y-%m-%d %H:%M:%S");
  } else {
    Serial.println("Time synchronization failed. Timestamp will show Time Error.");
  }
}

// ===================== Get Current Timestamp =====================
String getCurrentTimestamp() {
  struct tm timeinfo;
  char timeStringBuff[25];

  if (getLocalTime(&timeinfo)) {
    strftime(timeStringBuff, sizeof(timeStringBuff), "%Y-%m-%d %H:%M:%S", &timeinfo);
    return String(timeStringBuff);
  } else {
    return "Time Error";
  }
}

// ===================== MQTT Command Handler =====================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";

  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Command message received on topic [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(message);

  StaticJsonDocument<256> commandDoc;
  DeserializationError error = deserializeJson(commandDoc, message);

  if (error) {
    Serial.println("Failed to parse command JSON.");
    return;
  }

  const char* command = commandDoc["command"];

  if (command == NULL) {
    Serial.println("No command field found in message.");
    return;
  }

  String commandStr = String(command);

  if (commandStr == "TEMPORARY_ISOLATE") {
    is_isolated = true;
    Serial.println("[ACTION] TEMPORARY ISOLATION ACTIVATED. Data publishing paused.");
  } 
  else if (commandStr == "PERMANENT_QUARANTINE" || commandStr == "BLOCK_COMMUNICATION") {
    is_quarantined = true;
    Serial.println("[ACTION] PERMANENT QUARANTINE ACTIVATED. Device publishing stopped.");
  } 
  else if (commandStr == "ROLLBACK" || commandStr == "ALL_CLEAR") {
    is_isolated = false;
    is_quarantined = false;
    Serial.println("[ACTION] ROLLBACK / ALL CLEAR. Device resumed normal publishing.");
  } 
  else if (commandStr == "MONITOR") {
    Serial.println("[ACTION] MONITOR command received. Device remains active.");
  } 
  else {
    Serial.print("Unknown command received: ");
    Serial.println(commandStr);
  }
}

// ===================== MQTT Connection =====================
void connectMQTT() {
  while (!mqttClient.connected() && !is_quarantined) {
    Serial.print("Connecting to local Mosquitto broker... ");

    String clientId = "ESP32_TEMP_";
    clientId += String(random(0xffff), HEX);

    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected.");

      mqttClient.subscribe(COMMAND_TOPIC.c_str());
      mqttClient.subscribe(FLEET_TOPIC);

      Serial.print("Subscribed to command topic: ");
      Serial.println(COMMAND_TOPIC);

      Serial.print("Subscribed to fleet topic: ");
      Serial.println(FLEET_TOPIC);
    } else {
      Serial.print("failed. MQTT state = ");
      Serial.println(mqttClient.state());
      Serial.println("Retrying in 3 seconds...");
      delay(3000);
    }
  }
}

// ===================== Temperature Classification =====================
void classifyTemperature(float temperatureC, String &mlLabel, int &priorityScore, String &alertGroup, String &attackType) {
  if (temperatureC == DEVICE_DISCONNECTED_C || temperatureC == 85.0 || temperatureC == -127.0) {
    mlLabel = "ANOMALY";
    priorityScore = 90;
    alertGroup = "DEVICE_ATTACK";
    attackType = "sensor_malfunction";
  } 
  else if (temperatureC > 40.0) {
    mlLabel = "ANOMALY";
    priorityScore = 80;
    alertGroup = "DEVICE_ATTACK";
    attackType = "high_temperature";
  } 
  else if (temperatureC < 35.0) {
    mlLabel = "ANOMALY";
    priorityScore = 80;
    alertGroup = "DEVICE_ATTACK";
    attackType = "low_temperature";
  } 
  else {
    mlLabel = "NORMAL";
    priorityScore = 10;
    alertGroup = "NO_THREAT";
    attackType = "normal";
  }
}

// ===================== Setup =====================
void setup() {
  Serial.begin(115200);
  delay(1000);

  sensors.begin();

  connectWiFi();

  setupTime();

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  // Important for JSON payloads
  mqttClient.setBufferSize(1024);

  Serial.println("ESP32 Temperature MQTT Publisher Started");
}

// ===================== Main Loop =====================
void loop() {
  if (is_quarantined) {
    Serial.println("[QUARANTINED] Device communication stopped.");
    delay(3000);
    return;
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi disconnected. Reconnecting...");
    connectWiFi();
    setupTime();
  }

  if (!mqttClient.connected()) {
    connectMQTT();
  }

  mqttClient.loop();

  unsigned long currentTime = millis();

  if (currentTime - lastPublishTime >= publishInterval) {
    lastPublishTime = currentTime;

    if (is_isolated) {
      Serial.println("[ISOLATED] Transmission paused. Waiting for ROLLBACK or ALL_CLEAR command.");
      return;
    }

    sensors.requestTemperatures();
    float temperatureC = sensors.getTempCByIndex(0);

    String mlLabel;
    int priorityScore;
    String alertGroup;
    String attackType;

    classifyTemperature(temperatureC, mlLabel, priorityScore, alertGroup, attackType);

    String currentTimestamp = getCurrentTimestamp();

    StaticJsonDocument<512> doc;

    doc["timestamp"] = currentTimestamp;
    doc["device_id"] = DEVICE_ID;
    doc["device_type"] = DEVICE_TYPE;
    doc["ward"] = WARD;
    doc["life_support"] = LIFE_SUPPORT;
    doc["criticality_tier"] = CRITICALITY_TIER;
    doc["protocol"] = PROTOCOL;
    doc["src_ip"] = WiFi.localIP().toString();
    doc["dst_port"] = DST_PORT;
    doc["temperature_celsius"] = temperatureC;
    doc["ml_label"] = mlLabel;
    doc["priority_score"] = priorityScore;
    doc["alert_group"] = alertGroup;
    doc["attack_type"] = attackType;

    char payload[512];
    size_t payloadSize = serializeJson(doc, payload);

    Serial.print("Payload size: ");
    Serial.println(payloadSize);

    Serial.print("Publishing to topic: ");
    Serial.println(MQTT_TOPIC);

    bool published = mqttClient.publish(MQTT_TOPIC, payload);

    if (published) {
      Serial.println("MQTT data published successfully:");
      Serial.println(payload);
    } else {
      Serial.println("MQTT publish failed.");
      Serial.print("MQTT connected: ");
      Serial.println(mqttClient.connected());
      Serial.print("MQTT state: ");
      Serial.println(mqttClient.state());
    }

    Serial.println("--------------------------------");
  }
}