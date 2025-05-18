import subprocess
import json
import paho.mqtt.client as mqtt
import logging
from datetime import datetime

# MQTT Setup
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "rtl_433"

# Logging Setup
logging.basicConfig(
    filename="/home/admin/logs/rtl433_unknown.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(console_handler)

# Known models to process
KNOWN_MODELS = ["Prologue-TH", "AmbientWeather-WH31E"]

# Start rtl_433 subprocess
rtl433_proc = subprocess.Popen(
    ["rtl_433", "-F", "json"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
    bufsize=1
)

# MQTT Connect
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

logger.info("Listening to rtl_433...")

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
                logger.info(f"Published to {topic}: {data}")
            else:
                logger.info(f"Unknown or unhandled model: {line}")

        except json.JSONDecodeError:
            logger.warning(f"Failed to decode JSON: {line}")
            continue

except KeyboardInterrupt:
    logger.info("Keyboard interrupt received. Exiting...")

finally:
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    rtl433_proc.terminate()
    logger.info("Cleaned up and terminated subprocess.")
