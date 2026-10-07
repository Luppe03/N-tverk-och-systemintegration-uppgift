#include <WiFi.h>
#include <DHT.h>
#include <PubSubClient.h>
#include "secrets.h"


const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;


const char* mqtt_server = "192.168.0.54";
const int mqtt_port = 1883;
const char* mqtt_topic = "iot/sensor";


#define DHTPIN 4
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

WiFiClient espClient;
PubSubClient client(espClient);


void reconnectMQTT() {

  while (!client.connected()) {

    Serial.print("Ansluter till MQTT... ");

    if (client.connect("ESP32C6-Sensor", MQTT_USER, MQTT_PASSWORD)) {

      Serial.println("ansluten!");

    } else {

      Serial.print("misslyckades, felkod: ");
      Serial.println(client.state());

      Serial.println("Försöker igen om 5 sekunder...");
      delay(5000);
    }
  }
}


void setup() {

  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("Startar IoT-enheten...");

  dht.begin();

  Serial.println("Startar Wi-Fi-sökning...");

  int numberOfNetworks = WiFi.scanNetworks();

  Serial.print("Hittade nätverk: ");
  Serial.println(numberOfNetworks);

  for (int i = 0; i < numberOfNetworks; i++) {
    Serial.print(i);
    Serial.print(": ");
    Serial.print(WiFi.SSID(i));
    Serial.print("  Signal: ");
    Serial.print(WiFi.RSSI(i));
    Serial.println(" dBm");
  }

  Serial.println();
  Serial.println("Försöker ansluta till Wi-Fi...");

  WiFi.begin(ssid, password);

  int attempts = 0;

  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Wi-Fi anslutet!");
    Serial.print("IP-adress: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Fel: kunde inte ansluta till Wi-Fi.");
    Serial.print("Wi-Fi statuskod: ");
    Serial.println(WiFi.status());
    return;
  }

  Serial.println();
  Serial.println("Wi-Fi anslutet!");

  Serial.print("IP-adress: ");
  Serial.println(WiFi.localIP());

  Serial.println("DHT22 startad.");

  client.setServer(mqtt_server, mqtt_port);

  Serial.print("MQTT-server: ");
  Serial.println(mqtt_server);
}


void loop() {

  if (!client.connected()) {
    reconnectMQTT();
  }

  client.loop();

  delay(2500);

  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  if (isnan(temperature) || isnan(humidity)) {

    Serial.println("Fel: kunde inte läsa DHT22.");
    return;
  }

  Serial.println();
  Serial.println("=== Sensorvärden ===");

  Serial.print("Temperatur: ");
  Serial.print(temperature);
  Serial.println(" °C");

  Serial.print("Luftfuktighet: ");
  Serial.print(humidity);
  Serial.println(" %");

  Serial.println("====================");


  char message[150];

  snprintf(
    message,
    sizeof(message),
    "{\"sensorId\":\"room-a-temp-01\",\"temperature\":%.2f,\"humidity\":%.2f}",
    temperature,
    humidity
  );

  Serial.print("JSON: ");
  Serial.println(message);


  if (client.publish(mqtt_topic, message)) {

    Serial.println("MQTT-meddelande skickat!");

  } else {

    Serial.println("Fel: kunde inte skicka MQTT-meddelande.");
  }
}