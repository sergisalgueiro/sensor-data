from datetime import datetime
from dotenv import load_dotenv
import redis
import os
import logging
from DatabaseManager import DatabaseManager
from common.MQTTClient import MQTTClient
from prometheus_client import start_http_server, Counter, Gauge

# Set up logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get file directory
file_dir = os.path.dirname(os.path.abspath(__file__)) + "/"

load_dotenv()
# Configuration
MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
DB_FILE = file_dir + "sensor_data.db"
SCHEMA_FILE = file_dir + "schema.sql"
MQTT_TOPICS = [("temp_hum_sensor_room", 0), ("temp_hum_sensor_living", 0), ("temp_hum_sensor_terrace", 0)]

# Prometheus Metrics
MQTT_MESSAGES_TOTAL = Counter('sensor_messages_received_total', 'Total MQTT sensor messages received', ['topic'])
SENSOR_LAST_SEEN = Gauge('sensor_last_seen_timestamp_seconds', 'Timestamp of last message received from sensor', ['topic'])
SENSOR_FAILURES_TOTAL = Counter('sensor_failures_total', 'Total sensor failure packets (NaN)', ['topic'])
SENSOR_DB_WRITES_TOTAL = Counter('sensor_db_writes_total', 'Total sensor readings written to SQLite', ['topic'])
SENSOR_CURRENT_TEMP = Gauge('sensor_current_temperature_celsius', 'Current temperature reported by sensor', ['topic'])
SENSOR_CURRENT_HUMIDITY = Gauge('sensor_current_humidity_percent', 'Current humidity reported by sensor', ['topic'])

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPICS)

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = payload.split(",")
        topic = msg.topic
        timestamp = int(data[0])
        temperature = float(data[1])
        humidity = float(data[2])

        # Track Prometheus metrics
        MQTT_MESSAGES_TOTAL.labels(topic=topic).inc()
        SENSOR_LAST_SEEN.labels(topic=topic).set(timestamp)

        # Store in Redis
        redis_client.set(topic, payload)

        # Check if the values are NaN
        if temperature != temperature or humidity != humidity:
            SENSOR_FAILURES_TOTAL.labels(topic=topic).inc()
            db_manager.insert_sensor_failure(topic, timestamp)
            return

        SENSOR_CURRENT_TEMP.labels(topic=topic).set(temperature)
        SENSOR_CURRENT_HUMIDITY.labels(topic=topic).set(humidity)

        # Store in database
        db_manager.insert_sensor_data(topic, timestamp, temperature, humidity)
        SENSOR_DB_WRITES_TOTAL.labels(topic=topic).inc()

    except Exception as e:
        logger.error(f"Error processing message: {e}")

if __name__ == "__main__":
    # Start Prometheus metrics HTTP server on port 8001
    METRICS_PORT = int(os.getenv("METRICS_PORT", 8001))
    start_http_server(METRICS_PORT)
    logger.info(f"Prometheus metrics exporter started on port {METRICS_PORT}")

    # Initialize components
    db_manager = DatabaseManager(DB_FILE, SCHEMA_FILE)
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    mqtt_client = MQTTClient(MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASSWORD)
    mqtt_client.set_on_connect_callback(on_connect)
    mqtt_client.set_on_message_callback(on_message)

    # Start the MQTT client
    mqtt_client.connect()
    mqtt_client.client.loop_forever()
