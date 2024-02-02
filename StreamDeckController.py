# to fix list:
# acquisire i volumi in maniera diversa e non con wasapi_output_capture
# modificare come si salva il settings, deve essere inizializzato da gui e salvato dopo ogni cambiamento
import json
import math
import sys
import time
import logging
import threading
import serial
from obswebsocket import obsws, requests
import scripting


class StreamDeckController:
    def __init__(self, obs_data={}, serial_data={}):
        self.pot_value = 0
        self.destroyer = 0
        self.script_executing = ""
        self.obs_data = obs_data
        self.serial_data = serial_data
        self.ser = None
        self.ws = None
        self.ser_data = ""
        self.mapping = {}
        self.script = {}
        # logging.basicConfig(level=logging.DEBUG)

    def start(self):
        self.ws = self.connect_obs_web_socket(self.obs_data['host'], self.obs_data['port'], self.obs_data['password'])
        self.ser = self.open_serial_communication(self.serial_data['com_port'], self.serial_data['baud_rate'])
        self.mapping = self.load_settings()
        self.script = scripting.load_scripts()

        threading.Thread(target=self.read_ser_task).start()
        threading.Thread(target=self.main_task).start()

    def save_settings(self):
        with open('mapping.json', 'w') as file:
            json.dump(self.mapping, file)

    def load_settings(self):
        mapping_dict = {}
        try:
            with open("mapping.json", 'r') as file:
                mapping_dict = json.load(file)
        except FileNotFoundError:
            print(FileNotFoundError)

        return mapping_dict

    def pot_to_fader(self, pot_value):
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
        return pot_value, db

    def connect_obs_web_socket(self, host="192.168.0.57", port=4455, password="ciaociao"):
        ws = obsws(host=host, port=port, password=password, legacy=0)
        try:
            ws.connect()
            res = ws.call(requests.GetVersion()).getObsVersion()
            print(f"OBS Version: {res}")
        except Exception as error:
            print(f"Error: {error}")
            exit(0)
        return ws

    def open_serial_communication(self, com_port="COM7", baud_rate=9600):
        try:
            ser = serial.Serial(com_port, baud_rate)
            print("serial connection success!")
        except Exception as error:
            print(f"Error: {error}")
            exit(0)
        return ser

    def data_from_json_response(self, res, obj_string):
        objs = []
        for obj in res.datain[obj_string + 's']:
            objs.append(obj[obj_string + 'Name'])
        return objs

    def wait_for_data(self):
        self.ser_data = ""
        while self.ser_data == "":
            pass

    def get_volume(self, volume_name):
        req = requests.GetInputVolume(inputName=volume_name)
        res = self.ws.call(req).datain['inputVolumeMul']
        return res

    def get_volume_names(self):
        req = requests.GetInputList()
        res = self.ws.call(req)
        volumes = self.data_from_json_response(res, "input")
        return volumes

    def get_volumes_names(self):
        inputs = []
        accepted_inputs = ['wasapi_output_capture', 'wasapi_input_capture']
        req = requests.GetInputList()
        res = self.ws.call(req)
        input_list = res.datain['inputs']
        for input_dict in input_list:
            for accepted_input in accepted_inputs:
                if accepted_input in input_dict.values():
                    inputs.append(input_dict['inputName'])
        return inputs

    def get_scene_names(self):
        req = requests.GetSceneList()
        res = self.ws.call(req)
        scenes = self.data_from_json_response(res, "scene")
        return scenes

    def get_current_scene(self):
        req = requests.GetCurrentProgramScene()
        res = self.ws.call(req).datain['currentProgramSceneName']
        return res

    def get_stream_state(self):
        req = requests.GetStreamStatus()
        res = self.ws.call(req).datain['outputActive']
        return res

    def get_record_state(self):
        req = requests.GetRecordStatus()
        res = self.ws.call(req).datain['outputActive']
        return res

    def set_mode(self):
        while "NormalOperation" not in self.ser_data:
            if self.ser_data in ["B0", "B1", "B2", "B3", "P0", "P1", "P2", "G0", "G1", "G2", "G3"]:
                print(f"scenes: {self.get_scene_names()}")
                print(f"volumes: {self.get_volume_names()}")
                print(f"scripts: {self.script}")
                self.mapping[self.ser_data] = input()
                print(f"{self.mapping[self.ser_data]} set in button {self.ser_data}")
                self.ser_data = ""
            self.save_settings()

    def destroy(self):
        self.destroyer = 1

    def event_handler(self):
        res = ""
        if self.ser_data == "SetMode":
            self.set_mode()
        elif self.ser_data == "StartRecord":
            self.ws.call(requests.StartRecord())
        elif self.ser_data == "StopRecord":
            self.ws.call(requests.StopRecord())
        elif self.ser_data == "GetStreamStatus":
            self.ws.call(requests.GetRecordStatus())
        elif self.ser_data == "StartStream":
            self.ws.call(requests.StartStream())
        elif self.ser_data == "StopStream":
            self.ws.call(requests.StopStream())
        elif self.ser_data == "ChangeScene":
            self.wait_for_data()
            print(f"scene name: {self.mapping[self.ser_data]}")
            self.ws.call(requests.SetCurrentProgramScene(sceneName=self.mapping[self.ser_data]))
        elif self.ser_data == "SetInputVolume":
            self.wait_for_data()
            volume_name = self.mapping[self.ser_data]
            print(f"volume input name: {volume_name}")
            self.wait_for_data()
            volume_value, self.pot_value = self.pot_to_fader(int(self.ser_data))
            print(f"volume value: {volume_value}")
            print(f"pot value: {self.pot_value}")
            self.ws.call(requests.SetInputVolume(inputName=volume_name, inputVolumeDb=int(volume_value)))
        elif self.ser_data == "ExecuteScript":
            self.wait_for_data()
            script_name = self.mapping[self.ser_data]
            print(f"executing {script_name} script...")
            self.script_executing = self.ser_data
            scripting.execute_script(self.script[self.mapping[self.ser_data]])
            self.script_executing = ""
            print("executed!")

        self.ser_data = ""

    def read_ser_task(self):
        while not self.destroyer:
            try:
                self.ser_data = self.ser.readline().decode().strip()
                print(f"> {self.ser_data}")
                time.sleep(0.01)
            except:
                print("error reading serial!")
                self.destroyer = 1

    def main_task(self):
        while not self.destroyer:
            self.event_handler()
            time.sleep(0.01)
