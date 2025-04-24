import paho.mqtt.client as mqtt
from flask_socketio import SocketIO

class MQTTSubscriber:
    def __init__(self, socketio):
        self.socketio = socketio
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def connect(self):
        self.client.connect("test.mosquitto.org", 1883, 60)
        self.client.loop_start()
    
    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker with result code " + str(rc))
        # Subscribe to all healthconnect topics
        self.client.subscribe("healthconnect/monitor1/#")
    
    def on_message(self, client, userdata, msg):
        topic = msg.topic
        value = float(msg.payload.decode())
        # Extract the parameter from the topic
        param = topic.split('/')[-1]
        # Emit the data through Socket.IO
        self.socketio.emit('vital_signs_update', {
            'parameter': param,
            'value': value
        })