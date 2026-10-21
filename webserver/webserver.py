from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
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
LOCAL_TIMEZONE = pytz.timezone('Europe/Madrid')  # Europe/Madrid is the local timezone
STALE_THRESHOLD_SECONDS = 3600  # Consider sensor stale after 1 hour

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Configure Redis
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# Multi-language translations dictionary (Catalan default)
TRANSLATIONS = {
    'ca': {
        'just_now': 'ara mateix',
        'm_ago': 'fa {m}m',
        'h_ago': 'fa {h}h',
        'd_ago': 'fa {d}d',
        'sensors': {
            'room': 'Habitació',
            'living': "Sala d'estar",
            'terrace': 'Terrassa',
            'kitchen': 'Cuina',
            'bathroom': 'Bany',
            'garage': 'Garatge',
        }
    },
    'en': {
        'just_now': 'just now',
        'm_ago': '{m}m ago',
        'h_ago': '{h}h ago',
        'd_ago': '{d}d ago',
        'sensors': {
            'room': 'Room',
            'living': 'Living Room',
            'terrace': 'Terrace',
            'kitchen': 'Kitchen',
            'bathroom': 'Bathroom',
            'garage': 'Garage',
        }
    }
}


def _relative_time(seconds, lang='ca'):
    """Convert elapsed seconds to a human-readable relative time string in selected language."""
    t = TRANSLATIONS.get(lang, TRANSLATIONS['ca'])
    if seconds < 60:
        return t['just_now']
    elif seconds < 3600:
        m = int(seconds // 60)
        return t['m_ago'].format(m=m)
    elif seconds < 86400:
        h = int(seconds // 3600)
        return t['h_ago'].format(h=h)
    else:
        d = int(seconds // 86400)
        return t['d_ago'].format(d=d)


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


def format_data(lang='ca'):
    """
    Fetches and formats data from Redis for display. Default language is Catalan ('ca').
    """
    formatted_data = []
    now = datetime.datetime.now(tz=pytz.utc)
    t = TRANSLATIONS.get(lang, TRANSLATIONS['ca'])

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

        # Raw sensor key identifier (e.g. 'room', 'living', 'terrace')
        sensor_id = key.decode().split("_")[-1].lower()

        # Localized sensor display name (defaults to capitalized ID)
        sensor_name = t['sensors'].get(sensor_id, sensor_id.capitalize())

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
            "sensor_id": sensor_id,
            "sensor": sensor_name,
            "time": local_time,
            "relative_time": _relative_time(age_seconds, lang=lang),
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
    lang = request.args.get('lang', 'ca')
    if lang not in TRANSLATIONS:
        lang = 'ca'
    sensor_data = format_data(lang=lang)
    online_count = sum(1 for s in sensor_data if s['is_online'])
    return render_template('index.html',
                           sensor_data=sensor_data,
                           online_count=online_count,
                           total_count=len(sensor_data),
                           current_lang=lang)


@app.route('/api/sensors')
def api_sensors():
    """JSON API endpoint for auto-refresh, defaults to Catalan."""
    lang = request.args.get('lang', 'ca')
    if lang not in TRANSLATIONS:
        lang = 'ca'
    sensor_data = format_data(lang=lang)
    return jsonify({
        "sensors": sensor_data,
        "online_count": sum(1 for s in sensor_data if s['is_online']),
        "total_count": len(sensor_data),
        "lang": lang
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
