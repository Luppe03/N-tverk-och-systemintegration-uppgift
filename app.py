from flask import Flask, jsonify
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import logging
import os

MQTT_SERVER = "192.168.0.54"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/sensor"
MQTT_USER = "iotuser"
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
API_PORT = 5000

MAX_DATA_AGE_SECONDS = 10

logging.basicConfig(
    filename="iot_api.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

latest_data = {
    "sensorId": None,
    "temperature": None,
    "humidity": None,
    "timestamp": None
}

mqtt_connected = False


def on_connect(client, userdata, flags, reason_code, properties):
    global mqtt_connected

    if reason_code == 0:
        mqtt_connected = True

        print("Ansluten till MQTT!")
        logger.info("MQTT-anslutning etablerad")

        result = client.subscribe(MQTT_TOPIC)

        if result[0] == mqtt.MQTT_ERR_SUCCESS:
            print(f"Prenumererar på: {MQTT_TOPIC}")
            logger.info(
                f"Prenumererar på MQTT-topic: {MQTT_TOPIC}"
            )
        else:
            print("Kunde inte prenumerera på MQTT-topic.")
            logger.error(
                f"Kunde inte prenumerera på MQTT-topic: {MQTT_TOPIC}"
            )

    else:
        mqtt_connected = False

        print(f"MQTT-anslutning misslyckades: {reason_code}")
        logger.error(
            f"MQTT-anslutning misslyckades. Felkod: {reason_code}"
        )


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    global mqtt_connected

    mqtt_connected = False

    print("MQTT-anslutningen bröts.")
    logger.warning(
        f"MQTT-anslutningen bröts. Felkod: {reason_code}"
    )


def on_message(client, userdata, msg):
    global latest_data

    try:
        payload = msg.payload.decode("utf-8")

        data = json.loads(payload)

        if "sensorId" not in data:
            raise ValueError("sensorId saknas")

        if "temperature" not in data:
            raise ValueError("temperature saknas")

        if "humidity" not in data:
            raise ValueError("humidity saknas")

        latest_data = {
            "sensorId": data["sensorId"],
            "temperature": data["temperature"],
            "humidity": data["humidity"],
            "timestamp": datetime.now().isoformat()
        }

        print("Nytt sensorvärde:")
        print(latest_data)

        logger.info(
            f"Sensorvärde mottaget: "
            f"sensorId={latest_data['sensorId']}, "
            f"temperature={latest_data['temperature']}°C, "
            f"humidity={latest_data['humidity']}%"
        )

    except json.JSONDecodeError as e:
        print("Fel: MQTT-meddelandet innehåller ogiltig JSON.")
        logger.error(f"Ogiltig JSON från MQTT: {e}")

    except ValueError as e:
        print(f"Felaktig sensordata: {e}")
        logger.error(f"Felaktig sensordata: {e}")

    except UnicodeDecodeError as e:
        print("Fel: MQTT-meddelandet kunde inte avkodas.")
        logger.error(f"Avkodningsfel i MQTT-meddelande: {e}")

    except Exception as e:
        print("Fel vid behandling av MQTT-data:")
        print(e)
        logger.exception(
            f"Oväntat fel vid behandling av MQTT-data: {e}"
        )


mqtt_client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="iot-api-server"
)

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message


print("Ansluter till MQTT-server...")

logger.info(
    f"Försöker ansluta till MQTT-server "
    f"{MQTT_SERVER}:{MQTT_PORT}"
)

try:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.connect(MQTT_SERVER, MQTT_PORT, 60)

    logger.info("MQTT connect-anrop lyckades")

except Exception as e:
    print("Kunde inte ansluta till MQTT-server.")
    print(e)

    logger.exception(
        f"MQTT-anslutning misslyckades: {e}"
    )


mqtt_client.loop_start()


@app.route("/api/sensor", methods=["GET"])
def get_sensor():

    if latest_data["sensorId"] is None:

        logger.warning(
            "API-anrop till /api/sensor men ingen sensordata finns"
        )

        return jsonify({
            "status": "error",
            "message": "Inga sensordata har mottagits ännu."
        }), 503

    logger.info("API-anrop: GET /api/sensor")

    return jsonify({
        "status": "ok",
        "data": latest_data
    })


@app.route("/api/health", methods=["GET"])
def health():

    now = datetime.now()

    data_age_seconds = None
    sensor_data_available = latest_data["sensorId"] is not None

    if latest_data["timestamp"] is not None:

        last_update = datetime.fromisoformat(
            latest_data["timestamp"]
        )

        data_age_seconds = (
            now - last_update
        ).total_seconds()

    sensor_active = (
        sensor_data_available
        and data_age_seconds <= MAX_DATA_AGE_SECONDS
    )

    system_ok = (
        mqtt_connected
        and sensor_active
    )

    if system_ok:
        status = "ok"
    else:
        status = "error"

    logger.info(
        f"Health check: status={status}, "
        f"mqtt_connected={mqtt_connected}, "
        f"sensor_active={sensor_active}, "
        f"data_age_seconds={data_age_seconds}"
    )

    return jsonify({
        "status": status,
        "mqtt_connected": mqtt_connected,
        "sensor_data_available": sensor_data_available,
        "sensor_active": sensor_active,
        "last_sensor_update": latest_data["timestamp"],
        "data_age_seconds": data_age_seconds,
        "max_allowed_data_age_seconds": MAX_DATA_AGE_SECONDS
    })


if __name__ == "__main__":

    print()
    print("====================================")
    print(" IoT Sensor API")
    print("====================================")
    print(f"API: http://localhost:{API_PORT}")
    print(f"Sensor: http://localhost:{API_PORT}/api/sensor")
    print(f"Health: http://localhost:{API_PORT}/api/health")
    print("Loggfil: iot_api.log")
    print("====================================")
    print()

    logger.info("IoT Sensor API startas")

    app.run(
        host="0.0.0.0",
        port=API_PORT,
        debug=False
    )