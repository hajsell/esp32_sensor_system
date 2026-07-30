#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"
#include <WiFiClientSecure.h>
#include <time.h>

// --- KONFIGURACJA ---
const char* ssid = "";
const char* password = "";

const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = 3600;      // UTC+1
const int   daylightOffset_sec = 3600; // DST

const char* mqttServer = "";
const int mqttPort = 8883; 
const char* mqttUsername = "";
const char* mqttPassword = "";
const char* topicAll = "production/sensor/all";

#define DHTPIN 26
#define DHTTYPE DHT22
#define MQ2_PIN 34
#define MQ7_PIN 35

DHT dht(DHTPIN, DHTTYPE);
WiFiClientSecure espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;

// Funkcja generująca sformatowany czas
void getTimestamp(char* buffer, size_t len) {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    snprintf(buffer, len, "nieustalono");
    return;
  }
  strftime(buffer, len, "%Y-%m-%d %H:%M:%S", &timeinfo);
}

void setup() {
  Serial.begin(115200);
  delay(2000); 
  Serial.println("\n--- START PROGRAMU ---");

  dht.begin();

  Serial.printf("Laczenie z WiFi: %s ", ssid);
  WiFi.begin(ssid, password);
  
  int retry = 0;
  while (WiFi.status() != WL_CONNECTED && retry < 20) {
    delay(500);
    Serial.print(".");
    retry++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi OK. Synchronizacja czasu NTP...");
    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  } else {
    Serial.println("\nWiFi FAIL - Sprawdz dane logowania!");
  }

  espClient.setInsecure();
  client.setServer(mqttServer, mqttPort);
}

void loop() {
  // Obsługa połączenia MQTT
  if (WiFi.status() == WL_CONNECTED) {
    if (!client.connected()) {
      Serial.print("Proba MQTT...");
      if (client.connect("ESP32_Sensor_Production", mqttUsername, mqttPassword)) {
        Serial.println(" Polaczono!");
      } else {
        Serial.print(" Blad, rc=");
        Serial.println(client.state());
        delay(2000);
      }
    }
    client.loop();
  }

  unsigned long ms_now = millis();
  
  // Wysyłanie co 1 sekundę
  if (ms_now - lastMsg >= 1000) {
    lastMsg = ms_now;

    float t = dht.readTemperature();
    float h = dht.readHumidity();
    int m2 = analogRead(MQ2_PIN);
    int m7 = analogRead(MQ7_PIN);

    char currentTime[32];
    getTimestamp(currentTime, sizeof(currentTime));

    // Budowanie JSONa z kluczem "timestamp"
    char payload[256];
    snprintf(payload, sizeof(payload), 
      "{\"timestamp\":\"%s\",\"temperature\":%.2f,\"humidity\":%.2f,\"mq2\":%d,\"mq7\":%d}", 
      currentTime, t, h, m2, m7);

    // Wypisanie na Serial Monitor
    Serial.println(payload);

    // Wysyłka na serwer MQTT
    if (client.connected()) {
      client.publish(topicAll, payload);
    }
  }
}