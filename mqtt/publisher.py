import paho.mqtt.client as paho
from time import sleep

broker = "test.mosquitto.org"
port = 1883


def on_publish(client, userdata, result):  # create function for callback
    print("data published \n")


client1 = paho.Client("control1")  # create client object
client1.on_publish = on_publish  # assign function to callback
client1.connect(broker, port)

while True:
    ret = client1.publish("healthconnect/monitor1/temp", 35)
    ret = client1.publish("healthconnect/monitor1/spo2", 92)
    ret = client1.publish("healthconnect/monitor1/bpm", 64)
    ret = client1.publish("healthconnect/monitor1/ecg", 0.4)
    sleep(4)
    ret = client1.publish("healthconnect/monitor1/temp", 32)
    ret = client1.publish("healthconnect/monitor1/spo2", 89)
    ret = client1.publish("healthconnect/monitor1/bpm", 59)
    ret = client1.publish("healthconnect/monitor1/ecg", -0.2)
    sleep(4)


