# rtl433bridge2mqtt.py
import subprocess
import json
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, KNOWN_MODELS
import logging
from datetime import datetime
from logger import setup_logging

# MQTT Setup
MQTT_TOPIC_PREFIX = "rtl_433"

#logging setup
setup_logging
suspicious_logger = logging.getLogger("suspicious")



# Start rtl_433 subprocess
rtl433_proc = subprocess.Popen(
    ["rtl_433", "-F", "json"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
    bufsize=1
)

# MQTT Connect
try:
    mqtt_client = mqtt.Client()
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    logging.info("[Main] Listening to rtl_433...")
except Exception as e:
    logging.exception(f"[Main] MQTT connection failed: {e}")


try:
    for line in rtl433_proc.stdout:
        line = line.strip()
        if not line.startswith("{"):
            continue  # skip non-JSON lines

        try:
            data = json.loads(line)
            model = data.get("model")
            device_id = str(data.get("id"))

            if model in KNOWN_MODELS and device_id:
                topic = f"{MQTT_TOPIC_PREFIX}/{model}/{device_id}"
                mqtt_client.publish(topic, json.dumps(data))
                logging.info(f"[Main] Published to {topic}: {data}")
            else:
                suspicious_logger.info(f"[Main] Unknown or unhandled model: {line}")

        except json.JSONDecodeError:
            logging.warning(f"[Main] Failed to decode JSON: {line}")
            continue

except KeyboardInterrupt:
    logging.info("[Main] Keyboard interrupt received. Exiting...")

finally:
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    rtl433_proc.terminate()
    logging.info("[Main] Cleaned up and terminated subprocess.")
