#!/usr/bin/python

import mosquitto
import thread
# import serial
import json
import gspread

from config import *
from oauth2client.client import SignedJwtAssertionCredentials

# ser = serial.Serial('/dev/ttyS0', 38400, timeout=1)
# museum_open = False
photo_counts = {}
temperatures = {}
open_devices = {}

rows = {}
current_row = 3

json_key = json.load(open('iot-first-fifth-cbc92bb37a1f.json'))
scope = ['https://spreadsheets.google.com/feeds']

credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'].encode(), scope)
gc = gspread.authorize(credentials)
spreadsheet = gc.open("mot").sheet1


def on_connect(mqttc, obj, rc):
    print("Connected. (rc = " + str(rc) + ")")


def on_message(mqttc, obj, msg):
    global spreadsheet
    device_path = msg.topic[:msg.topic.rfind("/")]

    if msg.topic.endswith(FLASH_TOPIC_PATH):
        if device_path in photo_counts.keys():
            photo_counts[device_path] += 1
        else:
            photo_counts[device_path] = 1

        spreadsheet.update_cell(rows[device_path], 3, photo_counts[device_path])

        if photo_counts[device_path] > MAX_PHOTOS:
            close_device(device_path)

    elif msg.topic.endswith(TEMP_TOPIC_PATH):
        temperatures[device_path] = int(msg.payload)
        if int(msg.payload) > MAX_TEMP and open_devices[device_path] == True:
            close_device(device_path)
        elif int(msg.payload) < MAX_TEMP and open_devices[device_path] == False:
            open_device(device_path)
        spreadsheet.update_cell(rows[device_path], 4, temperatures[device_path])

    elif msg.topic.endswith(HELLO_TOPIC_PATH):
        init_device(device_path)

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


# # todo: subscribe to needed things
# # Subscribe to Button 1 - on/off switch
# ser.write(chr(0b10010000))

# Set testament for the client
mqttc.will_set(MUSEUM_GENERAL_TOPIC, SHUTDOWN_MSG, 0, True)
mqttc.connect(MQTT_BROKER_IP, MQTT_BROKER_PORT, 60)

mqttc.subscribe(MUSEUM_TOPIC + "/#", 0)

try:
    thread.start_new_thread(mqtt_thread_func, (mqttc,))
except:
    print "Error"


def init_device(path):
    open_devices[path] = True
    global current_row
    rows[path] = current_row
    current_row += 1
    global spreadsheet
    spreadsheet.update_cell(current_row, 2, path)
    spreadsheet.update_cell(current_row, 3, 0)
    spreadsheet.update_cell(current_row, 4, 20)
    spreadsheet.update_cell(current_row, 5, "tak")


def open_device(path):
    mqttc.publish(path, OPEN_MSG, 0, True)
    open_devices[path] = True
    global spreadsheet
    spreadsheet.update_cell(rows[path], 5, "tak")


def close_device(path):
    mqttc.publish(path, SHUTDOWN_MSG, 0, True)
    open_devices[path] = False
    global spreadsheet
    spreadsheet.update_cell(rows[path], 5, "nie")


def open_museum():
    # mqttc.publish(MUSEUM_GENERAL_TOPIC, OPEN_MSG, 0, True)
    for device in open_devices.keys():
        open_device(device)


def close_museum():
    # mqttc.publish(MUSEUM_GENERAL_TOPIC, SHUTDOWN_MSG, 0, True)
    for device in open_devices.keys():
        close_device(device)


while True:
    input_cmd = raw_input(">> ")
    if input_cmd == "open":
        open_museum()
    elif input_cmd == "close":
        close_museum()
