# Säkerhetsanalys
## 1. Översikt
Systemet består av en ESP32-C6 med DHT22-sensor, Wi-Fi, MQTT-broker och ett Flask API.

Säkerheten har fokuserat på autentisering, hantering av hemligheter, validering av data och begränsning av åtkomst.

## 2. Säkerhetsrisker
### Risk 1 – Obehörig åtkomst till MQTT
Om MQTT-brokern tillåter anonyma anslutningar kan obehöriga klienter ansluta och publicera eller läsa meddelanden.

### Åtgärd
MQTT-brokern är konfigurerad med:

```text
allow_anonymous false
```

Anslutning kräver användarnamn och lösenord.

ESP32 och Flask API använder MQTT-användaren `iotuser`.

Detta minskar risken för att obehöriga klienter ansluter till MQTT-brokern.

### Begränsning
MQTT körs fortfarande på port 1883 utan TLS. Användarnamn och lösenord skickas därför inte över en krypterad MQTT-anslutning.

---

## 3. Risk 2 – Lösenord i källkod
Att lagra Wi-Fi- eller MQTT-lösenord direkt i källkoden innebär en risk om projektet publiceras på GitHub.

### Åtgärd
ESP32:s hemliga uppgifter ligger i:

```text
src/esp32/esp32_sensor/secrets.h
```

Filen är inkluderad i `.gitignore` och ska därför inte publiceras i Git-repositoriet.

Flask API hämtar MQTT-lösenordet från en miljövariabel istället för att lagra det direkt i `app.py`.

Exempel:

```powershell
$env:MQTT_PASSWORD="DITT_MQTT_LÖSENORD"
py app.py
```

### Begränsning
Hemligheterna finns fortfarande lokalt på den dator och ESP32 där systemet körs. De behöver därför hanteras säkert av den som installerar systemet.

---

## 4. Risk 3 – Ogiltig eller manipulerad sensordata
En MQTT-klient kan försöka skicka felaktiga eller manipulerade meddelanden till topicen.

Exempelvis kan meddelandet sakna obligatoriska fält eller innehålla data som inte är giltig JSON.

### Åtgärd
API:t validerar mottagna MQTT-meddelanden.

Följande kontroller görs bland annat:

* meddelandet måste vara giltig JSON
* `sensorId` måste finnas
* `temperature` måste finnas
* `humidity` måste finnas

Felaktiga meddelanden loggas och behandlas inte som giltiga sensormätningar.

### Test
Ett ogiltigt MQTT-meddelande skickades manuellt till:

```text
iot/sensor
```

API:t upptäckte felet och fortsatte därefter att ta emot giltiga sensormätningar.

---

## 5. Risk 4 – Avbrott i sensor- eller nätverkskommunikation
Om ESP32 slutar skicka data kan API:t annars fortsätta visa den senast mottagna mätningen och det kan se ut som att systemet fungerar.

### Åtgärd
API:t övervakar tiden sedan den senaste sensormätningen.

Systemet använder:

```text
Maximal dataålder: 10 sekunder
```

Om ingen ny data kommer inom denna tid sätts:

```text
sensor_active: false
status: error
```

Det gör att kommunikationsavbrott kan upptäckas automatiskt.

---

## 6. MQTT-återanslutning
ESP32 kontrollerar om MQTT-anslutningen fortfarande är aktiv.

Om anslutningen bryts försöker ESP32 ansluta igen.

Mellan försöken väntar enheten fem sekunder.

Det gör systemet mer robust mot tillfälliga kommunikationsproblem.

---

## 7. Loggning
Säkerhets- och kommunikationsrelaterade händelser loggas av API-servern.

Exempel:

* MQTT-anslutningar
* MQTT-frånkopplingar
* mottagen sensordata
* ogiltiga meddelanden
* valideringsfel
* kommunikationsfel

Loggfil:

```text
iot_api.log
```

Loggfilen är exkluderad från Git med `.gitignore`.

---

## 8. Kvarvarande säkerhetsbegränsningar
Systemet uppfyller grundläggande säkerhetskrav men är inte fullt säkert för en produktionsmiljö.

Viktigaste begränsningarna är:

1. MQTT använder port 1883 utan TLS.
2. API:t använder HTTP istället för HTTPS.
3. API:t har ingen avancerad autentisering eller behörighetskontroll.
4. Systemet är främst utformat för ett lokalt nätverk.
5. Det finns ingen central logghantering.
6. Det finns ingen databas med historiska mätningar.

## 9. Möjliga framtida förbättringar
För en produktionsmiljö kan säkerheten förbättras genom att införa:

* MQTT över TLS
* HTTPS för API:t
* starkare API-autentisering
* behörighetskontroll
* nätverkssegmentering
* brandväggsregler
* centraliserad loggning
* säker lagring och rotation av lösenord
* databas med åtkomstkontroll

## 10. Sammanfattning
Systemet använder MQTT-autentisering, skyddad hantering av hemligheter, validering av inkommande data och övervakning av sensoraktivitet.

Det minskar risken för obehörig åtkomst, felaktig data och oupptäckta kommunikationsavbrott.

De största kvarvarande säkerhetsbristerna är att MQTT inte använder TLS och att API:t använder HTTP istället för HTTPS.
