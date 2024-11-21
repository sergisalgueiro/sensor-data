from datetime import datetime
from dotenv import load_dotenv
import os
from DatabaseManager import DatabaseManager
from MQTTClient import MQTTClient

if __name__ == "__main__":
    load_dotenv()
    # Configuration
    MQTT_HOST = os.getenv("MQTT_HOST")
    MQTT_PORT = int(os.getenv("MQTT_PORT"))
    MQTT_USER = os.getenv("MQTT_USER")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
    DB_FILE = "sensor_data.db"
    SCHEMA_FILE = "schema.sql"
    MQTT_TOPICS = [("temp_hum_sensor_room", 0), ("temp_hum_sensor_living", 0), ("temp_hum_sensor_terrace", 0)]

    # Initialize components
    db_manager = DatabaseManager(DB_FILE, SCHEMA_FILE)
    mqtt_client = MQTTClient(MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASSWORD, MQTT_TOPICS, db_manager)

    # Start the MQTT client
    mqtt_client.connect_and_start()
