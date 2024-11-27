from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
import redis
import os
import datetime
import pytz

load_dotenv()

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
LOCAL_TIMEZONE = pytz.timezone('Europe/Madrid')  # Adjust to your timezone

app = Flask(__name__)

# Configure Redis
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)

def format_data():
    """
    Fetches and formats data from Redis for display.
    """
    formatted_data = []
    for key in redis_client.keys("temp_hum_sensor_*"):
        # Parse the key
        key_str = key.decode()  # Redis keys are bytes; decode to string
        epoch, temp, hum = key_str.split(',')

        # Convert epoch time to human-readable time with timezone
        timestamp = datetime.fromtimestamp(int(epoch), tz=pytz.utc)
        local_time = timestamp.astimezone(LOCAL_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')

        # Fetch sensor values
        value = redis_client.get(key).decode()

        # Prepare display values with units
        temp_data = f"{temp.capitalize()}: {value.split(',')[0]}°C"
        hum_data = f"{hum.capitalize()}: {value.split(',')[1]}%"

        # Append to formatted data
        formatted_data.append({
            "time": local_time,
            "sensor1": temp_data,
            "sensor2": hum_data,
        })

    return formatted_data

@app.route('/')
def index():
    # Fetch all keys (topics) matching temp_hum_sensor_* and their latest values
    sensor_data = format_data()
    return render_template('index.html', sensor_data=sensor_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
