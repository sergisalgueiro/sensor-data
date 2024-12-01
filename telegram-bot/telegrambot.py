from telegram.ext import ContextTypes, CommandHandler, ApplicationBuilder
from telegram import Update
from dotenv import load_dotenv
import os
import redis
import datetime
import pytz
import logging
from common.MQTTClient import MQTTClient

# Set up logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
LOCAL_TIMEZONE = pytz.timezone('Europe/Madrid')  # Adjust to your timezone

# Configure Redis
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# MQTT callbacks
mqtt_client = MQTTClient(MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASSWORD)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the bot starts"""
    await update.message.reply_text("/now\n/room_on\n/room_off\n/living_on\n/living_off\n")

async def show_last_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the last data from the Redis"""
    chat_id = update.message.chat_id  # Get the chat ID of the user
    
    # Send all sensors in one only message to the user
    message = ""
    for data in format_last_data():
        message += f"Sensor: {data['sensor']}\n" \
                    f"Time: {data['time']}\n" \
                    f"Temperature: {data['temperature']}\n" \
                    f"Humidity: {data['humidity']}\n"
        if data != format_last_data()[-1]:
            message += "\n"
    await update.message.reply_text(message)

async def room_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message to turn on the room A/C"""
    mqtt_client.client.publish("room_ac", "on")
    await update.message.reply_text("Command sent to turn on Room A/C")

async def room_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message to turn off the room A/C"""
    mqtt_client.client.publish("room_ac", "off")
    await update.message.reply_text("Command sent to turn off Room A/C")

async def living_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message to turn on the living room A/C"""
    mqtt_client.client.publish("living_ac", "on")
    await update.message.reply_text("Command sent to turn on Living Room A/C")

async def living_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message to turn off the living room A/C"""
    mqtt_client.client.publish("living_ac", "off")
    await update.message.reply_text("Command sent to turn off Living Room A/C")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)

def main():
    """Start the bot and handle commands"""
    mqtt_client.connect()
    mqtt_client.client.loop_start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add handlers for the commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("now", show_last_data))
    app.add_handler(CommandHandler("room_on", room_on))
    app.add_handler(CommandHandler("room_off", room_off))
    app.add_handler(CommandHandler("living_on", living_on))
    app.add_handler(CommandHandler("living_off", living_off))
    app.add_error_handler(error)

    # Start the bot
    app.run_polling()

if __name__ == '__main__':
    main()
