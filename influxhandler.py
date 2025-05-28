# influxhandler.py

from influxdb import InfluxDBClient
from datetime import datetime
import logging

logger = logging.getLogger("influx")

# Connect once at module level
try:
    influx_client = InfluxDBClient(host='localhost', port=8086)
    influx_client.switch_database('weather_data')
    logger.info("[Influx] Connected to weather_data database.")
except Exception as e:
    logger.exception("[Influx] Connection failed")

def log_reading(data):
    if "temperature_C" not in data or "humidity" not in data:
        logger.warning(f"[Influx] Skipped write: missing temperature or humidity in {data}")
        return

    try:
        influx_payload = [{
            "measurement": "readings",
            "tags": {
                "model": str(data.get("model", "unknown")),
                "sensor_id": str(data.get("id", "unknown")),
                "channel": str(data.get("channel", "unknown"))
            },
            "time": datetime.utcnow().isoformat(),
            "fields": {
                "temperature": float(data["temperature_C"]),
                "humidity": float(data["humidity"])
            }
        }]
        influx_client.write_points(influx_payload)
        logger.debug(f"[Influx] Wrote: {influx_payload}")
    except Exception as e:
        logger.exception("[Influx] Failed to write reading")
