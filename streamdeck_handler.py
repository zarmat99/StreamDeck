import math
import sys
import time
import logging
import threading
import numpy as np
import serial
from obswebsocket import obsws, requests

ser_data = ""
mapping = {}
#logging.basicConfig(level=logging.DEBUG)
#sys.path.append('../')


def save_settings(file_path):
    global mapping
    with open(file_path, 'w') as file:
        for key, value in mapping.items():
            raw = f"{key} {value}\n"
            file.write(raw)


def read_settings(file_path):
    global mapping
    mapping = {}
    with open(file_path, 'r') as f_settings:
        for raw in f_settings:
            key, value = raw.strip().split(" ")
            mapping[key] = value
    print(mapping)


def pot_to_fader(pot_value):
    min_pot = 94
    max_pot = 1022
    min_db = -100
    max_db = 0
    base_esponential = 10  
    if pot_value <= min_pot:
        return min_db
    elif pot_value >= max_pot:
        return max_db
    db = ((math.log10(pot_value - min_pot + 1)) / (math.log10(max_pot - min_pot + 1))) * (max_db - min_db) + min_db
    return db


def connect_obs_web_socket(host="192.168.56.1", port=4455, password="ciaociao"):
    ws = obsws(host=host, port=port, password=password, legacy=0)
    try:
        ws.connect()
        res = ws.call(requests.GetVersion()).getObsVersion()
        print(f"OBS Version: {res}")
    except Exception as error:
        print(f"Error: {error}")
        exit(0)
    return ws


def open_serial_communication(com_port="COM7", baud_rate=9600):
    try:
        ser = serial.Serial(com_port, baud_rate)
        print("serial connection success!")
    except Exception as error:
        print(f"Error: {error}")
        exit(0)
    return ser


def data_from_json_response(res, obj_string):
    objs = []
    for obj in res.datain[obj_string + 's']:
        objs.append(obj[obj_string + 'Name'])
    return objs


def acquire_volume_names():
    req = requests.GetInputList()
    res = ws.call(req)
    volumes = data_from_json_response(res, "input")
    for volume in volumes:
        print(volume)
    return volumes


def acquire_scenes():
    req = requests.GetSceneList()
    res = ws.call(req)
    scenes = data_from_json_response(res, "scene")
    for scene in scenes:
        print(scene)
    return scenes


def set_input_volume(volume_name, volume_value):
    req = requests.SetInputVolume(inputName=volume_name, inputVolumeDb=int(volume_value))
    res = ws.call(req)
    print(res)


def wait_for_data():
    global ser_data
    ser_data = ""
    while ser_data == "":
        pass


def set_mode():
    global ser_data
    global mapping
    while "NormalOperation" not in ser_data:
        if ser_data in ["B0", "B1"]:
            acquire_scenes()
            mapping[ser_data] = input()
            print(f"{mapping[ser_data]} set in button {ser_data}")
            ser_data = ""
        if ser_data in ["P0", "P1", "P2"]:
            acquire_volume_names()
            mapping[ser_data] = input()
            print(f"{mapping[ser_data]} set in button {ser_data}")
            ser_data = ""
        save_settings("settings.txt")


def event_handler():
    global ser_data
    global mapping
    res = ""
    if ser_data == "SetMode":
        set_mode()
    elif ser_data == "StartRecord":
        req = requests.StartRecord()
        res = ws.call(req)
    elif ser_data == "StopRecord":
        req = requests.StopRecord()
        res = ws.call(req)
    elif ser_data == "GetStreamStatus":
        req = requests.GetRecordStatus()
        res = ws.call(req)
    elif ser_data == "StartStream":
        req = requests.StartStream()
        res = ws.call(req)
    elif ser_data == "StopStream":
        req = requests.StopStream()
        res = ws.call(req)
    elif ser_data == "ChangeScene":
        wait_for_data()
        print(f"scene name: {mapping[ser_data]}")
        req = requests.SetCurrentProgramScene(sceneName=mapping[ser_data])
        res = ws.call(req)
    elif ser_data == "SetInputVolume":
        wait_for_data()
        volume_name = mapping[ser_data]
        print(f"volume input name: {volume_name}")
        wait_for_data()
        volume_value = pot_to_fader(int(ser_data))
        print(f"volume value: {volume_value}")
        set_input_volume(volume_name, volume_value)
    ser_data = ""
    return res


def read_ser_task():
    global ser_data
    while True:
        ser_data = ser.readline().decode().strip()
        print(f"> {ser_data}")
        time.sleep(0.01)


def main_task():
    while True:
        event_handler()
        time.sleep(0.01)


if __name__ == '__main__':
    print("stream-deck 1.0 ALPHA5")
    ws = connect_obs_web_socket()
    ser = open_serial_communication()
    read_settings("settings.txt")
    threading.Thread(target=read_ser_task).start()
    threading.Thread(target=main_task).start()




