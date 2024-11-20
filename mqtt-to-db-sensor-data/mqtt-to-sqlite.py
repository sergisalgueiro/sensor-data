import paho.mqtt.client as mqtt
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import json
import os

# Load environment variables
load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

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

# Subscribe to all sensor topics temp_hum_sensor_room, temp_hum_sensor_living, temp_hum_sensor_terrace
MQTT_TOPICS = [("temp_hum_sensor_room", 0), ("temp_hum_sensor_living", 0), ("temp_hum_sensor_terrace", 0)]

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe(MQTT_TOPICS)

def on_message(client, userdata, msg):
    try:
        # Decode message payload with the format: epoch,temperature,humidity
        payload = msg.payload.decode()
        data = payload.split(",")

        # Extract data and write to SQLite
        topic = msg.topic
        timestamp = int(data[0])
        temperature = float(data[1])
        humidity = float(data[2])

        # Connect to SQLite and insert data
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sensor_data (topic, time_stamp, temperature, humidity) VALUES (?, ?, ?)",
            (topic, timestamp, temperature, humidity)
        )
        conn.commit()
        conn.close()
        print(f"Stored in DB: {topic}, {timestamp}, {temperature}, {humidity}")

    except Exception as e:
        print(f"Error processing message: {e}")

# MQTT client setup
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
mqtt_client.loop_forever()
