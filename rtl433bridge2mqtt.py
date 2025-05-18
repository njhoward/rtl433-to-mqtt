# rtl433bridge2mqtt.py
import subprocess
import json
from config import MQTT_BROKER, MQTT_PORT, KNOWN_MODELS
import logging
from datetime import datetime
from config import SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT
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
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

logging.info("Listening to rtl_433...")

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
                logging.info(f"Published to {topic}: {data}")
            else:
                suspicious_logger.info(f"Unknown or unhandled model: {line}")

        except json.JSONDecodeError:
            logging.warning(f"Failed to decode JSON: {line}")
            continue

except KeyboardInterrupt:
    logging.info("Keyboard interrupt received. Exiting...")

finally:
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    rtl433_proc.terminate()
    logger.info("Cleaned up and terminated subprocess.")
