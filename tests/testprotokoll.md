# Testprotokoll
## 1. Syfte
Testerna används för att verifiera att IoT-systemets dataflöde, API, MQTT-kommunikation, övervakning och felhantering fungerar.

Systemets dataflöde är:

```text
ESP32-C6 + DHT22
        |
        | Wi-Fi
        v
MQTT Broker (Mosquitto)
        |
        | MQTT / iot/sensor
        v
Flask API
        |
        | HTTP
        v
API-klient
```

---

## 2. Testmiljö
### Hårdvara
* Waveshare ESP32-C6
* DHT22

### Programvara
* Arduino IDE
* Mosquitto MQTT Broker
* Python
* Flask
* Paho MQTT

### Nätverk
MQTT-broker:

```text
192.168.0.54:1883
```

MQTT-topic:

```text
iot/sensor
```

API:

```text
http://localhost:5000
```

---

## 3. Test 1 – DHT22
### Syfte
Kontrollera att ESP32 kan läsa temperatur och luftfuktighet från DHT22.

### Test
ESP32 startades och DHT22-värden lästes i Serial Monitor.

### Förväntat resultat
Temperatur och luftfuktighet ska läsas utan fel.

### Resultat
Testet godkändes.

Exempel på uppmätta värden:

```text
Temperatur: 21.40 °C
Luftfuktighet: 53.60 %
```

---

## 4. Test 2 – Wi-Fi
### Syfte
Kontrollera att ESP32 ansluter till Wi-Fi.

### Test
ESP32 startades och nätverksanslutningen kontrollerades i Serial Monitor.

### Förväntat resultat
ESP32 ska ansluta och få en IP-adress.

### Resultat
Testet godkändes.

ESP32 fick exempelvis:

```text
IP-adress: 192.168.0.89
```

---

## 5. Test 3 – MQTT
### Syfte
Kontrollera att ESP32 kan ansluta till MQTT-brokern och publicera sensordata.

### Förväntat resultat
ESP32 ska ansluta till MQTT och publicera JSON till:

```text
iot/sensor
```

### Resultat
Testet godkändes.

ESP32 visade:

```text
MQTT-meddelande skickat!
```

Exempel på skickad JSON:

```json
{
  "sensorId": "room-a-temp-01",
  "temperature": 21.40,
  "humidity": 53.60
}
```

---

## 6. Test 4 – MQTT-autentisering
### Syfte
Kontrollera att MQTT-brokern kräver autentisering.

### Förväntat resultat
Anslutningar utan korrekt autentisering ska nekas.

### Resultat
Testet godkändes.

MQTT-brokern konfigurerades med:

```text
allow_anonymous false
```

ESP32 och Flask API använder autentiserade MQTT-anslutningar.

---

## 7. Test 5 – API /api/sensor
### Syfte
Kontrollera att API:t returnerar den senaste sensordatan.

### Test
```powershell
Invoke-RestMethod http://localhost:5000/api/sensor
```

### Förväntat resultat
API:t ska returnera status och senaste sensormätning.

### Resultat
Testet godkändes.

API:t returnerade bland annat:

```text
status: ok
sensorId: room-a-temp-01
temperature: 21.40
humidity: 53.60
```

---

## 8. Test 6 – API /api/health
### Syfte
Kontrollera systemets övervakningsfunktion.

### Test
```powershell
Invoke-RestMethod http://localhost:5000/api/health
```

### Förväntat resultat
Health-endpointen ska visa MQTT-status och om aktuell sensordata finns.

### Resultat
Testet godkändes.

Exempel:

```text
mqtt_connected: true
sensor_data_available: true
sensor_active: true
status: ok
```

---

## 9. Test 7 – Avbrott i sensor-/nätverkskommunikation
### Syfte
Kontrollera att systemet upptäcker när nya sensormätningar slutar komma.

### Test
ESP32 stoppades så att nya MQTT-meddelanden inte längre skickades.

### Förväntat resultat
API:t ska efter 10 sekunder identifiera sensorn som inaktiv.

### Resultat
Testet godkändes.

Health-endpointen visade:

```text
sensor_active: false
status: error
```

`data_age_seconds` fortsatte att öka eftersom ingen ny data kom in.

### Åtgärd
ESP32 startades igen.

### Verifiering
Efter att nya MQTT-meddelanden började komma in visade API:t:

```text
sensor_active: true
status: ok
```

---

## 10. Test 8 – Ogiltigt MQTT-meddelande
### Syfte
Kontrollera att API:t hanterar ett felaktigt MQTT-meddelande utan att krascha.

### Test
Ett ogiltigt meddelande skickades till:

```text
iot/sensor
```

Testmeddelande:

```text
DETTA ÄR INTE GILTIG JSON
```

### Förväntat resultat
API:t ska upptäcka att meddelandet inte är giltig sensordata, logga felet och fortsätta fungera.

### Resultat
Testet godkändes.

API:t registrerade ett fel och fortsatte därefter att ta emot giltiga sensormeddelanden.

### Verifiering
ESP32 fortsatte att skicka giltiga JSON-meddelanden och API:t fortsatte att behandla dem.

---

## 11. Sammanställning
| Test                     | Resultat |
| ------------------------ | -------- |
| DHT22-läsning            | Godkänd  |
| Wi-Fi-anslutning         | Godkänd  |
| MQTT-kommunikation       | Godkänd  |
| MQTT-autentisering       | Godkänd  |
| GET /api/sensor          | Godkänd  |
| GET /api/health          | Godkänd  |
| Kommunikationsavbrott    | Godkänd  |
| Ogiltigt MQTT-meddelande | Godkänd  |

## 12. Slutsats
Testerna visar att systemet kan samla in sensordata, överföra data via MQTT, behandla JSON, exponera data via ett API och upptäcka vanliga kommunikations- och dataproblem.

De två avsiktliga feltesterna visar även att systemet kan upptäcka avsaknad av nya sensormätningar och hantera ogiltiga MQTT-meddelanden utan att hela API:t slutar fungera.
