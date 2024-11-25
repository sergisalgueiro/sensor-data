import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, host, port, user, password, topics, db_manager):
        self.client = mqtt.Client()
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.topics = topics
        self.db_manager = db_manager

        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def connect_and_start(self):
        self.client.username_pw_set(self.user, self.password)
        self.client.connect(self.host, self.port, 60)
        self.client.loop_forever()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker with result code " + str(rc))
        client.subscribe(self.topics)
    
    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT broker with result code " + str(rc))

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            data = payload.split(",")
            topic = msg.topic
            timestamp = int(data[0])
            temperature = float(data[1])
            humidity = float(data[2])

            # Store in database
            self.db_manager.insert_sensor_data(topic, timestamp, temperature, humidity)

        except Exception as e:
            print(f"Error processing message: {e}")
