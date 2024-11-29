from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv
import os
import redis
import datetime
import pytz

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
LOCAL_TIMEZONE = pytz.timezone('Europe/Madrid')  # Adjust to your timezone

# Configure Redis
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)

def format_last_data():
    formatted_data = []
    for key in redis_client.keys("temp_hum_sensor_*"):
        # Fetch the value from Redis
        value_str = redis_client.get(key).decode()
        epoch, temperature, humidity = value_str.split(',')
        sensor = key.decode().split("_")[-1]

        # Convert epoch time to human-readable time with timezone
        timestamp = datetime.datetime.fromtimestamp(int(epoch), tz=pytz.utc)
        local_time = timestamp.astimezone(LOCAL_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')

        # Format the data with units
        formatted_data.append({
            "sensor": sensor.capitalize(),
            "time": local_time,
            "temperature": f"{temperature} °C",
            "humidity": f"{humidity} %"
        })
    
    return formatted_data

def start(update, context):
    """Send a welcome message when the bot starts"""
    update.message.reply_text("Hello! Send '/now'.")

def show_last_data(update, context):
    """Show the last data from the Redis"""
    chat_id = update.message.chat_id  # Get the chat ID of the user
    
    # Send all sensors in one only message to the user
    for data in format_last_data():
        message = f"Sensor: {data['sensor']}\n" \
                    f"Time: {data['time']}\n" \
                    f"Temperature: {data['temperature']}\n" \
                    f"Humidity: {data['humidity']}\n"
        if data != format_last_data()[-1]:
            message += "\n"
    update.message.reply_text(message)

def main():
    """Start the bot and handle commands"""
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add handlers for the commands
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("now", show_last_data))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()