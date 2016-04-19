#!/usr/bin/python

import mosquitto
import thread
import serial

from config import MQTT_BROKER_IP, MQTT_BROKER_PORT
from config import MUSEUM_GENERAL_TOPIC, SHUTDOWN_MSG, MUSEUM_TOPIC, OPEN_MSG, FLASH_TOPIC_PATH

ser = serial.Serial('/dev/ttyS0', 38400, timeout=1)
museum_open = False
photo_counts = {}


def on_connect(mqttc, obj, rc):
    print("Connected. (rc = " + str(rc) + ")")


def on_message(mqttc, obj, msg):
    if msg.payload.endswith(FLASH_TOPIC_PATH):
        dev = msg.topic[:-len(FLASH_TOPIC_PATH)]
        if dev in photo_counts.keys():
            photo_counts[dev] += 1
        else:
            photo_counts[dev] = 1
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


def on_publish(mqttc, obj, mid):
    print("published, mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + ", " + str(granted_qos))


def on_log(mqttc, obj, level, string):
    print(level, string)


def mqtt_thread_func(mqttc):
    mqttc.loop_forever()


# If you want to use a specific client id, use
# mqttc = mqtt.Client("client-id")
# but note that the client id must be unique on the broker. Leaving the client
# id parameter empty will generate a random id for you.
mqttc = mosquitto.Mosquitto()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
# Enable debug messages
# mqttc.on_log = on_log


# todo: subscribe to needed things
# Subscribe to Button 1 - on/off switch
ser.write(chr(0b10010000))

# Set testament for the client
mqttc.will_set(MUSEUM_GENERAL_TOPIC, SHUTDOWN_MSG, 0, True)
mqttc.connect(MQTT_BROKER_IP, MQTT_BROKER_PORT, 60)

mqttc.subscribe(MUSEUM_TOPIC + "/*", 0)

try:
    thread.start_new_thread(mqtt_thread_func, (mqttc,))
except:
    print "Error"

while True:
    cc = ser.read(1)
    if len(cc) > 0:
        cmd = ord(cc)
        # Button 1 pressed - on/off
        if cmd == int(0b11000011):
            mqttc.publish(MUSEUM_GENERAL_TOPIC, SHUTDOWN_MSG if museum_open else OPEN_MSG, 0, True)
            museum_open = not museum_open
