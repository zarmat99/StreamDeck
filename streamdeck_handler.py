import sys
import time
import logging
import threading
import serial
from obswebsocket import obsws, requests

ser_data = ""
logging.basicConfig(level=logging.DEBUG)
sys.path.append('../')


# function that open the connection with obste web socket in order to send
# requests and receive response
def ConnectObsWebSocket(host="10.239.51.83", port=4455, password="ciaociao"):
    ws = obsws(host=host, port=port, password=password, legacy=0)
    try:
        ws.connect()
        res = ws.call(requests.GetVersion()).getObsVersion()
        print(f"OBS Version: {res}")
    except Exception as error:
        print(f"Error: {error}")
        exit(0)
    return ws


# function that open serial communication with the micro in order
# to receive signals from the device
def OpenSerialCommunication(com_port="COM7", baud_rate=9600):
    try:
        ser = serial.Serial(com_port, baud_rate)
        print("serial connection success!")
    except Exception as error:
        print(f"Error: {error}")
        exit(0)
    return ser


def acquire_scenes(ws):
    # list of scenes
    scenes = []
    req = requests.GetSceneList()
    res = ws.call(req)
    for scene in res.datain['scenes']:
        scenes.append(scene['sceneName'])
    return scenes


def change_scene(scenes, scene_name):
    req = requests.SetCurrentProgramScene(sceneName=scene_name)
    res = ws.call(req)
    print(res)


# function that checks the signal arriving from the device and performs
# the corresponding action
def event_handler():
    global ser_data
    res = ""
    if ser_data == "SetMode":
        while "Normal Operation" not in ser_data:
            if "selected" in ser_data:
                ser.write(input().encode())
                time.sleep(3)
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
        while ser_data == "ChangeScene":
            pass
        print(f"scene name: {ser_data}")
        change_scene(scenes, ser_data)
    ser_data = ""
    return res


def read_ser_task():
    global ser_data
    while True:
        ser_data = ser.readline().decode().strip()
        print(f"> {ser_data}")
        time.sleep(0.1)


def main_task():
    while True:
        event_handler()
        time.sleep(0.1)


if __name__ == '__main__':
    print("stream-deck 1.0 ALPHA2")
    ws = ConnectObsWebSocket()
    ser = OpenSerialCommunication()

    scenes = acquire_scenes(ws)

    threading.Thread(target=read_ser_task).start()
    threading.Thread(target=main_task).start()




