import threading
import time
import PotentiometerWidget
import logging
from logging.handlers import RotatingFileHandler
import tkinter as tk
import customtkinter
import json
import StreamDeckController_New


class Logger:
    def __init__(self, levels=[], filename=None, console=False):
        self.accepted_levels = ['debug', 'info', 'warning', 'error', 'critical']
        self.levels = levels
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] > %(message)s')

        for level in self.levels:
            if level not in self.accepted_levels:
                raise ValueError(f'logging level {level} not valid. Please, select an accepted logging level: {self.accepted_levels}')

        if filename:
            file_path = 'logs/' + filename
            file_handler = RotatingFileHandler(file_path, maxBytes=10*1024*1024, backupCount=5)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        if console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def debug(self, message):
        if 'debug' in self.levels:
            self.logger.debug(message)

    def info(self, message):
        if 'info' in self.levels:
            self.logger.info(message)

    def warning(self, message):
        if 'warning' in self.levels:
            self.logger.warning(message)

    def error(self, message):
        if 'error' in self.levels:
            self.logger.error(message)

    def critical(self, message):
        if 'critical' in self.levels:
            self.logger.critical(message)


class BasePage(customtkinter.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.frames = {}
        self.labels = {}
        self.entries = {}
        self.buttons = {}
        self.canvas = {}
        self.comboboxes = {}
        self.scrollable = {}

    def change_window_name(self):
        self.parent.title("Streamdeck - BasePage")

    def show(self):
        self.grid(row=0, column=0, sticky="nsew")
        self.change_window_name()
        # self.tkraise()

    def hide(self):
        self.grid_forget()

    def create_page(self):
        self.create_frames()
        self.configure_frames()
        self.create_widgets()
        self.configure_widgets()
        self.grid_widgets()
        self.grid_frames()

    def create_frames(self):
        self.frames["title"] = customtkinter.CTkFrame(self, fg_color="gray25")
        self.frames["body"] = customtkinter.CTkFrame(self, corner_radius=0)
        self.frames["bottom"] = customtkinter.CTkFrame(self, fg_color="gray20", corner_radius=0)

    def configure_frames(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=4)
        self.grid_rowconfigure(1, weight=10)
        self.grid_rowconfigure(2, weight=1)

    def grid_frames(self):
        self.frames["title"].grid(row=0, column=0, sticky="nswe", padx=20, pady=(20, 5))
        self.frames["body"].grid(row=1, column=0, sticky="nswe", padx=20, pady=(5, 0))
        self.frames["bottom"].grid(row=2, column=0, sticky="nswe", padx=20, pady=(0, 20))

    def create_widgets(self):
        pass

    def configure_widgets(self):
        pass

    def grid_widgets(self):
        pass


class ConnectionPage(BasePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.vars = {
            'obs_data': {
                'host': None,
                'port': None,
                'password': None
            },
            'serial_data': {
                'com_port': None,
                'baud_rate': None
            }
        }
        self.create_page()

    def change_window_name(self):
        self.parent.title("Streamdeck - Connection")

    def create_widgets(self):
        # title_frame
        self.labels["Connection Page"] = customtkinter.CTkLabel(self.frames["title"], text="Connection Page", font=customtkinter.CTkFont(size=25, weight="bold"))
        # body_frame
        self.labels["obs_configuration"] = customtkinter.CTkLabel(self.frames["body"], text="OBS Configurations", font=customtkinter.CTkFont(size=20))
        self.labels["host"] = customtkinter.CTkLabel(self.frames["body"], text="Host", font=customtkinter.CTkFont(size=15))
        self.entries["host"] = customtkinter.CTkEntry(self.frames["body"], textvariable=self.vars["obs_data"]["host"])
        self.labels["port"] = customtkinter.CTkLabel(self.frames["body"], text="Port", font=customtkinter.CTkFont(size=15))
        self.entries["port"] = customtkinter.CTkEntry(self.frames["body"], textvariable=self.vars["obs_data"]["port"])
        self.labels["password"] = customtkinter.CTkLabel(self.frames["body"], text="Password", font=customtkinter.CTkFont(size=15))
        self.entries["password"] = customtkinter.CTkEntry(self.frames["body"], textvariable=self.vars["obs_data"]["password"])
        # streamdeck_conf_frame
        self.labels["streamdeck_conf"] = customtkinter.CTkLabel(self.frames["body"], text="StreamDeck Configurations", font=customtkinter.CTkFont(size=20))
        self.labels["com_port"] = customtkinter.CTkLabel(self.frames["body"], text="Com Port", font=customtkinter.CTkFont(size=15))
        self.entries["com_port"] = customtkinter.CTkEntry(self.frames["body"], textvariable=self.vars["serial_data"]["com_port"])
        self.labels["baud_rate"] = customtkinter.CTkLabel(self.frames["body"], text="Baud Rate", font=customtkinter.CTkFont(size=15))
        self.entries["baud_rate"] = customtkinter.CTkEntry(self.frames["body"], textvariable=self.vars["serial_data"]["baud_rate"])
        # bottom_frame
        self.buttons["connect"] = customtkinter.CTkButton(self.frames["bottom"], text="Connect", command=lambda: self.parent.show_page(self.parent.pages['online']))

    def configure_widgets(self):
        # connection_page_title_frame
        self.frames["title"].grid_rowconfigure(0, weight=1)
        self.frames["title"].grid_columnconfigure(0, weight=1)
        # body_frame
        self.frames["body"].grid_rowconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)
        self.frames["body"].grid_columnconfigure((0, 1), weight=1)
        # connection_page_bottom_frame
        self.frames["bottom"].grid_rowconfigure(0, weight=1)
        self.frames["bottom"].grid_columnconfigure(0, weight=1)

    def grid_widgets(self):
        # connection_page_title_frame
        self.labels["Connection Page"].grid(row=0, column=0)
        # body_frame
        self.labels["obs_configuration"].grid(row=0, column=0, columnspan=2)
        self.labels["host"].grid(row=1, column=0)
        self.entries["host"].grid(row=1, column=1)
        self.labels["port"].grid(row=2, column=0)
        self.entries["port"].grid(row=2, column=1)
        self.labels["password"].grid(row=3, column=0)
        self.entries["password"].grid(row=3, column=1)
        self.labels["streamdeck_conf"].grid(row=4, column=0, columnspan=2)
        self.labels["com_port"].grid(row=5, column=0)
        self.entries["com_port"].grid(row=5, column=1)
        self.labels["baud_rate"].grid(row=6, column=0)
        self.entries["baud_rate"].grid(row=6, column=1)
        # connection_page_bottom_frame
        self.buttons["connect"].grid(row=0, column=0, padx=(0, 20), sticky="e", pady=(0, 10))


class OnlinePage(BasePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_page()

    def change_window_name(self):
        self.parent.title("Streamdeck - Online")

    def create_widgets(self):
        # title_frame
        self.labels["online_page"] = customtkinter.CTkLabel(self.frames["title"], text="Online Page", font=customtkinter.CTkFont(size=25, weight="bold"))
        # body_frame
        self.labels["record_state"] = customtkinter.CTkLabel(self.frames["body"], text="Record State", font=customtkinter.CTkFont(size=15))
        self.canvas["record_state"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="red")
        self.labels["stream_state"] = customtkinter.CTkLabel(self.frames["body"], text="Stream State", font=customtkinter.CTkFont(size=15))
        self.canvas["stream_state"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="red")
        self.entries["sd_state"] = customtkinter.CTkLabel(self.frames["body"], text="State: Offline", font=customtkinter.CTkFont(size=15))
        self.labels["scene_0"] = customtkinter.CTkLabel(self.frames["body"], text="Scene 0", font=customtkinter.CTkFont(size=15))
        self.canvas["scene_0"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.labels["scene_1"] = customtkinter.CTkLabel(self.frames["body"], text="Scene 1", font=customtkinter.CTkFont(size=15))
        self.canvas["scene_1"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.labels["scene_2"] = customtkinter.CTkLabel(self.frames["body"], text="Scene 2", font=customtkinter.CTkFont(size=15))
        self.canvas["scene_2"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.labels["scene_3"] = customtkinter.CTkLabel(self.frames["body"], text="Scene 3", font=customtkinter.CTkFont(size=15))
        self.canvas["scene_3"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.labels["script_0"] = customtkinter.CTkLabel(self.frames["body"], text="Script 0", font=customtkinter.CTkFont(size=15))
        self.canvas["script_0"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.labels["script_1"] = customtkinter.CTkLabel(self.frames["body"], text="Script 1", font=customtkinter.CTkFont(size=15))
        self.canvas["script_1"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.labels["script_2"] = customtkinter.CTkLabel(self.frames["body"], text="Script 2", font=customtkinter.CTkFont(size=15))
        self.canvas["script_2"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.labels["script_3"] = customtkinter.CTkLabel(self.frames["body"], text="Script 3", font=customtkinter.CTkFont(size=15))
        self.canvas["script_3"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.labels["volume_0"] = customtkinter.CTkLabel(self.frames["body"], text="Volume 0", font=customtkinter.CTkFont(size=15))
        self.canvas["volume_0"] = PotentiometerWidget.PotentiometerWidget(self.frames["body"], color="gray20", radius=40)
        self.labels["volume_1"] = customtkinter.CTkLabel(self.frames["body"], text="Volume 1", font=customtkinter.CTkFont(size=15))
        self.canvas["volume_1"] = PotentiometerWidget.PotentiometerWidget(self.frames["body"], color="gray20", radius=40)
        self.labels["volume_2"] = customtkinter.CTkLabel(self.frames["body"], text="Volume 2", font=customtkinter.CTkFont(size=15))
        self.canvas["volume_2"] = PotentiometerWidget.PotentiometerWidget(self.frames["body"], color="gray20", radius=40)
        self.labels["volume_3"] = customtkinter.CTkLabel(self.frames["body"], text="Volume 3", font=customtkinter.CTkFont(size=15))
        self.canvas["volume_3"] = PotentiometerWidget.PotentiometerWidget(self.frames["body"], color="gray20", radius=40)
        # online_page_bottom_frame
        self.buttons["connection_page"] = customtkinter.CTkButton(self.frames["bottom"], text="Connection Page", command=lambda: self.parent.show_page(self.parent.pages['connection']))
        self.buttons["mapping_page"] = customtkinter.CTkButton(self.frames["bottom"], text="Mapping Page", command=lambda: self.parent.show_page(self.parent.pages['mapping']))
        self.buttons["script_page"] = customtkinter.CTkButton(self.frames["bottom"], text="Script Page", command=lambda: self.parent.show_page(self.parent.pages['script']))

    def configure_widgets(self):
        # title_frame
        self.frames["title"].grid_rowconfigure(0, weight=1)
        self.frames["title"].grid_columnconfigure(0, weight=1)
        self.frames["body"].grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.frames["body"].grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        self.frames["bottom"].grid_rowconfigure(0, weight=1)
        self.frames["bottom"].grid_columnconfigure((0, 1, 2), weight=1)

    def grid_widgets(self):
        # title_frame
        self.labels["online_page"].grid(row=0, column=0)
        # body_frame
        self.labels["record_state"].grid(row=0, column=0, columnspan=4, sticky="s")
        self.labels["stream_state"].grid(row=0, column=4, columnspan=4, sticky="s")
        self.canvas["record_state"].grid(row=1, column=0, columnspan=4)
        self.canvas["stream_state"].grid(row=1, column=4, columnspan=4)
        self.entries["sd_state"].grid(row=1, column=0, columnspan=8)
        self.labels["scene_0"].grid(row=2, column=0, sticky="s")
        self.labels["scene_1"].grid(row=2, column=1, sticky="s")
        self.labels["scene_2"].grid(row=2, column=2, sticky="s")
        self.labels["scene_3"].grid(row=2, column=3, sticky="s")
        self.labels["script_0"].grid(row=2, column=4, sticky="s")
        self.labels["script_1"].grid(row=2, column=5, sticky="s")
        self.labels["script_2"].grid(row=2, column=6, sticky="s")
        self.labels["script_3"].grid(row=2, column=7, sticky="s")
        self.canvas["scene_0"].grid(row=3, column=0)
        self.canvas["scene_1"].grid(row=3, column=1)
        self.canvas["scene_2"].grid(row=3, column=2)
        self.canvas["scene_3"].grid(row=3, column=3)
        self.canvas["script_0"].grid(row=3, column=4)
        self.canvas["script_1"].grid(row=3, column=5)
        self.canvas["script_2"].grid(row=3, column=6)
        self.canvas["script_3"].grid(row=3, column=7)
        self.labels["volume_0"].grid(row=4, column=2, sticky="s")
        self.labels["volume_1"].grid(row=4, column=3, sticky="s")
        self.labels["volume_2"].grid(row=4, column=4, sticky="s")
        self.labels["volume_3"].grid(row=4, column=5, sticky="s")
        self.canvas["volume_0"].grid(row=5, column=2)
        self.canvas["volume_1"].grid(row=5, column=3)
        self.canvas["volume_2"].grid(row=5, column=4)
        self.canvas["volume_3"].grid(row=5, column=5)
        # bottom_frame
        self.buttons["connection_page"].grid(row=0, column=0, sticky="w", padx=(20, 0), pady=(0, 10))
        self.buttons["mapping_page"].grid(row=0, column=0, columnspan=3, sticky="e", padx=(0, 165), pady=(0, 10))
        self.buttons["script_page"].grid(row=0, column=0, columnspan=3, sticky="e", padx=(0, 20), pady=(0, 10))


class MappingPage(BasePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_page()

    def change_window_name(self):
        self.parent.title("Streamdeck - Mapping")

    def create_widgets(self):
        # title_frame
        self.labels["online_page"] = customtkinter.CTkLabel(self.frames["title"], text="Mapping Page", font=customtkinter.CTkFont(size=25, weight="bold"))
        # body_frame
        self.labels["record_state"] = customtkinter.CTkLabel(self.frames["body"], text="Record State", font=customtkinter.CTkFont(size=15))
        self.canvas["record_state"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="red")
        self.labels["stream_state"] = customtkinter.CTkLabel(self.frames["body"], text="Stream State", font=customtkinter.CTkFont(size=15))
        self.canvas["stream_state"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="red")
        self.comboboxes["scene_0"] = customtkinter.CTkComboBox(self.frames["body"], values=[""], font=customtkinter.CTkFont(size=15))
        self.canvas["scene_0"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.comboboxes["scene_1"] = customtkinter.CTkComboBox(self.frames["body"], values=[""], font=customtkinter.CTkFont(size=15))
        self.canvas["scene_1"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.comboboxes["scene_2"] = customtkinter.CTkComboBox(self.frames["body"], values=[""], font=customtkinter.CTkFont(size=15))
        self.canvas["scene_2"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.comboboxes["scene_3"] = customtkinter.CTkComboBox(self.frames["body"], values=[""], font=customtkinter.CTkFont(size=15))
        self.canvas["scene_3"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.comboboxes["script_0"] = customtkinter.CTkComboBox(self.frames["body"], values=[""], font=customtkinter.CTkFont(size=15))
        self.canvas["script_0"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.comboboxes["script_1"] = customtkinter.CTkComboBox(self.frames["body"], values=[""], font=customtkinter.CTkFont(size=15))
        self.canvas["script_1"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.comboboxes["script_2"] = customtkinter.CTkComboBox(self.frames["body"], values=[""], font=customtkinter.CTkFont(size=15))
        self.canvas["script_2"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.comboboxes["script_3"] = customtkinter.CTkComboBox(self.frames["body"], values=[""], font=customtkinter.CTkFont(size=15))
        self.canvas["script_3"] = tk.Canvas(self.frames["body"], width=70, height=70, bg="grey")
        self.comboboxes["volume_0"] = customtkinter.CTkComboBox(self.frames["body"], values=[""], font=customtkinter.CTkFont(size=15))
        self.canvas["volume_0"] = PotentiometerWidget.PotentiometerWidget(self.frames["body"], color="gray20", radius=40)
        self.comboboxes["volume_1"] = customtkinter.CTkComboBox(self.frames["body"], values=[""], font=customtkinter.CTkFont(size=15))
        self.canvas["volume_1"] = PotentiometerWidget.PotentiometerWidget(self.frames["body"], color="gray20", radius=40)
        self.comboboxes["volume_2"] = customtkinter.CTkComboBox(self.frames["body"], values=[""], font=customtkinter.CTkFont(size=15))
        self.canvas["volume_2"] = PotentiometerWidget.PotentiometerWidget(self.frames["body"], color="gray20", radius=40)
        self.comboboxes["volume_3"] = customtkinter.CTkComboBox(self.frames["body"], values=[""], font=customtkinter.CTkFont(size=15))
        self.canvas["volume_3"] = PotentiometerWidget.PotentiometerWidget(self.frames["body"], color="gray20", radius=40)
        # online_page_bottom_frame
        self.buttons["save"] = customtkinter.CTkButton(self.frames["bottom"], text="Save", command=lambda: self.parent.show_page(self.parent.pages['online']))

    def configure_widgets(self):
        # title_frame
        self.frames["title"].grid_rowconfigure(0, weight=1)
        self.frames["title"].grid_columnconfigure(0, weight=1)
        self.frames["body"].grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.frames["body"].grid_columnconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)
        self.frames["bottom"].grid_rowconfigure(0, weight=1)
        self.frames["bottom"].grid_columnconfigure(0, weight=1)

    def grid_widgets(self):
        # title_frame
        self.labels["online_page"].grid(row=0, column=0)
        # body_frame
        self.labels["record_state"].grid(row=0, column=0, columnspan=4, sticky="s")
        self.labels["stream_state"].grid(row=0, column=4, columnspan=4, sticky="s")
        self.canvas["record_state"].grid(row=1, column=0, columnspan=4)
        self.canvas["stream_state"].grid(row=1, column=4, columnspan=4)
        self.comboboxes["scene_0"].grid(row=2, column=0, sticky="s")
        self.comboboxes["scene_1"].grid(row=2, column=1, sticky="s")
        self.comboboxes["scene_2"].grid(row=2, column=2, sticky="s")
        self.comboboxes["scene_3"].grid(row=2, column=3, sticky="s")
        self.comboboxes["script_0"].grid(row=2, column=4, sticky="s")
        self.comboboxes["script_1"].grid(row=2, column=5, sticky="s")
        self.comboboxes["script_2"].grid(row=2, column=6, sticky="s")
        self.comboboxes["script_3"].grid(row=2, column=7, sticky="s")
        self.canvas["scene_0"].grid(row=3, column=0)
        self.canvas["scene_1"].grid(row=3, column=1)
        self.canvas["scene_2"].grid(row=3, column=2)
        self.canvas["scene_3"].grid(row=3, column=3)
        self.canvas["script_0"].grid(row=3, column=4)
        self.canvas["script_1"].grid(row=3, column=5)
        self.canvas["script_2"].grid(row=3, column=6)
        self.canvas["script_3"].grid(row=3, column=7)
        self.comboboxes["volume_0"].grid(row=4, column=2, sticky="s")
        self.comboboxes["volume_1"].grid(row=4, column=3, sticky="s")
        self.comboboxes["volume_2"].grid(row=4, column=4, sticky="s")
        self.comboboxes["volume_3"].grid(row=4, column=5, sticky="s")
        self.canvas["volume_0"].grid(row=5, column=2)
        self.canvas["volume_1"].grid(row=5, column=3)
        self.canvas["volume_2"].grid(row=5, column=4)
        self.canvas["volume_3"].grid(row=5, column=5)
        # bottom_frame
        self.buttons["save"].grid(row=0, column=0, sticky="e", padx=(0, 20), pady=(0, 10))


class ScriptPage(BasePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_page()

    def change_window_name(self):
        self.parent.title("Streamdeck - Script")

    def create_widgets(self):
        # title_frame
        self.labels["script_page"] = customtkinter.CTkLabel(self.frames["title"], text="Script Page", font=customtkinter.CTkFont(size=25, weight="bold"))
        # body_frame
        self.comboboxes["script_list"] = customtkinter.CTkComboBox(self.frames["body"], values=[""], width=200)
        self.entries["script_name"] = customtkinter.CTkEntry(self.frames["body"], width=200)
        self.scrollable["steps_container"] = customtkinter.CTkScrollableFrame(self.frames["body"])
        self.buttons["add_step"] = customtkinter.CTkButton(self.frames["body"], text="Add Step")
        self.buttons["delete_step"] = customtkinter.CTkButton(self.frames["body"], text="Delete Step")
        self.buttons["save_script"] = customtkinter.CTkButton(self.frames["body"], text="Save Script")
        self.buttons["delete_script"] = customtkinter.CTkButton(self.frames["body"], text="Delete Script")
        self.buttons["clear_script"] = customtkinter.CTkButton(self.frames["body"], text="Clear Script")
        # online_page_bottom_frame
        self.buttons["online_page"] = customtkinter.CTkButton(self.frames["bottom"], text="Online Page", command=lambda: self.parent.show_page(self.parent.pages['online']))

    def configure_widgets(self):
        # title_frame
        self.frames["title"].grid_rowconfigure(0, weight=1)
        self.frames["title"].grid_columnconfigure(0, weight=1)
        self.frames["body"].grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.frames["body"].grid_columnconfigure(0, weight=4)
        self.frames["body"].grid_columnconfigure(1, weight=1)
        self.frames["bottom"].grid_rowconfigure(0, weight=1)
        self.frames["bottom"].grid_columnconfigure(0, weight=1)

    def grid_widgets(self):
        # title_frame
        self.labels["script_page"].grid(row=0, column=0)
        # body_frame
        self.comboboxes["script_list"].grid(row=0, column=0, sticky="w", padx=(40, 0), pady=(20, 10))
        self.entries["script_name"].grid(row=0, column=0, sticky="e", padx=(0, 20), pady=(20, 10))
        self.scrollable["steps_container"].grid(row=1, column=0, rowspan=5, padx=(20, 0), pady=(10, 20), sticky="nsew")
        self.buttons["add_step"].grid(row=1, column=1)
        self.buttons["delete_step"].grid(row=2, column=1)
        self.buttons["save_script"].grid(row=3, column=1)
        self.buttons["delete_script"].grid(row=4, column=1)
        self.buttons["clear_script"].grid(row=5, column=1)
        # online_page_bottom_frame
        self.buttons["online_page"].grid(row=0, column=0, sticky="w", padx=(20, 0), pady=(0, 10))


class DataClass:
    def __init__(self, app):
        self.app = app
        self.settings = {
            'connection': {
                'obs_data': {
                    'host': None,
                    'port': None,
                    'password': None
                },
                'serial_data': {
                    'com_port': None,
                    'baud_rate': None
                }
            },
            'online': {

            },
            'script': {

            },
            'mapping': {
                "B0": None,
                "B1": None,
                "B2": None,
                "B3": None,
                "P0": None,
                "P1": None,
                "P2": None,
                "P3": None,
                "G0": None,
                "G1": None,
                "G2": None,
                "G3": None
            }
        }

    def update_settings(self):
        self.update_connection_page_settings()
        self.update_online_page_settings()
        self.update_mapping_page_settings()
        self.update_script_page_settings()
        self.app.logger.debug(f"update settings ok")

    def update_online_page_settings(self):
        pass

    def update_mapping_page_settings(self):
        pass

    def update_script_page_settings(self):
        pass

    def update_connection_page_settings(self):
        self.settings['connection']['obs_data']['host'] = self.app.pages['connection'].entries['host'].get()
        self.settings['connection']['obs_data']['port'] = self.app.pages['connection'].entries['port'].get()
        self.settings['connection']['obs_data']['password'] = self.app.pages['connection'].entries['password'].get()
        self.settings['connection']['serial_data']['com_port'] = self.app.pages['connection'].entries['com_port'].get()
        self.settings['connection']['serial_data']['baud_rate'] = self.app.pages['connection'].entries['baud_rate'].get()

    def save_settings(self):
        with open('settings.json', 'w') as file:
            json.dump(self.settings, file)
            self.app.logger.debug("settings.json save ok")

    def update_widgets(self, page):
        if page == self.app.pages['connection']:
            self.update_connection_page_widgets()
        elif page == self.app.pages['online']:
            self.update_online_page_widgets()
        elif page == self.app.pages['mapping']:
            self.update_mapping_page_widgets()
        elif page == self.app.pages['script']:
            self.update_script_page_widgets()
        self.app.logger.debug(f"widget update ok: {page}")

    def update_connection_page_widgets(self):
        self.app.pages['connection'].entries['host'].insert(0, self.settings['connection']['obs_data']['host'] or "")
        self.app.pages['connection'].entries['port'].insert(0, self.settings['connection']['obs_data']['port'] or "")
        self.app.pages['connection'].entries['password'].insert(0, self.settings['connection']['obs_data']['password'] or "")
        self.app.pages['connection'].entries['com_port'].insert(0, self.settings['connection']['serial_data']['com_port'] or "")
        self.app.pages['connection'].entries['baud_rate'].insert(0, self.settings['connection']['serial_data']['baud_rate'] or "")

    def update_online_page_widgets(self):
        pass

    def update_mapping_page_widgets(self):
        pass

    def update_script_page_widgets(self):
        pass

    def load_settings(self):
        try:
            with open('settings.json', 'r') as file:
                settings = json.load(file)
                self.settings = settings
                self.app.logger.debug("settings.json load ok")
        except FileNotFoundError:
            self.save_settings()
            self.app.logger.debug("settings.json creation ok")


class Application(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        # class variables
        self.new_page = False
        self.pages = {}
        self.current_page = None
        self.list = {"scene": [],
                     "script": [],
                     "volume": []}
        # class objects
        self.logger = None
        self.settings = None
        self.sdc = None
        # init application
        self.init()

    def init(self):
        self.init_logger()
        self.init_graphic()
        self.init_data()
        self.init_sdc()
        self.init_app_mainloop()

    def init_graphic(self):
        self.geometry("800x400")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.add_pages()

    def init_data(self):
        self.settings = DataClass(self)
        self.settings.load_settings()
        for page in self.pages:
            self.show_page(self.pages[page])
            self.settings.update_widgets(self.current_page)
        self.show_page(self.pages['online'])

    def init_sdc(self):
        self.sdc = StreamDeckController_New.StreamDeckController(self)
        self.sdc.connect_obs_web_socket()
        self.sdc.open_serial_communication()
        if self.sdc.start():
            self.logger.debug("init ok")
        else:
            self.logger.debug("init error")

    def init_logger(self):
        self.logger = Logger(levels=['debug', 'error'], filename='logs.log', console=True)
        self.logger.debug("* * *  New App Execution * * *")

    def init_app_mainloop(self):
        threading.Thread(target=self.task_app_mainloop, daemon=True).start()

    def add_pages(self):
        self.pages['connection'] = ConnectionPage(self)
        self.pages['online'] = OnlinePage(self)
        self.pages['mapping'] = MappingPage(self)
        self.pages['script'] = ScriptPage(self)

    def show_page(self, page):
        if self.current_page:
            self.current_page.hide()
        self.current_page = page
        self.current_page.show()

    def connection_page_handler(self):
        pass

    def online_page_handler(self):
        # variables definition
        scene_tuple = [
            ("B0", self.current_page.canvas["scene_0"]),
            ("B1", self.current_page.canvas["scene_1"]),
            ("B2", self.current_page.canvas["scene_2"]),
            ("B3", self.current_page.canvas["scene_3"])
        ]
        script_tuple = [
            ("G0", self.current_page.canvas["script_0"]),
            ("G1", self.current_page.canvas["script_1"]),
            ("G2", self.current_page.canvas["script_2"]),
            ("G3", self.current_page.canvas["script_3"])
        ]
        current_page = self.pages["online"]
        mapping = self.settings.settings['mapping']

        # check for new page first iteration
        if self.new_page:
            current_page.entries['sd_state'].configure(text="State: Connecting...")
            if self.sdc.ws is None:
                if not self.sdc.connect_obs_web_socket():
                    self.logger.debug("obsws error")
            if self.sdc.ser is None:
                if not self.sdc.open_serial_communication():
                    self.logger.debug("serial error")
            if self.sdc.start():
                # init online page with values
                current_page.entries['sd_state'].configure(text="State: Online")
                for name_label in current_page.labels.keys():
                    i = name_label.split("_")[1]
                    if "scene" in name_label:
                        key = f"B{i}"
                    elif "script" in name_label:
                        key = f"G{i}"
                    #elif "volume" in name_label:
                    #    key = f"P{i}"
                    else:
                        continue
                    if self.settings.settings["mapping"][key] is not None:
                        current_page.labels[name_label].configure(text=self.settings.settings["mapping"][key])
                        current_page.canvas[name_label].config(bg="grey")
                    else:
                        current_page.canvas[name_label].config(bg="red")
            else:
                current_page.entries['sd_state'].configure(text="State: Offline")
            self.new_page = False

        # online page routine
        if self.sdc.ws is not None and self.sdc.ser is not None:
            # update record / streaming state
            if self.sdc.get_record_state():
                current_page.canvas["record_state"].config(bg="yellow")
                self.sdc.ser.write("RecordOnLed\n".encode())
            else:
                current_page.canvas["record_state"].config(bg="red")
                self.sdc.ser.write("RecordOffLed\n".encode())
            if self.sdc.get_stream_state():
                current_page.canvas["stream_state"].config(bg="yellow")
                self.sdc.ser.write("StreamOnLed\n".encode())
            else:
                current_page.canvas["stream_state"].config(bg="red")
                self.sdc.ser.write("StreamOffLed\n".encode())

            # update scripts state
            for script, button_script_canvas in script_tuple:
                if script in mapping and button_script_canvas.cget("bg") != "red":
                    if self.sdc.script_executing == script:
                        bg_color = "yellow"
                    else:
                        bg_color = "gray"
                    button_script_canvas.config(bg=bg_color)

            # update scenes state
            for scene, button_scene_canvas in scene_tuple:
                if scene in mapping and button_scene_canvas.cget("bg") != "red":
                    if self.sdc.get_current_scene() == mapping[scene]:
                        bg_color = "yellow"
                    else:
                        bg_color = "gray"
                    button_scene_canvas.config(bg=bg_color)

            # update volumes state
            volume = 0
            volume_names = self.sdc.get_volumes_names()
            for volume_name in volume_names:
                if volume_name in mapping.values():
                    volume = self.sdc.get_volume(volume_name)
                    volume *= 1000
                for key, value in mapping.items():
                    if value == volume_name:
                        if key == "P0":
                            current_page.canvas["volume_0"].draw_ray_by_value(volume)
                        elif key == "P1":
                            current_page.canvas["volume_1"].draw_ray_by_value(volume)
                        elif key == "P2":
                            current_page.canvas["volume_2"].draw_ray_by_value(volume)
                        elif key == "P3":
                            current_page.canvas["volume_3"].draw_ray_by_value(volume)

    def mapping_page_handler(self):
        combobox_scenes = [
            ('B0', self.current_page.comboboxes["scene_0"], self.current_page.canvas["scene_0"]),
            ('B1', self.current_page.comboboxes["scene_1"], self.current_page.canvas["scene_1"]),
            ('B2', self.current_page.comboboxes["scene_2"], self.current_page.canvas["scene_2"]),
            ('B3', self.current_page.comboboxes["scene_3"], self.current_page.canvas["scene_3"])
        ]
        combobox_scripts = [
            ('G0', self.current_page.comboboxes["script_0"], self.current_page.canvas["script_0"]),
            ('G1', self.current_page.comboboxes["script_1"], self.current_page.canvas["script_1"]),
            ('G2', self.current_page.comboboxes["script_2"], self.current_page.canvas["script_2"]),
            ('G3', self.current_page.comboboxes["script_3"], self.current_page.canvas["script_3"])
        ]
        combobox_volumes = [
            ('P0', self.current_page.comboboxes["volume_0"], self.current_page.canvas["volume_0"]),
            ('P1', self.current_page.comboboxes["volume_1"], self.current_page.canvas["volume_1"]),
            ('P2', self.current_page.comboboxes["volume_2"], self.current_page.canvas["volume_2"]),
            ('P3', self.current_page.comboboxes["volume_3"], self.current_page.canvas["volume_3"])
        ]

        # init mapping page
        if self.new_page:
            for i, name_widget in enumerate(self.current_page.comboboxes.keys()):
                j = i % 4
                if "scene" in name_widget:
                    key = f"B{j}"
                elif "script" in name_widget:
                    key = f"G{j}"
                elif "volume" in name_widget:
                    key = f"P{j}"
                if self.settings.settings["mapping"][key] is not None:
                    self.current_page.comboboxes[name_widget].set(value=self.settings.settings["mapping"][key])
            self.new_page = False

        # update lists if something change in obs
        if self.list["scene"] != self.sdc.get_scene_names() or self.list["script"] != list(self.settings.settings["script"].keys()) or self.list["volume"] != self.sdc.get_volumes_names():
            self.list["scene"] = self.sdc.get_scene_names()
            self.list["script"] = list(self.settings.settings["script"].keys())
            self.list["volume"] = self.sdc.get_volumes_names()
            for name_widget in self.current_page.comboboxes.keys():
                widget_type = name_widget.split("_")[0]
                self.current_page.comboboxes[name_widget].configure(values=self.list[widget_type])

        for button, combobox, canvas in combobox_scenes:
            if combobox.get() in self.sdc.get_scene_names():
                self.settings.settings["mapping"][button] = combobox.get()
                canvas.config(bg="grey")
            else:
                canvas.config(bg="red")

        for button, combobox, canvas in combobox_scripts:
            if combobox.get() in list(self.settings.settings["script"].keys()):
                self.settings.settings["mapping"][button] = combobox.get()
                canvas.config(bg="grey")
            else:
                canvas.config(bg="red")

        for pot, combobox, canvas in combobox_volumes:
            if combobox.get() in self.sdc.get_volumes_names():
                self.settings.settings["mapping"][pot] = combobox.get()

    def script_page_handler(self):
        pass

    def task_app_mainloop(self):
        previous_page = "no_page"
        time_diff = -1
        while True:
            time_start = time.time()

            if self.current_page != previous_page:
                self.logger.debug("---------- CHANGE PAGE ----------")
                self.settings.update_settings()
                self.settings.save_settings()
                previous_page = self.current_page
                self.new_page = True

            if self.current_page == self.pages['connection']:
                self.connection_page_handler()
            elif self.current_page == self.pages['online']:
                self.online_page_handler()
            elif self.current_page == self.pages['mapping']:
                self.mapping_page_handler()
            elif self.current_page == self.pages['script']:
                self.script_page_handler()

            if not (round(time_diff, 3) - 0.05 <= round(time.time() - time_start, 3) <= round(time_diff, 3) + 0.1):
                time_diff = time.time() - time_start
                self.logger.debug(f"thread execution time = {round(time_diff, 3)} seconds")

            time.sleep(0.01)


if __name__ == "__main__":
    customtkinter.set_appearance_mode("Dark")
    application = Application()
    application.mainloop()
