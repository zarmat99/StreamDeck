import sys
import time
import logging
import threading
import numpy as np
import serial
from obswebsocket import obsws, requests

ser_data = ""
logging.basicConfig(level=logging.DEBUG)
#sys.path.append('../')


def map_to_db(value, min_value, max_value, min_db, max_db):
    value = max(min(value, max_value), min_value)
    percentage = (value - min_value) / (max_value - min_value)
    db_value = min_db + percentage * (max_db - min_db)
    return db_value


def connect_obs_web_socket(host="10.239.51.41", port=4455, password="ciaociao"):
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
    while "Normal Operation" not in ser_data:
        if ser_data in ["B0", "B1"]:
            acquire_scenes()
            scene = input()
            ser.write(scene.encode())
            print(f"{scene} set in button {ser_data}")
            ser_data = ""
        if ser_data in ["P0", "P1", "P2"]:
            acquire_volume_names()
            volume = input()
            ser.write(volume.encode())
            print(f"{volume} set in button {ser_data}")
            ser_data = ""


def event_handler():
    global ser_data
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
        print(f"scene name: {ser_data}")
        req = requests.SetCurrentProgramScene(sceneName=ser_data)
        res = ws.call(req)
        print(res)
    elif ser_data == "SetInputVolume":
        wait_for_data()
        volume_name = ser_data
        print(f"volume input name: {volume_name}")
        wait_for_data()
        min_pot = 92
        max_pot = 1023
        volume_value = map_to_db(ser_data, min_pot, max_pot, -100, 0)
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

    threading.Thread(target=read_ser_task).start()
    threading.Thread(target=main_task).start()




