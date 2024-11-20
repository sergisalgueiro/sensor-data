CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
);
