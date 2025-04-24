import paho.mqtt.client as paho
from time import sleep

broker = "test.mosquitto.org"
port = 1883

# Create client object with callback API version
client1 = paho.Client(client_id="control1", callback_api_version=paho.CallbackAPIVersion.VERSION1)

def on_publish(client, userdata, result):
    print("Data published")

# Assign callback function
client1.on_publish = on_publish

try:
    # Connect to broker
    client1.connect(broker, port)
    print(f"Connected to broker: {broker}")

    while True:
        # First set of values
        client1.publish("healthconnect/monitor1/temp", 35)
        client1.publish("healthconnect/monitor1/spo2", 92)
        client1.publish("healthconnect/monitor1/bpm", 64)
        client1.publish("healthconnect/monitor1/ecg", 0.4)
        sleep(4)

        # Second set of values
        client1.publish("healthconnect/monitor1/temp", 32)
        client1.publish("healthconnect/monitor1/spo2", 89)
        client1.publish("healthconnect/monitor1/bpm", 59)
        client1.publish("healthconnect/monitor1/ecg", -0.2)
        sleep(4)

except KeyboardInterrupt:
    print("\nStopping publisher...")
    client1.disconnect()
    print("Disconnected from broker")
except Exception as e:
    print(f"Error: {e}")
    client1.disconnect()