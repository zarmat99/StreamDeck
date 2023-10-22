import math
import sys
import time
import logging
import threading
import serial
from obswebsocket import obsws, requests
import scripting

ser_data = ""
recording = 0
streaming = 0
mapping = {}
script = {}
logging.basicConfig(level=logging.DEBUG)
# sys.path.append('../')


def save_settings(file_path):
    global mapping
    with open(file_path, 'w') as file:
        for key, value in mapping.items():
            raw = f"{key} {value}\n"
            file.write(raw)


def read_settings(file_path):
    mapping_dict = {}
    with open(file_path, 'r') as f_settings:
        for raw in f_settings:
            try:
                key, value = raw.strip().split(" ")
                mapping_dict[key] = value
            except:
                print("error")
    print(mapping_dict)
    return mapping_dict


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


def connect_obs_web_socket(host="172.28.48.1", port=4455, password="ciaociao"):
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
    return volumes


def acquire_scenes():
    req = requests.GetSceneList()
    res = ws.call(req)
    scenes = data_from_json_response(res, "scene")
    return scenes


def wait_for_data():
    global ser_data
    ser_data = ""
    while ser_data == "":
        pass


def get_stream_state():
    req = requests.GetStreamStatus()
    res = ws.call(req).datain['outputActive']
    return res


def get_record_state():
    req = requests.GetRecordStatus()
    res = ws.call(req).datain['outputActive']
    return res


def set_mode():
    global ser_data
    global mapping
    global scripts
    while "NormalOperation" not in ser_data:
        if ser_data in ["B0", "B1", "B2", "B3", "P0", "P1", "P2", "G0", "G1", "G2", "G3"]:
            print(f"scenes: {acquire_scenes()}")
            print(f"volumes: {acquire_volume_names()}")
            print(f"scripts: {scripts}")
            mapping[ser_data] = input()
            print(f"{mapping[ser_data]} set in button {ser_data}")
            ser_data = ""
        save_settings("settings.txt")


def event_handler():
    global ser_data
    global mapping
    global recording
    global streaming
    res = ""
    if ser_data == "SetMode":
        set_mode()
    elif ser_data == "StartRecord":
        ws.call(requests.StartRecord())
    elif ser_data == "StopRecord":
        ws.call(requests.StopRecord())
    elif ser_data == "GetStreamStatus":
        ws.call(requests.GetRecordStatus())
    elif ser_data == "StartStream":
        ws.call(requests.StartStream())
    elif ser_data == "StopStream":
        ws.call(requests.StopStream())
    elif ser_data == "ChangeScene":
        wait_for_data()
        print(f"scene name: {mapping[ser_data]}")
        ws.call(requests.SetCurrentProgramScene(sceneName=mapping[ser_data]))
    elif ser_data == "SetInputVolume":
        wait_for_data()
        volume_name = mapping[ser_data]
        print(f"volume input name: {volume_name}")
        wait_for_data()
        volume_value = pot_to_fader(int(ser_data))
        print(f"volume value: {volume_value}")
        ws.call(requests.SetInputVolume(inputName=volume_name, inputVolumeDb=int(volume_value)))
    elif ser_data in ["G0", "G1", "G2", "G3"]:
        print(f"executing {mapping[ser_data]} script...")
        scripting.execute_script(scripts[mapping[ser_data]])
        print("executed!")

    '''
    if get_record_state() and recording == 0:
        ser.write("RecordOnLed\n".encode())
        recording = 1
    elif get_record_state() is False and recording:
        ser.write("RecordOffLed\n".encode())
        recording = 0
    if get_stream_state() and streaming == 0:
        ser.write("StreamOnLed\n".encode())
        streaming = 1
    elif get_stream_state() is False and streaming:
        ser.write("StreamOffLed\n".encode())
        streaming = 0
    '''
    ser_data = ""


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


def scripting_mode():
    global scripts
    choice = ""
    ser.write("DumbMode\n".encode())
    while choice != "exit":
        choice = input("1. create script\n"
                       "2. execute script\n"
                       "3. scripts list\n"
                       "4. read scripts\n"
                       "5. save scripts\n"
                       "6. delete script\n")
        if choice == "1":
            scripts = scripting.create_script(scripts)
        elif choice == "2":
            scripting.execute_script(scripts)
        elif choice == "3":
            for key in scripts:
                print(key)
                print(scripts[key])
        elif choice == "4":
            scripts = scripting.read_script("scripts.txt")
        elif choice == "5":
            scripting.save_scripts("scripts.txt", scripts)
        elif choice == "6":
            scripts.pop(input("name: "))
    ser.write("NormalOperation\n".encode())


if __name__ == '__main__':
    print("stream-deck 1.0 ALPHA7")
    ws = connect_obs_web_socket()
    ser = open_serial_communication()
    mapping = read_settings("settings.txt")
    scripts = scripting.read_script("scripts.txt")
    print(scripts)
    # scripting_mode()
    threading.Thread(target=read_ser_task).start()
    threading.Thread(target=main_task).start()




