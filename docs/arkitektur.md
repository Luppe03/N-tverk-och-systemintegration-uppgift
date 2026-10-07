# Arkitektur – Säker och integrerad IoT-lösning

## 1. Översikt
Systemet består av en fysisk IoT-enhet, en MQTT-broker och en Flask-baserad API-server.

ESP32-C6 samlar in temperatur och luftfuktighet från en DHT22-sensor. Sensordata skickas via Wi-Fi till en MQTT-broker. Flask API prenumererar på MQTT-topic och behandlar den mottagna JSON-datan.

API:t gör sedan den senaste sensordatan tillgänglig för andra system via HTTP.

## 2. Arkitektur
```text
+-------------------------+
|       ESP32-C6          |
|                         |
|       DHT22             |
|  Temperatur + fuktighet |
+------------+------------+
             |
             | Wi-Fi
             |
             v
+-------------------------+
|    MQTT Broker          |
|      Mosquitto          |
|                         |
|  192.168.0.54:1883      |
|  Topic: iot/sensor      |
+------------+------------+
             |
             | MQTT
             |
             v
+-------------------------+
|      Flask API          |
|                         |
|    Python + Paho        |
|                         |
|      Port: 5000         |
+------------+------------+
             |
             | HTTP
             |
             v
+-------------------------+
|    Andra system /       |
|    API-klienter          |
|                         |
|  /api/sensor            |
|  /api/health            |
+-------------------------+
```

## 3. Komponenter
### ESP32-C6
ESP32-C6 fungerar som IoT-enhet.

Ansvar:

* ansluta till Wi-Fi
* läsa temperatur från DHT22
* läsa luftfuktighet från DHT22
* skapa JSON-data
* ansluta till MQTT
* publicera sensordata
* försöka återansluta om MQTT-anslutningen bryts

### DHT22
DHT22 är den fysiska sensorn i systemet.

Den mäter:

* temperatur
* luftfuktighet

Sensorn är ansluten till ESP32-C6 via GPIO4.

### Wi-Fi
ESP32-C6 ansluter till det lokala Wi-Fi-nätverket.

ESP32 använder en IP-adress i det lokala nätverket och kommunicerar med MQTT-brokern över nätverket.

### Mosquitto
Mosquitto fungerar som MQTT-broker.

Broker:

```text
192.168.0.54
```

Port:

```text
1883
```

MQTT-topic:

```text
iot/sensor
```

Brokern kräver autentisering och tillåter inte anonyma anslutningar.

### Flask API
Flask API körs på datorn och tar emot MQTT-data genom Paho MQTT.

API:t:

* tar emot MQTT-meddelanden
* avkodar JSON
* validerar sensordata
* sparar senaste mätningen
* loggar händelser
* övervakar systemets status
* exponerar sensordata via HTTP

API-port:

```text
5000
```

## 4. Kommunikation
### ESP32 → MQTT Broker
Protokoll:

```text
MQTT
```

Transport:

```text
TCP/IP
```

Broker:

```text
192.168.0.54:1883
```

Topic:

```text
iot/sensor
```

Kommunikationsmodell:

```text
Publish / Subscribe
```

ESP32 publicerar sensordata till MQTT-topic.

### MQTT Broker → Flask API
Flask API prenumererar på:

```text
iot/sensor
```

MQTT valdes eftersom protokollet är väl lämpat för IoT-system där sensorer skickar små mängder data över ett nätverk.

MQTT använder en publish/subscribe-modell där ESP32 publicerar sensordata till en topic och Flask API prenumererar på samma topic. Det gör att IoT-enheten inte behöver känna till vilka system som använder datan.

MQTT passar även bra för lösningen eftersom protokollet har låg overhead och är enkelt att använda för periodiska sensormätningar.

I denna lösning används MQTT-topic:

iot/sensor

och MQTT-brokern kör på:

192.168.0.54:1883

När ett nytt meddelande publiceras skickar MQTT-brokern meddelandet till API-servern.

### Klient → Flask API
API-klienter använder HTTP GET.

Tillgängliga endpoints:

```text
GET /api/sensor
GET /api/health
```

## 5. Dataformat
Systemet använder JSON.

Exempel:

```json
{
  "sensorId": "room-a-temp-01",
  "temperature": 21.40,
  "humidity": 53.60
}
```

API:t lägger till en timestamp när meddelandet tas emot:

```json
{
  "sensorId": "room-a-temp-01",
  "temperature": 21.40,
  "humidity": 53.60,
  "timestamp": "2026-10-07T13:55:53"
}
```

## 6. Felhantering
ESP32 försöker automatiskt återansluta till MQTT om anslutningen bryts.

API-servern hanterar bland annat:

* MQTT-anslutningsfel
* MQTT-frånkoppling
* ogiltig JSON
* saknade JSON-fält
* felaktig teckenkodning
* oväntade fel vid behandling av data
* avsaknad av nya sensormätningar

API:t använder en gräns på 10 sekunder för att avgöra om sensorn fortfarande är aktiv.

Om ingen ny data kommer inom 10 sekunder rapporteras:

```text
sensor_active: false
status: error
```

## 7. Övervakning
Systemet övervakas genom:

```text
GET /api/health
```

Health-endpointen kontrollerar bland annat:

* MQTT-anslutning
* om sensordata finns
* om sensorn är aktiv
* tid sedan senaste mätning
* systemstatus

Det gör det möjligt att upptäcka kommunikationsproblem utan att behöva kontrollera ESP32 manuellt.

## 8. Loggning
API-servern använder Python logging.

Loggfil:

```text
iot_api.log
```

Exempel på händelser som loggas:

* MQTT-anslutning
* MQTT-frånkoppling
* mottagna sensordata
* API-anrop
* ogiltig JSON
* felaktig sensordata
* health checks
* kommunikationsfel

## 9. Säkerhet
MQTT-brokern kräver användarnamn och lösenord.

Anonyma MQTT-anslutningar är avstängda.

Hemlig information som Wi-Fi- och MQTT-lösenord lagras lokalt i `secrets.h`.

`secrets.h` är exkluderad från Git med `.gitignore`.

API-serverns MQTT-lösenord hämtas från en miljövariabel.

## 10. Tekniska begränsningar
MQTT använder port 1883 utan TLS.

Det innebär att MQTT-kommunikationen inte är krypterad.

API:t använder HTTP istället för HTTPS.

Systemet är därför främst lämpat för ett kontrollerat lokalt nätverk och behöver ytterligare säkerhetsåtgärder innan det används i en produktionsmiljö.

Exempel på framtida förbättringar:

* MQTT över TLS
* HTTPS
* starkare API-autentisering
* databas för historiska mätvärden
* centraliserad logghantering
* mer avancerad övervakning
