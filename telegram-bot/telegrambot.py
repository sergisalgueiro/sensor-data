from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv
import os

load_dotenv()

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GRAFANA_IP = os.getenv('GRAFANA_IP')
GRAFANA_PORT = os.getenv('GRAFANA_PORT')
DASHBOARD_UID = os.getenv('DASHBOARD_UID')

# Setup Selenium for headless browsing
options = Options()
options.add_argument('--headless')  # Run headlessly (no GUI)
options.add_argument('--disable-gpu')  # Disable GPU acceleration for Raspberry Pi
options.add_argument('--no-sandbox')  # Fixes certain issues on Raspberry Pi

# Initialize the WebDriver (Chromium with headless options)
driver = webdriver.Chrome(options=options)

# Grafana Dashboard URL
GRAFANA_URL = 'http://' + GRAFANA_IP + ':' + GRAFANA_PORT + '/d/' + DASHBOARD_UID

def capture_dashboard():
    # Open Grafana dashboard in browser
    driver.get(GRAFANA_URL)

    # Wait for the page to load
    time.sleep(5)

    # Save screenshot
    screenshot_path = 'grafana_dashboard.png'
    driver.save_screenshot(screenshot_path)
    return screenshot_path

def start(update, context):
    """Send a welcome message when the bot starts"""
    update.message.reply_text("Hello! Send '/show_dashboard' to get the Grafana dashboard image.")

def show_dashboard(update, context):
    """Capture and send the Grafana dashboard image to the user"""
    chat_id = update.message.chat_id  # Get the chat ID of the user
    image_path = capture_dashboard()  # Capture the dashboard screenshot
    
    # Send the image to the user
    context.bot.send_photo(chat_id=chat_id, photo=open(image_path, 'rb'))
    update.message.reply_text("Here is your Grafana dashboard image!")

def main():
    """Start the bot and handle commands"""
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add handlers for the commands
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("show_dashboard", show_dashboard))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    try:
        main()
    finally:
        driver.quit()  # Close the Selenium driver when the bot stops
