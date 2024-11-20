import paho.mqtt.client as mqtt
import sqlite3
from datetime import datetime
import json
import os

# SQLite setup
DB_FILE = "sensor_data.db"

# Function to initialize the database
def initialize_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Load schema from file and execute it
    with open("schema.sql", "r") as schema_file:
        schema = schema_file.read()
        cursor.executescript(schema)
    
    conn.commit()
    conn.close()

# Initialize the database
initialize_db()

# MQTT setup
MQTT_BROKER = "localhost"  # Replace with your broker's IP
MQTT_PORT = 1883
# Subscribe to all sensor topics temp_hum_sensor_room, temp_hum_sensor_living, temp_hum_sensor_terrace
MQTT_TOPICS = [("temp_hum_sensor_/#", 0)]  

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe(MQTT_TOPICS)

def on_message(client, userdata, msg):
    try:
        # Decode message payload
        payload = msg.payload.decode()
        data = json.loads(payload)

        # Extract data and write to SQLite
        topic = msg.topic
        timestamp = data.get("timestamp", datetime.utcnow().isoformat())
        value = float(data.get("value", 0))

        # Connect to SQLite and insert data
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sensor_data (topic, timestamp, value) VALUES (?, ?, ?)",
            (topic, timestamp, value)
        )
        conn.commit()
        conn.close()
        print(f"Stored in DB: {topic}, {timestamp}, {value}")

    except Exception as e:
        print(f"Error processing message: {e}")

# MQTT client setup
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_forever()
