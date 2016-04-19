#!/usr/bin/python

import mosquitto
import thread
import serial

from config import MQTT_BROKER_IP, MQTT_BROKER_PORT, MUSEUM_GENERAL_TOPIC, SHUTDOWN_MSG, MUSEUM_TOPIC

ser = serial.Serial('/dev/ttyS0', 38400, timeout=1)


def on_connect(mqttc, obj, rc):
    print("Connected. (rc = " + str(rc) + ")")


def on_message(mqttc, obj, msg):
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
# Subscribe to motion/light sensor
ser.write(chr(0b10000001))

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
        # flash detected
        if cmd == int(0b11000001):
            mqttc.publish(FLASH_TOPIC, "got a flash here", 0, True)
