"""
Heart Rate Sensor — MQTT Log Collector
Subscribes to MQTT and logs pulse oximeter data to CSV.
"""
import paho.mqtt.client as mqtt
import csv
import json
from datetime import datetime

BROKER = "10.86.251.69"
PORT = 1883
TOPIC = "hospital/iomt/pulse"

filename = "iomt_dataset.csv"

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        print("Log received:", data)

        with open(filename, "a", newline="") as file:
            writer = csv.writer(file)

            writer.writerow([
                datetime.now(),
                data.get("device_id"),
                data.get("device_type"),
                data.get("ward"),
                data.get("life_support"),
                data.get("criticality_tier"),
                data.get("protocol"),
                data.get("src_ip"),
                data.get("heart_rate_bpm_pulse"),
                data.get("ppg_raw_value")
            ])

    except Exception as e:
        print("Error:", e)

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)

client.loop_forever()
