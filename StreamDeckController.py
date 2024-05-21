# to fix list:
# - acquisire i volumi in maniera diversa e non con wasapi_output_capture
# - al posto di utilizzare self.run per gestire l'esecuzione dei thread posso uccidere il thread quando non sono nella online page
#   e ogni volta che ritorno nella online page chiamo la sdc.start()
import math
import time
import threading
import serial
from obswebsocket import obsws, requests
import scripting


class StreamDeckController:
    def __init__(self, app):
        self.app = app
        self.pot_value = 0
        self.destroyer = 0
        self.script_executing = ""
        self.ser_data = ""
        self.ser = None
        self.ws = None
        self.run = False
        # logging.basicConfig(level=logging.DEBUG)

    def start(self):
        if self.ser is not None and self.ws is not None:
            if not self.run:
                threading.Thread(target=self.read_ser_task, daemon=True).start()
                threading.Thread(target=self.main_task, daemon=True).start()
                self.run = True
            return True
        else:
            return False

    def connect_obs_web_socket(self):
        host = self.app.settings.settings['connection']['obs_data']['host']
        port = self.app.settings.settings['connection']['obs_data']['port']
        password = self.app.settings.settings['connection']['obs_data']['password']
        self.ws = obsws(host=host, port=port, password=password, timeout=2, legacy=0)
        try:
            self.ws.connect()
            self.ws.call(requests.GetVersion()).getObsVersion()
            return True
        except BaseException:
            self.ws = None
            return False


    def open_serial_communication(self):
        com_port = self.app.settings.settings['connection']['serial_data']['com_port']
        baud_rate = self.app.settings.settings['connection']['serial_data']['baud_rate']
        try:
            self.ser = serial.Serial(com_port, baud_rate, timeout=2)
            return True
        except Exception:
            self.ser = None
            return False

    def pot_to_fader(self, pot_value):
        min_pot = 94
        max_pot = 1022
        min_db = -100
        max_db = 0
        base_esponential = 10
        if pot_value <= min_pot:
            return min_pot, min_db
        elif pot_value >= max_pot:
            return max_pot, max_db
        db = ((math.log10(pot_value - min_pot + 1)) / (math.log10(max_pot - min_pot + 1))) * (max_db - min_db) + min_db
        return pot_value, db

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

    def get_volume(self, volume_name):
        req = requests.GetInputVolume(inputName=volume_name)
        res = self.ws.call(req).datain['inputVolumeMul']
        return res

    def get_scene_names(self):
        scenes = []
        req = requests.GetSceneList()
        res = self.ws.call(req)
        scene_list = res.datain['scenes']
        for scene in scene_list:
            scenes.append(scene["sceneName"])
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

    def destroy(self):
        self.destroyer = 1

    def read_ser_task(self):
        while not self.destroyer:
            try:
                self.ser_data = self.ser.readline().decode().strip()
                print(f"> {self.ser_data}")
                time.sleep(0.01)
            except Exception as e:
                print(f"Error: {e}")
                self.destroyer = 1

    def event_handler(self):
        if self.ser_data == "StartRecord":
            self.ws.call(requests.StartRecord())
        elif self.ser_data == "StopRecord" in self.ser_data:
            self.ws.call(requests.StopRecord())
        elif self.ser_data == "GetStreamStatus":
            self.ws.call(requests.GetRecordStatus())
        elif self.ser_data == "StartStream":
            self.ws.call(requests.StartStream())
        elif self.ser_data == "StopStream":
            self.ws.call(requests.StopStream())
        elif "ChangeScene" in self.ser_data:
            pin = self.ser_data.split()[1]
            scene_name = self.app.settings.settings['mapping'][pin]
            print(self.ser_data)
            self.ws.call(requests.SetCurrentProgramScene(sceneName=scene_name))
        elif "SetInputVolume" in self.ser_data:
            pin = self.ser_data.split()[1]
            volume_ser = self.ser_data.split()[2]
            volume_name = self.app.settings.settings['mapping'][pin]
            volume_value, self.pot_value = self.pot_to_fader(int(volume_ser))
            print(f"{self.ser_data}:{self.pot_value} dB")
            self.ws.call(requests.SetInputVolume(inputName=volume_name, inputVolumeDb=int(self.pot_value)))
        elif "ExecuteScript" in self.ser_data:
            pin = self.ser_data.split()[1]
            script_name = self.app.settings.settings['mapping'][pin]
            self.script_executing = pin
            scripting.execute_script(self.app.settings.settings['script'][script_name])
            self.script_executing = ""

        self.ser_data = ""

    def main_task(self):
        time.sleep(3)
        while not self.destroyer:
            self.event_handler()
            time.sleep(0.01)
