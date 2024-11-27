from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
import redis
import os

load_dotenv()
# Configuration
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

app = Flask(__name__)

# Configure Redis
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)

@app.route('/')
def index():
    # Fetch all keys (topics) matching temp_hum_sensor_* and their latest values
    sensor_data = {key.decode(): redis_client.get(key).decode() for key in redis_client.keys("temp_hum_sensor_*")}
    return render_template('index.html', sensor_data=sensor_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
