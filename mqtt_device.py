#!/usr/bin/python

import sys
import mosquitto
import thread
import serial


def on_connect(mqttc, obj, rc):
    print("Connected. (rc = " + str(rc) + ")")
    open_exhibit()


def on_message(mqttc, obj, msg):
    if msg.topic == DEVICE_TOPIC:
        global SHUTDOWN_MSG
        if msg.payload == SHUTDOWN_MSG:
            close_exhibit()
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


def on_publish(mqttc, obj, mid):
    print("published, mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + ", " + str(granted_qos))


def on_log(mqttc, obj, level, string):
    print(level, string)


def mqtt_thread_func(mqttc):
    mqttc.loop_forever()


def open_exhibit():
    # set RGB LED to green
    ser.write(chr(0b0001100))
    print("Exhibit opened.")


def close_exhibit():
    # set RGB LED to red
    ser.write(chr(0b0110000))
    print("Exhibit closed.")


SHUTDOWN_MSG = "shutdown"
MQTT_BROKER_IP = "127.0.0.1"
MQTT_BROKER_PORT = 1883
MUSEUM_GENERAL_TOPIC = "museum/all"
DEVICE_TOPIC = "museum/floor2/room1/exhibit1"
FLASH_TOPIC = DEVICE_TOPIC + "/flash"

ser = serial.Serial('/dev/ttyS0', 38400, timeout=1)
# todo: subscribe to needed things
# Subscribe to motion/light sensor
ser.write(chr(0b10000001))


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
mqttc.will_set(DEVICE_TOPIC, DEVICE_TOPIC + " shutting down.", 0, True)

mqttc.connect(MQTT_BROKER_IP, MQTT_BROKER_PORT, 60)

mqttc.subscribe(MUSEUM_GENERAL_TOPIC, 0)
mqttc.subscribe(DEVICE_TOPIC, 0)

try:
    thread.start_new_thread(mqtt_thread_func, (mqttc,))
except:
    print "Error"

print "Started"

while True:
    cc = ser.read(1)
    if len(cc) > 0:
        cmd = ord(cc)
        # flash detected
        if cmd == int(0b11000001):
            mqttc.publish(FLASH_TOPIC, "got a flash here", 0, True)
