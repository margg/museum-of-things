#!/usr/bin/python

# This shows a simple example of an MQTT subscriber.

import sys
import mosquitto
import thread
import serial


def on_connect(mqttc, obj, rc):
    print("rc: " + str(rc))


def on_message(mqttc, obj, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


def on_publish(mqttc, obj, mid):
    print("mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(mqttc, obj, level, string):
    print(string)


def mqtt_thread_func(mqttc):
    mqttc.loop_forever()


MQTT_BROKER_IP = "127.0.0.1"
MQTT_BROKER_PORT = 1883

ser = serial.Serial('/dev/ttyS0', 38400, timeout=1)
# todo: subscribe to needed things
ser.write(chr(128))
ser.write(chr(0b10000100))


# If you want to use a specific client id, use
# mqttc = mqtt.Client("client-id")
# but note that the client id must be unique on the broker. Leaving the client
# id parameter empty will generate a random id for you.
mqttc = mosquitto.Mosquitto()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
# Uncomment to enable debug messages
# mqttc.on_log = on_log

# setting testament for that client
dev_path = "museum/floor2/room1/exhibit1"

mqttc.will_set(dev_path, "", 0, True)

mqttc.connect(MQTT_BROKER_IP, MQTT_BROKER_PORT, 60)

mqttc.subscribe("museum/floor2/room1/+", 0)

# publishing message on topic with QoS 0 and the message is not Retained
# mqttc.publish("museum/floor2/room1/exhibit1", "20", 0, False)

try:
    thread.start_new_thread(mqtt_thread_func, (mqttc,))
except:
    print "Error"

print "Started"

while True:
    cc = ser.read(1)
    if len(cc) < 1:
        continue
    cmd = ord(cc)

    if cmd & 0b01000000 != 0:
        mqttc.publish(dev_path, str(cmd), 0, True)
