#!/usr/bin/python

import sys
import mosquitto
import thread
import serial

from config import *

if len(sys.argv) < 2:
    print("Usage: \n\tpython mqtt_device.py <device_path>\n\neg. python mqtt_device.py /floor1/room2/ex3")
    sys.exit(-1)

DEVICE_PATH = sys.argv[1]
DEVICE_TOPIC = MUSEUM_TOPIC + DEVICE_PATH
FLASH_TOPIC = DEVICE_TOPIC + FLASH_TOPIC_PATH
HELLO_TOPIC = DEVICE_TOPIC + HELLO_TOPIC_PATH
FLASH_DETECTED_MSG = "flash"
HELLO_MSG = "hi"

TEMP_TOPIC = DEVICE_TOPIC + TEMP_TOPIC_PATH

ser = serial.Serial('/dev/ttyS0', 38400, timeout=1)
temperature = 20


def on_connect(mqttc, obj, rc):
    print("Connected. (rc = " + str(rc) + ")")
    send_hello()
    open_exhibit()


def on_message(mqttc, obj, msg):
    if msg.topic == MUSEUM_GENERAL_TOPIC or msg.topic == DEVICE_TOPIC:
        if msg.payload == SHUTDOWN_MSG:
            close_exhibit()
        elif msg.payload == OPEN_MSG:
            open_exhibit()
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


def on_publish(mqttc, obj, mid):
    print("published, mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + ", " + str(granted_qos))


def on_log(mqttc, obj, level, string):
    print(level, string)


def mqtt_thread_func(mqttc):
    mqttc.loop_forever()


def send_hello():
    mqttc.publish(HELLO_TOPIC, HELLO_MSG, 0, True)
    print("Sent hello message.")


def open_exhibit():
    # set RGB LED to green
    ser.write(chr(0b01001100))
    print("Exhibit opened.")


def close_exhibit():
    # set RGB LED to red
    ser.write(chr(0b01110000))
    print("Exhibit closed.")


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
mqttc.on_log = on_log


# Subscribe to motion/light sensor and knob
ser.write(chr(0b10000101))

# Set testament for the client
mqttc.will_set(DEVICE_TOPIC, DEVICE_TOPIC + " shutting down.", 0, True)
mqttc.connect(MQTT_BROKER_IP, MQTT_BROKER_PORT, 60)

mqttc.subscribe(MUSEUM_GENERAL_TOPIC, 0)
mqttc.subscribe(DEVICE_TOPIC, 0)

try:
    thread.start_new_thread(mqtt_thread_func, (mqttc,))
except:
    print "Error"

while True:
    cc = ser.read(1)
    if len(cc) > 0:
        cmd = int(ord(cc))
        print("cmd: " + str(cmd))
        if cmd == int(0b11000001):
            print("flash detected")
            mqttc.publish(FLASH_TOPIC, FLASH_DETECTED_MSG, 0, True)
        elif int(0b01000000) <= cmd <= int(0b01111111):
            global temperature
            cmd -= 64
            print("temperature: " + str(cmd))
            if abs(cmd - temperature) >= 2:
                mqttc.publish(TEMP_TOPIC, cmd, 0, True)
                temperature = cmd
