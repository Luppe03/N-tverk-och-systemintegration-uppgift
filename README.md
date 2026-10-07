Nätverk och systemintegration

1. Syfte
Det här projektet är en IoT-lösning för insamling och integration av sensordata från en byggnad.

En ESP32-C6 med en DHT22-sensor mäter temperatur och luftfuktighet. Mätvärdena skickas via Wi-Fi och MQTT till en lokal MQTT-broker. En Flask-baserad API-server tar emot MQTT-data, validerar informationen och gör den tillgänglig via HTTP API.

Lösningen innehåller även loggning, övervakning, autentisering och felhantering.

2. Översikt
Dataflödet ser ut såhär:

ESP32-C6 + DHT22
↓ Wi-Fi
MQTT Broker (Mosquitto)
↓ MQTT topic: iot/sensor
Flask API
↓
/api/sensor
/api/health

Komponenter
ESP32-C6 – IoT-enhet
DHT22 – temperatur- och luftfuktighetssensor
Wi-Fi – nätverksanslutning
Mosquitto – MQTT-broker
MQTT – kommunikationsprotokoll
Flask – API-server
Python – backend
JSON – dataformat

3. Funktion
ESP32-C6 läser temperatur och luftfuktighet från DHT22 ungefär var 2,5 sekund.

Exempel på skickad JSON:

{
  "sensorId": "room-a-temp-01",
  "temperature": 21.40,
  "humidity": 53.60
}

Data skickas till MQTT-topic:

iot/sensor

MQTT-brokern kör på:
192.168.0.54:1883

Flask API kör på port:
5000

4. API
Hämta senaste sensordata
GET /api/sensor

Exempel på svar:

{
  "status": "ok",
  "data": {
    "sensorId": "room-a-temp-01",
    "temperature": 21.40,
    "humidity": 53.60,
    "timestamp": "2026-10-07T13:55:53"
  }
}
Kontrollera systemets status
GET /api/health

Exempel på svar:

{
  "status": "ok",
  "mqtt_connected": true,
  "sensor_data_available": true,
  "sensor_active": true,
  "last_sensor_update": "2026-10-07T13:55:53",
  "data_age_seconds": 1.87,
  "max_allowed_data_age_seconds": 10
}

API betraktar sensorn som aktiv om den senaste mätningen är högst 10 sekunder gammal.

5. Säkerhet
Följande säkerhetsåtgärder används.

MQTT-autentisering

MQTT-brokern tillåter inte anonyma anslutningar.

Användarnamn och lösenord krävs för anslutning.

Skydd av hemligheter

Lösenord för MQTT och Wi-Fi lagras lokalt i secrets.h och exponeras inte i den versionshanterade källkoden.

Filen secrets.h finns i .gitignore och ska därför inte publiceras på GitHub.

API-serverns MQTT-lösenord hämtas från en miljövariabel istället för att lagras direkt i Python-koden.

Indatavalidering

API-servern kontrollerar att mottagna MQTT-meddelanden innehåller:
sensorId
temperature
humidity

Ogiltig JSON, saknade fält och felaktigt kodade meddelanden hanteras utan att API-servern avslutas.

6. Loggning och övervakning
API-servern loggar bland annat:
MQTT-anslutningar
MQTT-frånkopplingar
mottagna sensorvärden
ogiltig JSON
felaktig sensordata
API-anrop
health checks
kommunikationsfel

Loggfilen heter:
iot_api.log

Health-endpointen används som monitoring-funktion:
GET /api/health

Den visar bland annat:
MQTT-anslutning
om sensordata finns
om sensorn är aktiv
hur gammal senaste mätningen är
systemets aktuella status

7. Felhantering och tester
Minst två avsiktliga fel har testats.

Fel 1 – avbruten sensor/dataöverföring

ESP32 stoppades så att nya mätvärden inte längre skickades.

API upptäckte att den senaste mätningen blev äldre än 10 sekunder.

Resultat:

sensor_active: false
status: error

När ESP32 åter startades och nya mätvärden kom in blev systemstatus åter ok.

Fel 2 – ogiltigt MQTT-meddelande

Ett felaktigt MQTT-meddelande skickades till iot/sensor.

API upptäckte att meddelandet inte kunde behandlas som giltig sensordata och loggade felet.

Systemet fortsatte därefter att behandla giltiga sensormeddelanden.

8. Installation
Krav
ESP32-C6
DHT22
Arduino IDE
Python 3
Flask
Paho MQTT
Mosquitto MQTT Broker
Python-beroenden

Installera:

py -m pip install flask paho-mqtt
Starta MQTT-broker

Mosquitto ska vara konfigurerad med autentisering och får inte tillåta anonyma anslutningar.

Exempel:

listener 1883 0.0.0.0
allow_anonymous false
password_file C:\Program Files\mosquitto\passwd
Starta API

Sätt MQTT-lösenordet som miljövariabel och starta API:t:

$env:MQTT_PASSWORD="DITT_MQTT_LÖSENORD"
py app.py

Lösenordet ska inte skrivas direkt i app.py eller publiceras på GitHub.

Starta ESP32

Öppna esp32_sensor.ino i Arduino IDE och ladda upp programmet till ESP32-C6.

Wi-Fi- och MQTT-hemligheter ska finnas lokalt i:

secrets.h

9. Kontrollera dataflödet
När systemet körs ska ESP32 visa exempelvis:

Wi-Fi anslutet!
MQTT-meddelande skickat!

API-servern ska visa:

Ansluten till MQTT!
Prenumererar på: iot/sensor

Kontrollera senaste sensordata:

Invoke-RestMethod http://localhost:5000/api/sensor

Kontrollera systemstatus:

Invoke-RestMethod http://localhost:5000/api/health

Om allt fungerar ska health-status vara:

status: ok

10. Begränsningar
Projektet använder MQTT på port 1883 utan TLS, vilket innebär att MQTT-kommunikationen inte är krypterad.

Flask API använder HTTP istället för HTTPS.

Lösningen är främst utvecklad för ett lokalt nätverk och saknar bland annat:

TLS-certifikat
HTTPS
avancerad användarautentisering för API
databas för historiska mätvärden
centraliserad logghantering

Dessa funktioner skulle kunna implementeras i en produktionsmiljö.

11. Projektstruktur
IoT-projekt/
├── .gitignore
├── README.md
├── app.py
├── src/
│   └── esp32/
│       └── esp32_sensor/
│           ├── esp32_sensor.ino
│           └── secrets.h
├── docs/
└── tests/