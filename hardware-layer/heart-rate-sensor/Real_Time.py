"""
Heart Rate Sensor — Real-Time MQTT Viewer
Subscribes to all IoMT device topics and prints live data.
"""
import paho.mqtt.client as mqtt
import json

BROKER = "10.86.251.69"
PORT = 1883
TOPIC = "hospital/iomt/#"

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):

    payload = msg.payload.decode()

    if not payload.startswith("{"):
        return

    log = json.loads(payload)

    print("Device Log:", log)

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)

client.loop_forever()
