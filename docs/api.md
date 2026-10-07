# API-dokumentation
## 1. Översikt
Systemet innehåller ett REST-baserat API byggt med Flask.

API:t gör den senaste sensordatan tillgänglig för andra system och innehåller även en health-endpoint för övervakning.

API-servern körs på port:

```text
5000
```

Basadress lokalt:

```text
http://localhost:5000
```

## 2. GET /api/sensor
Returnerar den senaste mottagna sensordatan.

### HTTP-metod
```text
GET
```

### Endpoint
```text
/api/sensor
```

### Exempel
```text
GET http://localhost:5000/api/sensor
```

### Lyckat svar
HTTP-status:

```text
200 OK
```

Exempel:

```json
{
  "status": "ok",
  "data": {
    "sensorId": "room-a-temp-01",
    "temperature": 21.40,
    "humidity": 53.60,
    "timestamp": "2026-10-07T13:55:53"
  }
}
```

### Om sensordata saknas
Om API:t inte har tagit emot någon sensordata returneras:

```text
503 Service Unavailable
```

Exempel:

```json
{
  "status": "error",
  "message": "Ingen sensordata tillgänglig"
}
```

## 3. GET /api/health
Används för att kontrollera systemets status.

Endpointen kontrollerar bland annat MQTT-anslutningen och hur gammal den senaste sensordatan är.

### HTTP-metod
```text
GET
```

### Endpoint
```text
/api/health
```

### Exempel
```text
GET http://localhost:5000/api/health
```

### Systemet fungerar
HTTP-status:

```text
200 OK
```

Exempel:

```json
{
  "status": "ok",
  "mqtt_connected": true,
  "sensor_data_available": true,
  "sensor_active": true,
  "data_age_seconds": 2.1,
  "max_allowed_data_age_seconds": 10,
  "last_sensor_update": "2026-10-07T13:55:53"
}
```

### Sensor eller kommunikation har problem
Om systemet inte har fått ny sensordata inom 10 sekunder rapporteras sensorn som inaktiv.

Exempel:

```json
{
  "status": "error",
  "mqtt_connected": true,
  "sensor_data_available": true,
  "sensor_active": false,
  "data_age_seconds": 22.4,
  "max_allowed_data_age_seconds": 10,
  "last_sensor_update": "2026-10-07T13:55:53"
}
```

Detta gör att en avbruten sensor- eller nätverkskommunikation kan upptäckas automatiskt.

## 4. Dataformat
API:t använder JSON.

Sensordatan innehåller följande fält:

| Fält          | Datatyp | Beskrivning                          |
| ------------- | ------- | ------------------------------------ |
| `sensorId`    | string  | Identifierar sensorn                 |
| `temperature` | number  | Temperatur i °C                      |
| `humidity`    | number  | Luftfuktighet i procent              |
| `timestamp`   | string  | Tidpunkt då API:t tog emot mätningen |

## 5. MQTT till API
Sensordatan skickas först från ESP32-C6 till MQTT-brokern.

```text
ESP32-C6
    |
    | MQTT
    v
Mosquitto
    |
    | Topic: iot/sensor
    v
Flask API
```

API:t prenumererar på:

```text
iot/sensor
```

När ett MQTT-meddelande tas emot valideras JSON-datan innan den sparas som senaste mätning.

## 6. Felhantering
API:t hanterar bland annat:

* saknad sensordata
* ogiltig JSON
* saknade obligatoriska fält
* felaktiga datatyper eller värden
* felaktig teckenkodning
* MQTT-frånkoppling

Ogiltiga MQTT-meddelanden ska inte stoppa API-servern. Felet loggas och API:t fortsätter att behandla nya giltiga meddelanden.

## 7. Testa API:t
API:t kan testas från PowerShell.

### Testa sensordata
```powershell
Invoke-RestMethod http://localhost:5000/api/sensor
```

### Testa health
```powershell
Invoke-RestMethod http://localhost:5000/api/health
```

Om systemet fungerar ska `/api/sensor` visa den senaste temperatur- och luftfuktighetsmätningen och `/api/health` ska visa systemets aktuella status.

## 8. API-begränsningar
API:t är för närvarande avsett för ett lokalt nätverk.

Det använder HTTP istället för HTTPS och har ingen avancerad API-autentisering.

För en produktionsmiljö bör exempelvis HTTPS och autentisering införas.
