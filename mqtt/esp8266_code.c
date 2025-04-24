#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#define LM35_PIN A0
#define ledB D3
#define FALL_PIN D5

 
#include <Wire.h>
#include "MAX30100_PulseOximeter.h"
#define REPORTING_PERIOD_MS 10000

// Create a PulseOximeter object
PulseOximeter pox;

// Time at which the last beat occurred
uint32_t tsLastReport = 0;

int analogValue = analogRead(LM35_PIN);
float millivolts = (analogValue / 1024.0) * 3300; // 3300 is the voltage provided by NodeMCU
float celsius = millivolts / 10;

char msg_out[20];
char msg_hr[20];
char msg_ic[20];

int spo2 = 0;

// Callback routine is executed when a pulse is detected
void onBeatDetected()
{
  Serial.println("Beat!");
  digitalWrite(ledB, !digitalRead(ledB));
}

// WiFi
const char *ssid = "iPhone";     // Enter your WiFi name
const char *password = "20242025"; // Enter WiFi password

// MQTT Broker
const char *mqtt_broker = "test.mosquitto.org";
const char *topic = "healthconnect/monitor1/temp";
const char *mqtt_username = "";
const char *mqtt_password = "";
const int mqtt_port = 1883;

WiFiClient espClient;
PubSubClient client(espClient);

void setup()
{
  Serial.begin(9600);
  pinMode(LM35_PIN, INPUT);
  pinMode(FALL_PIN, INPUT);
  // Initialize sensor
  if (!pox.begin())
  {
    Serial.println("FAILED");
    for (;;)
    {
      Serial.println("Failed to initialize");
      delay(3000);
    }
  }
  else
  {
    Serial.println("SUCCESS");
  }

  // Configure sensor to use 7.6mA for LED drive
  pox.setIRLedCurrent(MAX30100_LED_CURR_4_4MA);

  // Register a callback routine
  pox.setOnBeatDetectedCallback(onBeatDetected);
  // Set software serial baud to 115200;
  
  // connecting to a WiFi network
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to the WiFi network");

  delay(500);
  // connecting to a mqtt broker
  client.setServer(mqtt_broker, mqtt_port);
  client.setCallback(callback);
  while (!client.connected())
  {
    String client_id = "esp8266-client-";
    client_id += String(WiFi.macAddress());
    Serial.printf("The client %s connects to the public mqtt broker\n", client_id.c_str());
    if (client.connect(client_id.c_str(), mqtt_username, mqtt_password))
    {
      // print message
      Serial.println("Public mosquitoo mqtt broker connected");
    }
    else
    {
      // print message
      Serial.print("failed with state ");
      Serial.print(client.state());
      delay(2000);
    }
  }
  // publish and subscribe
  client.subscribe(topic);
  delay(2000);
}

// Function Called when a message arrived
void callback(char *topic, byte *payload, unsigned int length)
{
  Serial.print("Message arrived in topic: ");
  Serial.println(topic);
  Serial.print("Message:");
  for (int i = 0; i < length; i++)
  {
    Serial.print((char)payload[i]);
  }
  Serial.println();
  Serial.println("-----------------------");
}


void loop()
{
  client.loop();
  // Read from the sensor
  pox.update();
  // Grab the updated heart rate and SpO2 levels
  if (millis() - tsLastReport > REPORTING_PERIOD_MS)
  {
    analogValue = analogRead(LM35_PIN);
    millivolts = (analogValue / 1024.0) * 3300; // 3300 is the voltage provided by NodeMCU
    celsius = (millivolts / 10 )+ 11;
    sprintf(msg_out, "%2.f", celsius);
    Serial.print("Temp : ");
    Serial.println(msg_out);
    // Publishe the data to the broker
    client.publish("healthconnect/monitor1//temp", msg_out);
    spo2 = pox.getSpO2();
    sprintf(msg_hr, "%.2f", pox.getHeartRate());
    Serial.print("Heart Rate : ");
    Serial.println(pox.getHeartRate());
    client.publish("healthconnect/monitor1//plsRate", msg_hr);
    sprintf(msg_ic, "%d", pox.getSpO2());
    Serial.print("spo2 : ");
    Serial.println(pox.getSpO2());
    client.publish("healthconnect/monitor1/spio2", msg_ic);
    stReport = millis();
    delay(2000);
  }
}