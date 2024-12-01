import sqlite3
import logging

#  Setup logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


TEMP_THRESHOLD = 0.5
HUM_THRESHOLD = 1.0

class DatabaseManager:
    def __init__(self, db_file, schema_file):
        self.db_file = db_file
        self.schema_file = schema_file
        self.initialize_db()


    def initialize_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        with open(self.schema_file, "r") as schema_file:
            schema = schema_file.read()
            cursor.executescript(schema)
        conn.commit()
        conn.close()

    def insert_sensor_data(self, topic, timestamp, temperature, humidity):
        # insert data into the database only if the temperature or humidity value is different from the previous one by more than the threshold
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT temperature, humidity FROM sensor_data WHERE topic = ? ORDER BY time_stamp DESC LIMIT 1",
                (topic,)
            )
            row = cursor.fetchone()
            if row is None or abs(row[0] - temperature) > TEMP_THRESHOLD or abs(row[1] - humidity) > HUM_THRESHOLD:
                cursor.execute(
                    "INSERT INTO sensor_data (topic, time_stamp, temperature, humidity) VALUES (?, ?, ?, ?)",
                    (topic, timestamp, temperature, humidity)
                )
                conn.commit()
                logger.debug(f"Stored in DB: {topic}, {timestamp}, {temperature}, {humidity}")
            conn.close()
        except sqlite3.Error as e:
            logger.debug(f"Database error: {e}")
