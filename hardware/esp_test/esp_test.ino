#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// WiFi credentials
const char* ssid = "iPhone";       // Replace with your WiFi SSID
const char* password = "20242025"; // Replace with your WiFi password

// MQTT Broker details
const char* mqtt_broker = "test.mosquitto.org";
const int mqtt_port = 1883;
const char* topic_temp = "healthconnect/monitor1/temp";
const char* topic_spo2 = "healthconnect/monitor1/spo2";
const char* topic_bpm = "healthconnect/monitor1/bpm";
const char* topic_ecg = "healthconnect/monitor1/ecg";

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);

  // Connect to WiFi
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");

  // Connect to MQTT broker
  client.setServer(mqtt_broker, mqtt_port);
  while (!client.connected()) {
    Serial.println("Connecting to MQTT broker...");
    String client_id = "esp8266-client-" + String(WiFi.macAddress());
    if (client.connect(client_id.c_str())) {
      Serial.println("Connected to MQTT broker");
    } else {
      Serial.print("Failed to connect. State: ");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

void loop() {
  // Ensure the client stays connected
  if (!client.connected()) {
    while (!client.connected()) {
      Serial.println("Reconnecting to MQTT broker...");
      String client_id = "esp8266-client-" + String(WiFi.macAddress());
      if (client.connect(client_id.c_str())) {
        Serial.println("Reconnected to MQTT broker");
      } else {
        Serial.print("Failed to reconnect. State: ");
        Serial.println(client.state());
        delay(2000);
      }
    }
  }

  // Simulate data
  float temp = random(30, 40) + random(0, 100) / 100.0; // Random temperature between 30.00°C and 40.99°C
  int spo2 = random(90, 100);                          // Random SpO2 between 90% and 100%
  int bpm = random(60, 100);                           // Random BPM between 60 and 100
  float ecg = random(-10, 10) / 10.0;                  // Random ECG value between -1.0 and 1.0

  // Publish data
  char temp_str[8];
  char spo2_str[8];
  char bpm_str[8];
  char ecg_str[8];

  dtostrf(temp, 4, 2, temp_str);
  itoa(spo2, spo2_str, 10);
  itoa(bpm, bpm_str, 10);
  dtostrf(ecg, 4, 2, ecg_str);

  client.publish(topic_temp, temp_str);
  client.publish(topic_spo2, spo2_str);
  client.publish(topic_bpm, bpm_str);
  client.publish(topic_ecg, ecg_str);

  // Print data to Serial Monitor
  Serial.println("Published data:");
  Serial.print("Temperature: "); Serial.println(temp_str);
  Serial.print("SpO2: "); Serial.println(spo2_str);
  Serial.print("BPM: "); Serial.println(bpm_str);
  Serial.print("ECG: "); Serial.println(ecg_str);

  // Wait before publishing again
  delay(5000);
}
