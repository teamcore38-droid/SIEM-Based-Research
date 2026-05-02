#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "MAX30105.h" // Example sensor lib

// --- Configuration ---
const char* ssid = "HOSPITAL_WIFI";
const char* password = "SECURE_PASSWORD";
const char* mqtt_server = "192.168.1.10"; // Wazuh/Gateway IP

// --- Objects ---
WiFiClient espClient;
PubSubClient client(espClient);
MAX30105 particleSensor;

void setup() {
  Serial.begin(115200);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi...");
  }
  
  // Setup Sensor
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) { 
    Serial.println("MAX30105 was not found. Please check wiring/power. ");
    while (1);
  }
  particleSensor.setup(); 

  // MQTT Setup
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) {
    // Reconnect logic
  }
  client.loop();

  // Read Data
  long irValue = particleSensor.getIR();
  
  // Send to SIEM/ARS if outlier detected (Simulated)
  if (irValue < 50000) {
      Serial.println("Finger removed!");
  } else {
      Serial.println("Monitoring...");
      // client.publish("hospital/ward1/pulseox", String(irValue).c_str());
  }
  
  delay(100);
}
