# Felsökning och feltester
## 1. Syfte
Två avsiktliga fel har introducerats i systemet för att kontrollera att fel kan upptäckas och hanteras.

De två testerna är:

1. Avbrott i sensor-/nätverkskommunikationen.
2. Ogiltigt MQTT-meddelande.

---

## 2. Feltest 1 – Avbrott i sensor- eller nätverkskommunikation
### Fel
ESP32-enheten stoppades så att nya sensormätningar inte längre skickades till MQTT-brokern.

### Symptom
API:t fortsatte att innehålla den senaste mottagna sensordatan, men ingen ny data kom in.

Efter mer än 10 sekunder visade health-endpointen bland annat:

```text
sensor_data_available: true
sensor_active: false
status: error
```

`data_age_seconds` ökade eftersom ingen ny mätning togs emot.

### Hur felet upptäcktes
Felet upptäcktes genom:

```text
GET /api/health
```

Exempel:

```powershell
Invoke-RestMethod http://localhost:5000/api/health
```

Health-funktionen kontrollerar om den senaste sensordatan är äldre än den tillåtna gränsen på 10 sekunder.

### Orsak
ESP32 skickade inte längre nya MQTT-meddelanden.

Det innebar att API:t inte fick någon ny sensordata.

### Åtgärd
ESP32 startades igen och anslöts till Wi-Fi och MQTT-brokern.

När nya MQTT-meddelanden började komma in igen blev sensorn aktiv.

### Verifiering
Efter att ESP32 startades igen visade health-endpointen åter:

```text
mqtt_connected: true
sensor_data_available: true
sensor_active: true
status: ok
```

Felet var därmed åtgärdat.

---

## 3. Feltest 2 – Ogiltigt MQTT-meddelande
### Fel
Ett meddelande som inte innehöll giltig JSON skickades manuellt till MQTT-topic:

```text
iot/sensor
```

Exempel på testmeddelande:

```text
DETTA ÄR INTE GILTIG JSON
```

### Symptom
API:t kunde inte tolka meddelandet som giltig JSON.

Ett fel registrerades i API-loggen.

### Hur felet upptäcktes
Felet upptäcktes genom API:ts loggning.

Testmeddelandet skickades med Mosquitto:

```powershell
cd "C:\Program Files\mosquitto"
.\mosquitto_pub.exe -h 192.168.0.54 -p 1883 -t "iot/sensor" -m "DETTA ÄR INTE GILTIG JSON"
```

### Orsak
MQTT-meddelandet följde inte systemets definierade JSON-format.

Förväntat format innehåller bland annat:

```json
{
  "sensorId": "room-a-temp-01",
  "temperature": 21.40,
  "humidity": 53.60
}
```

Testmeddelandet innehöll istället vanlig text.

### Åtgärd
API:t validerar mottagna MQTT-meddelanden innan de används som sensordata.

Ogiltiga meddelanden ignoreras och felet loggas.

API-servern fortsätter därefter att behandla nya MQTT-meddelanden.

### Verifiering
Efter det felaktiga meddelandet fortsatte ESP32 att skicka giltiga JSON-meddelanden.

API:t kunde åter ta emot och behandla sensordata utan att behöva startas om.

---

## 4. Felsökningsmetod
Vid problem med systemet kan följande ordning användas:

### Steg 1 – Kontrollera ESP32
Kontrollera Serial Monitor.

Kontrollera:

* Wi-Fi-anslutning
* IP-adress
* MQTT-anslutning
* DHT22-mätningar
* att MQTT-meddelanden skickas

### Steg 2 – Kontrollera MQTT-brokern
Kontrollera att Mosquitto körs och lyssnar på:

```text
192.168.0.54:1883
```

Kontrollera även att MQTT-användarnamn och lösenord är korrekta.

### Steg 3 – Kontrollera Flask API
Starta API:t med:

```powershell
$env:MQTT_PASSWORD="DITT_MQTT_LÖSENORD"
py app.py
```

Kontrollera terminalen efter MQTT-anslutningen.

### Steg 4 – Kontrollera API-status
Kör:

```powershell
Invoke-RestMethod http://localhost:5000/api/health
```

Kontrollera framför allt:

```text
mqtt_connected
sensor_data_available
sensor_active
data_age_seconds
status
```

### Steg 5 – Kontrollera loggen
Kontrollera:

```text
iot_api.log
```

Loggen kan visa MQTT-anslutningar, frånkopplingar, mottagna data och fel.

---

## 5. Vanliga problem
| Problem                          | Möjlig orsak                      | Kontroll                   |
| -------------------------------- | --------------------------------- | -------------------------- |
| ESP32 får ingen Wi-Fi-anslutning | Fel nätverk eller lösenord        | Serial Monitor             |
| MQTT ansluter inte               | Broker körs inte eller fel IP     | Mosquitto + Serial Monitor |
| `not authorised`                 | Fel MQTT-inloggning               | MQTT-konfiguration         |
| Ingen sensordata                 | ESP32 skickar inte                | Serial Monitor             |
| `sensor_active: false`           | Ingen ny data på över 10 sekunder | `/api/health`              |
| API startar inte                 | Fel Python-miljö eller paket      | `py app.py`                |
| Ogiltig sensordata               | Fel JSON-format                   | `iot_api.log`              |
| API visar gammal data            | Sensor-/nätverksavbrott           | `/api/health`              |

## 6. Slutsats
De två feltesterna visar att systemet kan upptäcka både kommunikationsavbrott och ogiltiga MQTT-meddelanden.

Health-endpointen används för att upptäcka avsaknad av nya sensormätningar, medan API:ts validering och loggning hanterar felaktiga MQTT-meddelanden.

Systemet kan därefter fortsätta behandla giltiga sensordata när felet har försvunnit.
