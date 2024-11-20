CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    time_stamp INTEGER NOT NULL,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL
);
