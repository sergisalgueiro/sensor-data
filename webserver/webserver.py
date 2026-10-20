from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
import redis
import os
import datetime
import pytz
import math
from prometheus_flask_exporter import PrometheusMetrics

load_dotenv()

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
LOCAL_TIMEZONE = pytz.timezone('Europe/Madrid')  # Adjust to your timezone
STALE_THRESHOLD_SECONDS = 3600  # Consider sensor stale after 1 hour

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Configure Redis
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)


def _relative_time(seconds):
    """Convert elapsed seconds to a human-readable relative time string."""
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        m = int(seconds // 60)
        return f"{m}m ago"
    elif seconds < 86400:
        h = int(seconds // 3600)
        return f"{h}h ago"
    else:
        d = int(seconds // 86400)
        return f"{d}d ago"


def _temp_class(value):
    """Return a CSS class based on temperature range for color coding."""
    if value is None:
        return "temp-na"
    if value < 10:
        return "temp-freezing"
    elif value < 18:
        return "temp-cold"
    elif value < 22:
        return "temp-cool"
    elif value < 26:
        return "temp-comfortable"
    elif value < 30:
        return "temp-warm"
    else:
        return "temp-hot"


def format_data():
    """
    Fetches and formats data from Redis for display.
    """
    formatted_data = []
    now = datetime.datetime.now(tz=pytz.utc)

    for key in redis_client.keys("temp_hum_sensor_*"):
        # Fetch the value from Redis
        value_str = redis_client.get(key).decode()  # Decode bytes to string
        epoch, temperature, humidity = value_str.split(',')

        # Convert epoch time to human-readable time with timezone
        timestamp = datetime.datetime.fromtimestamp(int(epoch), tz=pytz.utc)
        local_time = timestamp.astimezone(LOCAL_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')

        # Calculate age for staleness detection
        age_seconds = (now - timestamp).total_seconds()
        is_stale = age_seconds > STALE_THRESHOLD_SECONDS

        # sensor is the key without the prefix
        sensor = key.decode().split("_")[-1]

        # Parse numeric values, handle NaN gracefully
        try:
            temp_val = float(temperature)
            hum_val = float(humidity)
            temp_valid = not math.isnan(temp_val)
            hum_valid = not math.isnan(hum_val)
        except (ValueError, TypeError):
            temp_val = 0
            hum_val = 0
            temp_valid = False
            hum_valid = False

        is_online = temp_valid and not is_stale

        # Format the data with units
        formatted_data.append({
            "sensor": sensor.capitalize(),
            "time": local_time,
            "relative_time": _relative_time(age_seconds),
            "temperature": f"{temp_val:.1f}" if temp_valid else "—",
            "humidity": f"{hum_val:.1f}" if hum_valid else "—",
            "temp_value": temp_val if temp_valid else None,
            "hum_value": hum_val if hum_valid else None,
            "temp_class": _temp_class(temp_val if temp_valid else None),
            "is_stale": is_stale,
            "is_online": is_online,
        })

    # Sort alphabetically by sensor name
    formatted_data.sort(key=lambda x: x['sensor'])
    return formatted_data


@app.route('/')
def index():
    # Fetch all keys (topics) matching temp_hum_sensor_* and their latest values
    sensor_data = format_data()
    online_count = sum(1 for s in sensor_data if s['is_online'])
    return render_template('index.html',
                           sensor_data=sensor_data,
                           online_count=online_count,
                           total_count=len(sensor_data))


@app.route('/api/sensors')
def api_sensors():
    """JSON API endpoint for auto-refresh."""
    sensor_data = format_data()
    return jsonify({
        "sensors": sensor_data,
        "online_count": sum(1 for s in sensor_data if s['is_online']),
        "total_count": len(sensor_data),
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
