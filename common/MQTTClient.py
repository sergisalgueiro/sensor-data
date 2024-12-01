import paho.mqtt.client as mqtt
import logging

# Set up logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self, host, port, user, password):
        self.client = mqtt.Client()
        self.host = host
        self.port = port
        self.user = user
        self.password = password

        self._user_on_connect = None
        self.client.on_disconnect = self.on_disconnect
        self.client.on_connect = self._composite_on_connect
        self.client.on_publish = self.on_publish       

    def connect(self):
        self.client.username_pw_set(self.user, self.password)
        self.client.connect(self.host, self.port, 60)

    def _composite_on_connect(self, client, userdata, flags, rc):
        logger.debug("Connected to MQTT broker with result code " + str(rc))
        if self._user_on_connect:
            self._user_on_connect(client, userdata, flags, rc)

    def set_on_connect_callback(self, callback):
        self._user_on_connect = callback
    
    def on_disconnect(client, userdata, rc):
        logger.debug("Disconnected from MQTT broker with result code " + str(rc))

    def set_on_message_callback(self, callback):
        self.client.on_message = callback

    def publish(self, topic, payload):
        result = self.client.publish(topic, payload)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.debug(f"Published message to topic {topic}")

    def on_publish(self, client, userdata, mid):
        logger.debug(f"Message {mid} published")
