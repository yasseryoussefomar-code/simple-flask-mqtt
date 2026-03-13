import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
import paho.mqtt.client as mqtt

app = Flask(__name__)

MONGODB_URI = os.getenv("MONGODB_URI")

MQTT_BROKER = "broker.hivemq.com"
DATA_TOPIC = "iot/simple/data"
CMD_TOPIC = "iot/simple/cmd"

client = MongoClient(MONGODB_URI)
db = client["iot_demo"]
readings = db["readings"]

def on_connect(client, userdata, flags, rc, properties=None):
    client.subscribe(DATA_TOPIC)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())

    readings.insert_one({
        "value": payload["value"],
        "time": datetime.utcnow()
    })

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, 1883)
mqtt_client.loop_start()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/data")
def data():
    docs = list(readings.find({}, {"_id":0}))
    return jsonify(docs)

@app.route("/send", methods=["POST"])
def send():
    command = request.form["cmd"]

    mqtt_client.publish(CMD_TOPIC, json.dumps({"command":command}))

    return "Command sent"

if __name__ == "__main__":
    app.run()
