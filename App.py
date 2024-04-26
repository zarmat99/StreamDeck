# implementation task:
# - aggiungere il metodo update generale che dipende dalla pagina corrente in cui ci si trova
# - accorpare la load online parameters in update online parameters (quindi aggiornare le label in real time)
# - implementare la cancellazione di un elemento dal mapping

# to fix
# - corregere il bug che non cambia colore il pot del volume se questo non è mappato

# new implementation
# - aggiungere la possibilità di cancellare un elemento dal mapping

import tkinter as tk
import tkinter.messagebox
import customtkinter
import PotentiometerWidget
import StreamDeckController
import json
import scripting

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("dark-blue")
pages = {"connection": 0, "online": 1, "mapping": 2, "script": 3}


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        # ------------------- Variables -------------------------------------------------------------------------------
        self.script_button = None
        self.delete_script_button = None
        self.clear_script_button = None
        self.script_selected = None
        self.save_script_button = None
        self.delete_step_button = None
        self.add_step_button = None
        self.script_scrollable_frame = None
        self.script_name_entry = None
        self.script_list_combobox = None
        self.script_page_title_label = None
        self.script_page_bottom_frame = None
        self.script_page_script_frame = None
        self.script_page_title_frame = None
        self.var_combobox_volumes = None
        self.var_combobox_scenes = None
        self.var_combobox_scripts = None
        self.volume3_combobox = None
        self.volume2_combobox = None
        self.volume1_combobox = None
        self.volume0_combobox = None
        self.script3_button_combobox = None
        self.script2_button_combobox = None
        self.script1_button_combobox = None
        self.script0_button_combobox = None
        self.scene3_button_combobox = None
        self.scene2_button_combobox = None
        self.scene1_button_combobox = None
        self.scene0_button_combobox = None
        self.mapping_page_streams_frame = None
        self.mapping_page_volumes_frame = None
        self.mapping_page_script_frame = None
        self.mapping_page_scenes_frame = None
        self.back_to_online_button = None
        self.mapping_page_title_label = None
        self.mapping_page_bottom_frame = None
        self.mapping_page_title_frame = None
        self.mapping_button = None
        self.script3_button_canvas = None
        self.script3_button_label = None
        self.script2_button_canvas = None
        self.script2_button_label = None
        self.script1_button_canvas = None
        self.script1_button_label = None
        self.script0_button_canvas = None
        self.script0_button_label = None
        self.online_page_script_frame = None
        self.connection_info_button = None
        self.online_page_bottom_frame = None
        self.volume3_pot = None
        self.volume3_label = None
        self.volume2_pot = None
        self.volume2_label = None
        self.volume1_pot = None
        self.volume1_label = None
        self.volume0_pot = None
        self.volume0_label = None
        self.scene3_button_canvas = None
        self.scene3_button_label = None
        self.scene2_button_canvas = None
        self.scene2_button_label = None
        self.scene1_button_canvas = None
        self.scene1_button_label = None
        self.scene0_button_canvas = None
        self.scene0_button_label = None
        self.stream_button_label = None
        self.record_button_label = None
        self.stream_button_canvas = None
        self.record_button = None
        self.record_button_canvas = None
        self.online_page_volumes_frame = None
        self.online_page_scenes_frame = None
        self.online_page_streams_frame = None
        self.online_page_title_label = None
        self.online_page_title_frame = None
        self.streamdeck_configuration_label = None
        self.connection_page_bottom_frame = None
        self.connection_page_title_frame = None
        self.connect_button = None
        self.baud_rate_entry = None
        self.baud_rate_label = None
        self.com_port_entry = None
        self.com_port_label = None
        self.obs_configuration_label = None
        self.password_entry = None
        self.password_label = None
        self.port_entry = None
        self.port_label = None
        self.host_entry = None
        self.host_label = None
        self.streamdeck_conf_frame = None
        self.obs_conf_frame = None
        self.connection_page_title_label = None
        self.sdc = None
        self.page = pages['connection']
        self.current_script_combobox_list = []
        self.current_script_entry_list = []
        self.host_entry_var = tkinter.StringVar()
        self.port_entry_var = tkinter.StringVar()
        self.com_port_entry_var = tkinter.StringVar()
        self.password_entry_var = tkinter.StringVar()
        self.baud_rate_var = tkinter.StringVar()
        # -------------------------------------------------------------------------------------------------------------

        # ------------------- Init ------------------------------------------------------------------------------------
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        # self.bind("<Configure>", self.resize)
        self.load_settings()
        self.create_connection_page()
        self.grid_connection_page()
        # -------------------------------------------------------------------------------------------------------------

    # ----------------------------------------- M E T H O D S ---------------------------------------------------------

    # ------------------- General Methods -----------------------------------------------------------------------------
    def resize(self, event):
        if self.volume0_pot is not None and self.volume1_pot is not None and self.volume2_pot is not None and self.volume3_pot is not None:
            online_page_volumes_frame_width = event.width // 4
            self.online_page_volumes_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
            self.volume0_pot.config(width=online_page_volumes_frame_width)
            self.volume1_pot.config(width=online_page_volumes_frame_width)
            self.volume2_pot.config(width=online_page_volumes_frame_width)
            self.volume3_pot.config(width=online_page_volumes_frame_width)
    # -----------------------------------------------------------------------------------------------------------------

    # ------------------- Connection Page Methods ---------------------------------------------------------------------
    def create_connection_page(self):
        self.create_connection_page_frames()
        self.create_connection_page_widgets_in_frames()
        self.configure_connection_page_frames()
        self.grid_connection_page_widgets_in_frames()

    def create_connection_page_frames(self):
        self.connection_page_title_frame = customtkinter.CTkFrame(self)
        self.obs_conf_frame = customtkinter.CTkFrame(self)
        self.streamdeck_conf_frame = customtkinter.CTkFrame(self)
        self.connection_page_bottom_frame = customtkinter.CTkFrame(self)

    def create_connection_page_widgets_in_frames(self):
        # connection_page_title_frame
        self.connection_page_title_label = customtkinter.CTkLabel(self.connection_page_title_frame,
                                                                  text="Connection Page",
                                                                  font=customtkinter.CTkFont(size=25, weight="bold"))
        # obs_conf_frame
        self.obs_configuration_label = customtkinter.CTkLabel(self.obs_conf_frame, text="OBS Configurations",
                                                              font=customtkinter.CTkFont(size=20))
        self.host_label = customtkinter.CTkLabel(self.obs_conf_frame, text="Host",
                                                 font=customtkinter.CTkFont(size=15))
        self.host_entry = customtkinter.CTkEntry(self.obs_conf_frame, textvariable=self.host_entry_var)
        self.port_label = customtkinter.CTkLabel(self.obs_conf_frame, text="Port",
                                                 font=customtkinter.CTkFont(size=15))
        self.port_entry = customtkinter.CTkEntry(self.obs_conf_frame, textvariable=self.port_entry_var)
        self.password_label = customtkinter.CTkLabel(self.obs_conf_frame, text="Password",
                                                     font=customtkinter.CTkFont(size=15))
        self.password_entry = customtkinter.CTkEntry(self.obs_conf_frame, textvariable=self.password_entry_var)
        # streamdeck_conf_frame
        self.streamdeck_configuration_label = customtkinter.CTkLabel(self.streamdeck_conf_frame,
                                                                     text="StreamDeck Configurations",
                                                                     font=customtkinter.CTkFont(size=20))
        self.com_port_label = customtkinter.CTkLabel(self.streamdeck_conf_frame, text="Com Port",
                                                     font=customtkinter.CTkFont(size=15))
        self.com_port_entry = customtkinter.CTkEntry(self.streamdeck_conf_frame, textvariable=self.com_port_entry_var)
        self.baud_rate_label = customtkinter.CTkLabel(self.streamdeck_conf_frame, text="Baud Rate",
                                                      font=customtkinter.CTkFont(size=15))
        self.baud_rate_entry = customtkinter.CTkEntry(self.streamdeck_conf_frame, textvariable=self.baud_rate_var)
        # connection_page_bottom_frame
        self.connect_button = customtkinter.CTkButton(self.connection_page_bottom_frame, text="Connect",
                                                      command=self.connect_button_event)

    def configure_connection_page_frames(self):
        # connection_page_title_frame
        self.connection_page_title_frame.grid_rowconfigure(0, weight=1)
        self.connection_page_title_frame.grid_columnconfigure(0, weight=1)
        # obs_conf_frame
        self.obs_conf_frame.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.obs_conf_frame.grid_columnconfigure((0, 1), weight=1)
        # streamdeck_conf_frame
        self.streamdeck_conf_frame.grid_rowconfigure((0, 1, 2), weight=1)
        self.streamdeck_conf_frame.grid_columnconfigure((0, 1), weight=1)
        # connection_page_bottom_frame
        self.connection_page_bottom_frame.grid_rowconfigure(0, weight=1)
        self.connection_page_bottom_frame.grid_columnconfigure(0, weight=1)

    def grid_connection_page_widgets_in_frames(self):
        # connection_page_title_frame
        self.connection_page_title_label.grid(row=0, column=0)
        # obs_conf_frame
        self.obs_configuration_label.grid(row=0, column=0, columnspan=2)
        self.host_label.grid(row=1, column=0)
        self.host_entry.grid(row=1, column=1)
        self.port_label.grid(row=2, column=0)
        self.port_entry.grid(row=2, column=1)
        self.password_label.grid(row=3, column=0)
        self.password_entry.grid(row=3, column=1)
        # streamdeck_conf_frame
        self.streamdeck_configuration_label.grid(row=0, column=0, columnspan=2)
        self.com_port_label.grid(row=1, column=0)
        self.com_port_entry.grid(row=1, column=1)
        self.baud_rate_label.grid(row=2, column=0)
        self.baud_rate_entry.grid(row=2, column=1)
        # connection_page_bottom_frame
        self.connect_button.grid(row=0, column=0, sticky="e")

    def grid_connection_page(self):
        # configure window
        self.title("StreamDeck - Connection")
        self.geometry(f"{800}x{400}")

        # configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.reset_column_row_configure(column=0, row=3)

        # grid frames
        self.connection_page_title_frame.grid(row=0, column=0, sticky="nswe", padx=20, pady=(20, 5))
        self.obs_conf_frame.grid(row=1, column=0, sticky="nswe", padx=20, pady=(5, 5))
        self.streamdeck_conf_frame.grid(row=2, column=0,  sticky="nswe", padx=20, pady=(5, 5))
        self.connection_page_bottom_frame.grid(row=3, column=0, sticky="nswe", padx=20, pady=(5, 20))

    def forget_connection_page(self):
        self.connection_page_title_frame.grid_forget()
        self.streamdeck_conf_frame.grid_forget()
        self.obs_conf_frame.grid_forget()
        self.connection_page_bottom_frame.grid_forget()

    def connect_button_event(self):
        if self.sdc is None:
            connection_page_data = self.get_dict_connection_page_data()
            self.sdc = StreamDeckController.StreamDeckController(connection_page_data['obs_data'],
                                                                 connection_page_data['serial_data'])
            self.sdc.start()
        self.save_settings()
        self.from_connection_page_to_online_page_event()
    # -----------------------------------------------------------------------------------------------------------------

    # ------------------- Online Page Methods -------------------------------------------------------------------------
    def create_online_page(self):
        self.create_online_page_frames()
        self.create_online_page_widgets_in_frames()
        self.configure_online_page_frames()
        self.grid_online_page_widgets_in_frames()

    def create_online_page_frames(self):
        self.online_page_title_frame = customtkinter.CTkFrame(self)
        self.online_page_streams_frame = customtkinter.CTkFrame(self)
        self.online_page_scenes_frame = customtkinter.CTkFrame(self)
        self.online_page_script_frame = customtkinter.CTkFrame(self)
        self.online_page_volumes_frame = customtkinter.CTkFrame(self)
        self.online_page_bottom_frame = customtkinter.CTkFrame(self)

    def create_online_page_widgets_in_frames(self):
        # online_page_title_frame
        self.online_page_title_label = customtkinter.CTkLabel(self.online_page_title_frame, text="Online Page",
                                                              font=customtkinter.CTkFont(size=25, weight="bold"))
        # online_page_streams_frame
        self.record_button_label = customtkinter.CTkLabel(self.online_page_streams_frame, text="Record State",
                                                          font=customtkinter.CTkFont(size=15))
        self.record_button_canvas = tk.Canvas(self.online_page_streams_frame, width=70, height=70, bg="red")
        self.stream_button_label = customtkinter.CTkLabel(self.online_page_streams_frame, text="Stream State",
                                                          font=customtkinter.CTkFont(size=15))
        self.stream_button_canvas = tk.Canvas(self.online_page_streams_frame, width=70, height=70, bg="red")
        # online_page_scenes_frame
        self.scene0_button_label = customtkinter.CTkLabel(self.online_page_scenes_frame, text="Scene 0",
                                                          font=customtkinter.CTkFont(size=15))
        self.scene0_button_canvas = tk.Canvas(self.online_page_scenes_frame, width=70, height=70, bg="grey")
        self.scene1_button_label = customtkinter.CTkLabel(self.online_page_scenes_frame, text="Scene 1",
                                                          font=customtkinter.CTkFont(size=15))
        self.scene1_button_canvas = tk.Canvas(self.online_page_scenes_frame, width=70, height=70, bg="grey")
        self.scene2_button_label = customtkinter.CTkLabel(self.online_page_scenes_frame, text="Scene 2",
                                                          font=customtkinter.CTkFont(size=15))
        self.scene2_button_canvas = tk.Canvas(self.online_page_scenes_frame, width=70, height=70, bg="grey")
        self.scene3_button_label = customtkinter.CTkLabel(self.online_page_scenes_frame, text="Scene 3",
                                                          font=customtkinter.CTkFont(size=15))
        self.scene3_button_canvas = tk.Canvas(self.online_page_scenes_frame, width=70, height=70, bg="grey")
        # online_page_script_frame
        self.script0_button_label = customtkinter.CTkLabel(self.online_page_script_frame, text="Script 0",
                                                           font=customtkinter.CTkFont(size=15))
        self.script0_button_canvas = tk.Canvas(self.online_page_script_frame, width=70, height=70, bg="grey")
        self.script1_button_label = customtkinter.CTkLabel(self.online_page_script_frame, text="Script 1",
                                                           font=customtkinter.CTkFont(size=15))
        self.script1_button_canvas = tk.Canvas(self.online_page_script_frame, width=70, height=70, bg="grey")
        self.script2_button_label = customtkinter.CTkLabel(self.online_page_script_frame, text="Script 2",
                                                           font=customtkinter.CTkFont(size=15))
        self.script2_button_canvas = tk.Canvas(self.online_page_script_frame, width=70, height=70, bg="grey")
        self.script3_button_label = customtkinter.CTkLabel(self.online_page_script_frame, text="Script 3",
                                                           font=customtkinter.CTkFont(size=15))
        self.script3_button_canvas = tk.Canvas(self.online_page_script_frame, width=70, height=70, bg="grey")
        # online_page_volumes_frame
        self.volume0_label = customtkinter.CTkLabel(self.online_page_volumes_frame, text="Volume 0",
                                                    font=customtkinter.CTkFont(size=15))
        self.volume0_pot = PotentiometerWidget.PotentiometerWidget(self.online_page_volumes_frame, radius=40)
        self.volume1_label = customtkinter.CTkLabel(self.online_page_volumes_frame, text="Volume 1",
                                                    font=customtkinter.CTkFont(size=15))
        self.volume1_pot = PotentiometerWidget.PotentiometerWidget(self.online_page_volumes_frame, radius=40)
        self.volume2_label = customtkinter.CTkLabel(self.online_page_volumes_frame, text="Volume 2",
                                                    font=customtkinter.CTkFont(size=15))
        self.volume2_pot = PotentiometerWidget.PotentiometerWidget(self.online_page_volumes_frame, radius=40)
        self.volume3_label = customtkinter.CTkLabel(self.online_page_volumes_frame, text="Volume 3",
                                                    font=customtkinter.CTkFont(size=15))
        self.volume3_pot = PotentiometerWidget.PotentiometerWidget(self.online_page_volumes_frame, radius=40)
        # online_page_bottom_frame
        self.connection_info_button = customtkinter.CTkButton(self.online_page_bottom_frame, text="Connection Info",
                                                              command=self.from_online_page_to_connection_page_event)
        self.mapping_button = customtkinter.CTkButton(self.online_page_bottom_frame, text="Mapping",
                                                      command=self.from_online_page_to_mapping_page_event,
                                                      width=100)
        self.script_button = customtkinter.CTkButton(self.online_page_bottom_frame, text="Script",
                                                     command=self.from_online_page_to_script_page_event,
                                                     width=100)

    def configure_online_page_frames(self):
        # online_page_title_frame
        self.online_page_title_frame.grid_rowconfigure(0, weight=1)
        self.online_page_title_frame.grid_columnconfigure(0, weight=1)
        # online_page_streams_frame
        self.online_page_streams_frame.grid_rowconfigure((0, 1), weight=1)
        self.online_page_streams_frame.grid_columnconfigure((0, 1), weight=1)
        # online_page_scenes_frame
        self.online_page_scenes_frame.grid_rowconfigure((0, 1), weight=1)
        self.online_page_scenes_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        # online_page_script_frame
        self.online_page_script_frame.grid_rowconfigure((0, 1), weight=1)
        self.online_page_script_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        # online_page_volumes_frame
        self.online_page_volumes_frame.grid_rowconfigure((0, 1), weight=1)
        self.online_page_volumes_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        # online_page_bottom_frame
        self.online_page_bottom_frame.grid_rowconfigure(0, weight=1)
        self.online_page_bottom_frame.grid_columnconfigure(0, weight=1)

    def grid_online_page_widgets_in_frames(self):
        # online_page_title_frame
        self.online_page_title_label.grid(row=0, column=0)
        # online_page_streams_frame
        self.record_button_label.grid(row=0, column=0)
        self.stream_button_label.grid(row=0, column=1)
        self.record_button_canvas.grid(row=1, column=0)
        self.stream_button_canvas.grid(row=1, column=1)
        # online_page_scenes_frame
        self.scene0_button_label.grid(row=0, column=0)
        self.scene1_button_label.grid(row=0, column=1)
        self.scene2_button_label.grid(row=0, column=2)
        self.scene3_button_label.grid(row=0, column=3)
        self.scene0_button_canvas.grid(row=1, column=0)
        self.scene1_button_canvas.grid(row=1, column=1)
        self.scene2_button_canvas.grid(row=1, column=2)
        self.scene3_button_canvas.grid(row=1, column=3)
        # online_page_script_frame
        self.script0_button_label.grid(row=0, column=0)
        self.script1_button_label.grid(row=0, column=1)
        self.script2_button_label.grid(row=0, column=2)
        self.script3_button_label.grid(row=0, column=3)
        self.script0_button_canvas.grid(row=1, column=0)
        self.script1_button_canvas.grid(row=1, column=1)
        self.script2_button_canvas.grid(row=1, column=2)
        self.script3_button_canvas.grid(row=1, column=3)
        # online_page_volumes_frame
        self.volume0_label.grid(row=0, column=0, sticky="nsew")
        self.volume1_label.grid(row=0, column=1, sticky="nsew")
        self.volume2_label.grid(row=0, column=2, sticky="nsew")
        self.volume3_label.grid(row=0, column=3, sticky="nsew")
        self.volume0_pot.grid(row=1, column=0, sticky="nsew")
        self.volume1_pot.grid(row=1, column=1, sticky="nsew")
        self.volume2_pot.grid(row=1, column=2, sticky="nsew")
        self.volume3_pot.grid(row=1, column=3, sticky="nsew")
        # online_page_bottom_frame
        self.connection_info_button.grid(row=0, column=0, sticky="w", padx=10)
        self.script_button.grid(row=0, column=1, sticky="e", padx=(0, 5))
        self.mapping_button.grid(row=0, column=2, sticky="e", padx=(5, 10))

    def grid_online_page(self):
        # configure window
        self.title("StreamDeck - Online")
        self.geometry(f"{800}x{400}")

        # configure grid
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)
        self.reset_column_row_configure(column=1, row=4)

        # grid
        self.online_page_title_frame.grid(row=0, column=0, columnspan=2, sticky="nswe", padx=20, pady=(20, 5))
        self.online_page_streams_frame.grid(row=1, column=0, columnspan=2, sticky="nswe", padx=20, pady=(5, 5))
        self.online_page_scenes_frame.grid(row=2, column=0, sticky="nswe", padx=(20, 5), pady=(5, 5))
        self.online_page_script_frame.grid(row=2, column=1, sticky="nswe", padx=(5, 20), pady=(5, 5))
        self.online_page_volumes_frame.grid(row=3, column=0, columnspan=2, sticky="nswe", padx=20, pady=(5, 5))
        self.online_page_bottom_frame.grid(row=4, column=0, columnspan=2, sticky="nswe", padx=20, pady=(5, 20))

    def forget_online_page(self):
        self.online_page_title_frame.grid_forget()
        self.online_page_streams_frame.grid_forget()
        self.online_page_scenes_frame.grid_forget()
        self.online_page_script_frame.grid_forget()
        self.online_page_volumes_frame.grid_forget()
        self.online_page_bottom_frame.grid_forget()

    def load_online_page_parameters(self):
        self.var_combobox_scenes = self.sdc.get_scene_names()
        self.var_combobox_scripts = list(self.sdc.script.keys())
        self.var_combobox_volumes = self.sdc.get_volumes_names()

        if 'B0' in self.sdc.mapping:
            self.scene0_button_label.configure(text=self.sdc.mapping['B0'])
            self.scene0_button_canvas.configure(bg="grey")
        else:
            self.scene0_button_canvas.configure(bg="red")
        if 'B1' in self.sdc.mapping:
            self.scene1_button_label.configure(text=self.sdc.mapping['B1'])
            self.scene1_button_canvas.configure(bg="grey")
        else:
            self.scene1_button_canvas.configure(bg="red")
        if 'B2' in self.sdc.mapping:
            self.scene2_button_label.configure(text=self.sdc.mapping['B2'])
            self.scene2_button_canvas.configure(bg="grey")
        else:
            self.scene2_button_canvas.configure(bg="red")
        if 'B3' in self.sdc.mapping:
            self.scene3_button_label.configure(text=self.sdc.mapping['B3'])
            self.scene3_button_canvas.configure(bg="grey")
        else:
            self.scene3_button_canvas.configure(bg="red")
        if 'G0' in self.sdc.mapping:
            self.script0_button_label.configure(text=self.sdc.mapping['G0'])
            self.script0_button_canvas.configure(bg="grey")
        else:
            self.script0_button_canvas.configure(bg="red")
        if 'G1' in self.sdc.mapping:
            self.script1_button_label.configure(text=self.sdc.mapping['G1'])
            self.script1_button_canvas.configure(bg="grey")
        else:
            self.script1_button_canvas.configure(bg="red")
        if 'G2' in self.sdc.mapping:
            self.script2_button_label.configure(text=self.sdc.mapping['G2'])
            self.script2_button_canvas.configure(bg="grey")
        else:
            self.script2_button_canvas.configure(bg="red")
        if 'G3' in self.sdc.mapping:
            self.script3_button_label.configure(text=self.sdc.mapping['G3'])
            self.script3_button_canvas.configure(bg="grey")
        else:
            self.script3_button_canvas.configure(bg="red")
        if 'P0' in self.sdc.mapping:
            self.volume0_label.configure(text=self.sdc.mapping['P0'])
            self.volume0_pot.itemconfigure(self.volume0_pot.circle, fill="gray")
        else:
            self.volume0_pot.itemconfigure(self.volume0_pot.circle, fill="red")
        if 'P1' in self.sdc.mapping:
            self.volume1_label.configure(text=self.sdc.mapping['P1'])
            self.volume1_pot.itemconfigure(self.volume1_pot.circle, fill="gray")
        else:
            self.volume1_pot.itemconfigure(self.volume1_pot.circle, fill="red")
        if 'P2' in self.sdc.mapping:
            self.volume2_label.configure(text=self.sdc.mapping['P2'])
            self.volume2_pot.itemconfigure(self.volume2_pot.circle, fill="gray")
        else:
            self.volume2_pot.itemconfigure(self.volume2_pot.circle, fill="red")
        if 'P3' in self.sdc.mapping:
            self.volume3_label.configure(text=self.sdc.mapping['P3'])
            self.volume3_pot.itemconfigure(self.volume3_pot.circle, fill="gray")
        else:
            self.volume3_pot.itemconfigure(self.volume3_pot.circle, fill="red")

    def update_online_page_parameters(self):
        scene_tuple = [
            ("B0", self.scene0_button_canvas),
            ("B1", self.scene1_button_canvas),
            ("B2", self.scene2_button_canvas),
            ("B3", self.scene3_button_canvas)
        ]
        script_tuple = [
            ("G0", self.script0_button_canvas),
            ("G1", self.script1_button_canvas),
            ("G2", self.script2_button_canvas),
            ("G3", self.script3_button_canvas)
        ]

        # update record / streaming state
        if self.sdc.get_record_state():
            self.record_button_canvas.config(bg="yellow")
        else:
            self.record_button_canvas.config(bg="red")
        if self.sdc.get_stream_state():
            self.stream_button_canvas.config(bg="yellow")
        else:
            self.stream_button_canvas.config(bg="red")

        for script, button_script_canvas in script_tuple:
            if script in self.sdc.mapping:
                bg_color = "yellow" if self.sdc.script_executing == script else "grey"
            else:
                bg_color = "red"
            button_script_canvas.config(bg=bg_color)

        for scene, button_scene_canvas in scene_tuple:
            if scene in self.sdc.mapping:
                bg_color = "yellow" if self.sdc.get_current_scene() == self.sdc.mapping[scene] else "grey"
            else:
                bg_color = "red"
            button_scene_canvas.config(bg=bg_color)

        volume_names = self.sdc.get_volumes_names()
        for volume_name in volume_names:
            if volume_name in self.sdc.mapping.values():
                volume = self.sdc.get_volume(volume_name)
                volume *= 1000
            for key, value in self.sdc.mapping.items():
                if value == volume_name:
                    if key == "P0":
                        self.volume0_pot.draw_ray_by_value(volume)
                    elif key == "P1":
                        self.volume1_pot.draw_ray_by_value(volume)
                    elif key == "P2":
                        self.volume2_pot.draw_ray_by_value(volume)
                    elif key == "P3":
                        self.volume3_pot.draw_ray_by_value(volume)
        if self.page == pages['online']:
            self.after(10, self.update_online_page_parameters)
    # -----------------------------------------------------------------------------------------------------------------

    # ------------------- Mapping Page Methods ------------------------------------------------------------------------
    def create_mapping_page(self):
        self.create_mapping_page_frames()
        self.create_mapping_page_widgets_in_frames()
        self.configure_mapping_page_frames()
        self.grid_mapping_page_widgets_in_frames()

    def create_mapping_page_frames(self):
        self.mapping_page_title_frame = customtkinter.CTkFrame(self)
        self.mapping_page_streams_frame = customtkinter.CTkFrame(self)
        self.mapping_page_scenes_frame = customtkinter.CTkFrame(self)
        self.mapping_page_script_frame = customtkinter.CTkFrame(self)
        self.mapping_page_volumes_frame = customtkinter.CTkFrame(self)
        self.mapping_page_bottom_frame = customtkinter.CTkFrame(self)

    def create_mapping_page_widgets_in_frames(self):
        # mapping_page_title_frame
        self.mapping_page_title_label = customtkinter.CTkLabel(self.mapping_page_title_frame, text="Mapping Page",
                                                               font=customtkinter.CTkFont(size=25, weight="bold"))
        # mapping_page_streams_frame
        self.record_button_label = customtkinter.CTkLabel(self.mapping_page_streams_frame, text="Record State",
                                                          font=customtkinter.CTkFont(size=15))
        self.record_button_canvas = tk.Canvas(self.mapping_page_streams_frame, width=70, height=70, bg="red")
        self.stream_button_label = customtkinter.CTkLabel(self.mapping_page_streams_frame, text="Stream State",
                                                          font=customtkinter.CTkFont(size=15))
        self.stream_button_canvas = tk.Canvas(self.mapping_page_streams_frame, width=70, height=70, bg="red")
        # mapping_page_scenes_frame
        self.scene0_button_combobox = customtkinter.CTkComboBox(self.mapping_page_scenes_frame, values=[""],
                                                                width=100)
        self.scene0_button_canvas = tk.Canvas(self.mapping_page_scenes_frame, width=70, height=70, bg="grey")
        self.scene1_button_combobox = customtkinter.CTkComboBox(self.mapping_page_scenes_frame, values=[""],
                                                                width=100)
        self.scene1_button_canvas = tk.Canvas(self.mapping_page_scenes_frame, width=70, height=70, bg="grey")
        self.scene2_button_combobox = customtkinter.CTkComboBox(self.mapping_page_scenes_frame, values=[""],
                                                                width=100)
        self.scene2_button_canvas = tk.Canvas(self.mapping_page_scenes_frame, width=70, height=70, bg="grey")
        self.scene3_button_combobox = customtkinter.CTkComboBox(self.mapping_page_scenes_frame, values=[""],
                                                                width=100)
        self.scene3_button_canvas = tk.Canvas(self.mapping_page_scenes_frame, width=70, height=70, bg="grey")

        # mapping_page_script_frame
        self.script0_button_combobox = customtkinter.CTkComboBox(self.mapping_page_script_frame, values=[""],
                                                                 width=100)
        self.script0_button_canvas = tk.Canvas(self.mapping_page_script_frame, width=70, height=70, bg="grey")
        self.script1_button_combobox = customtkinter.CTkComboBox(self.mapping_page_script_frame, values=[""],
                                                                 width=100)
        self.script1_button_canvas = tk.Canvas(self.mapping_page_script_frame, width=70, height=70, bg="grey")
        self.script2_button_combobox = customtkinter.CTkComboBox(self.mapping_page_script_frame, values=[""],
                                                                 width=100)
        self.script2_button_canvas = tk.Canvas(self.mapping_page_script_frame, width=70, height=70, bg="grey")
        self.script3_button_combobox = customtkinter.CTkComboBox(self.mapping_page_script_frame, values=[""],
                                                                 width=100)
        self.script3_button_canvas = tk.Canvas(self.mapping_page_script_frame, width=70, height=70, bg="grey")

        # mapping_page_volumes_frame
        self.volume0_combobox = customtkinter.CTkComboBox(self.mapping_page_volumes_frame, values=[""],
                                                          width=100)
        self.volume0_pot = PotentiometerWidget.PotentiometerWidget(self.mapping_page_volumes_frame, radius=40)
        self.volume1_combobox = customtkinter.CTkComboBox(self.mapping_page_volumes_frame, values=[""],
                                                          width=100)
        self.volume1_pot = PotentiometerWidget.PotentiometerWidget(self.mapping_page_volumes_frame, radius=40)
        self.volume2_combobox = customtkinter.CTkComboBox(self.mapping_page_volumes_frame, values=[""],
                                                          width=100)
        self.volume2_pot = PotentiometerWidget.PotentiometerWidget(self.mapping_page_volumes_frame, radius=40)
        self.volume3_combobox = customtkinter.CTkComboBox(self.mapping_page_volumes_frame, values=[""],
                                                          width=100)
        self.volume3_pot = PotentiometerWidget.PotentiometerWidget(self.mapping_page_volumes_frame, radius=40)

        # mapping_page_bottom_frame
        self.back_to_online_button = customtkinter.CTkButton(self.mapping_page_bottom_frame, text="Back to Online",
                                                             command=self.from_mapping_page_to_online_page_event)

    def configure_mapping_page_frames(self):
        # mapping_page_title_frame
        self.mapping_page_title_frame.grid_rowconfigure(0, weight=1)
        self.mapping_page_title_frame.grid_columnconfigure(0, weight=1)
        # mapping_page_streams_frame
        self.mapping_page_streams_frame.grid_rowconfigure((0, 1), weight=1)
        self.mapping_page_streams_frame.grid_columnconfigure((0, 1), weight=1)
        # mapping_page_scenes_frame
        self.mapping_page_scenes_frame.grid_rowconfigure((0, 1), weight=1)
        self.mapping_page_scenes_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        # mapping_page_script_frame
        self.mapping_page_script_frame.grid_rowconfigure((0, 1), weight=1)
        self.mapping_page_script_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        # mapping_page_volumes_frame
        self.mapping_page_volumes_frame.grid_rowconfigure((0, 1), weight=1)
        self.mapping_page_volumes_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        # mapping_page_bottom_frame
        self.mapping_page_bottom_frame.grid_rowconfigure(0, weight=1)
        self.mapping_page_bottom_frame.grid_columnconfigure(0, weight=1)

    def grid_mapping_page_widgets_in_frames(self):
        # mapping_page_title_frame
        self.mapping_page_title_label.grid(row=0, column=0)
        # mapping_page_streams_frame
        self.record_button_label.grid(row=0, column=0)
        self.stream_button_label.grid(row=0, column=1)
        self.record_button_canvas.grid(row=1, column=0)
        self.stream_button_canvas.grid(row=1, column=1)
        # mapping_page_scenes_frame
        self.scene0_button_combobox.grid(row=0, column=0)
        self.scene1_button_combobox.grid(row=0, column=1)
        self.scene2_button_combobox.grid(row=0, column=2)
        self.scene3_button_combobox.grid(row=0, column=3)
        self.scene0_button_canvas.grid(row=1, column=0)
        self.scene1_button_canvas.grid(row=1, column=1)
        self.scene2_button_canvas.grid(row=1, column=2)
        self.scene3_button_canvas.grid(row=1, column=3)
        # mapping_page_script_frame
        self.script0_button_combobox.grid(row=0, column=0)
        self.script1_button_combobox.grid(row=0, column=1)
        self.script2_button_combobox.grid(row=0, column=2)
        self.script3_button_combobox.grid(row=0, column=3)
        self.script0_button_canvas.grid(row=1, column=0)
        self.script1_button_canvas.grid(row=1, column=1)
        self.script2_button_canvas.grid(row=1, column=2)
        self.script3_button_canvas.grid(row=1, column=3)
        # mapping_page_volumes_frame
        self.volume0_combobox.grid(row=0, column=0)
        self.volume1_combobox.grid(row=0, column=1)
        self.volume2_combobox.grid(row=0, column=2)
        self.volume3_combobox.grid(row=0, column=3)
        self.volume0_pot.grid(row=1, column=0, sticky="nsew")
        self.volume1_pot.grid(row=1, column=1, sticky="nsew")
        self.volume2_pot.grid(row=1, column=2, sticky="nsew")
        self.volume3_pot.grid(row=1, column=3, sticky="nsew")
        # mapping_page_bottom_frame
        self.back_to_online_button.grid(row=0, column=0, columnspan=2, sticky="w")

    def grid_mapping_page(self):
        # configure window
        self.title("StreamDeck - Mapping")
        self.geometry(f"{800}x{400}")

        # configure grid
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)
        self.reset_column_row_configure(column=1, row=4)

        # grid
        self.mapping_page_title_frame.grid(row=0, column=0, columnspan=2, sticky="nswe", padx=20, pady=(20, 5))
        self.mapping_page_streams_frame.grid(row=1, column=0, columnspan=2, sticky="nswe", padx=20, pady=(5, 5))
        self.mapping_page_scenes_frame.grid(row=2, column=0, sticky="nswe", padx=(20, 5), pady=(5, 5))
        self.mapping_page_script_frame.grid(row=2, column=1, sticky="nswe", padx=(5, 20), pady=(5, 5))
        self.mapping_page_volumes_frame.grid(row=3, column=0, columnspan=2, sticky="nswe", padx=20, pady=(5, 5))
        self.mapping_page_bottom_frame.grid(row=4, column=0, columnspan=2, sticky="nswe", padx=20, pady=(5, 20))

    def forget_mapping_page(self):
        self.mapping_page_title_frame.grid_forget()
        self.mapping_page_streams_frame.grid_forget()
        self.mapping_page_scenes_frame.grid_forget()
        self.mapping_page_script_frame.grid_forget()
        self.mapping_page_volumes_frame.grid_forget()
        self.mapping_page_bottom_frame.grid_forget()

    def load_mapping_page_parameters(self):
        self.var_combobox_scenes = self.sdc.get_scene_names()
        self.var_combobox_scripts = list(self.sdc.script.keys())
        self.var_combobox_volumes = self.sdc.get_volumes_names()

        self.scene0_button_combobox.configure(values=self.var_combobox_scenes)
        self.scene1_button_combobox.configure(values=self.var_combobox_scenes)
        self.scene2_button_combobox.configure(values=self.var_combobox_scenes)
        self.scene3_button_combobox.configure(values=self.var_combobox_scenes)
        self.script0_button_combobox.configure(values=self.var_combobox_scripts)
        self.script1_button_combobox.configure(values=self.var_combobox_scripts)
        self.script2_button_combobox.configure(values=self.var_combobox_scripts)
        self.script3_button_combobox.configure(values=self.var_combobox_scripts)
        self.volume0_combobox.configure(values=self.var_combobox_volumes)
        self.volume1_combobox.configure(values=self.var_combobox_volumes)
        self.volume2_combobox.configure(values=self.var_combobox_volumes)
        self.volume3_combobox.configure(values=self.var_combobox_volumes)
        self.scene0_button_combobox.set(value=self.sdc.mapping['B0'] if 'B0' in self.sdc.mapping.keys() else "")
        self.scene1_button_combobox.set(value=self.sdc.mapping['B1'] if 'B1' in self.sdc.mapping.keys() else "")
        self.scene2_button_combobox.set(value=self.sdc.mapping['B2'] if 'B2' in self.sdc.mapping.keys() else "")
        self.scene3_button_combobox.set(value=self.sdc.mapping['B3'] if 'B3' in self.sdc.mapping.keys() else "")
        self.script0_button_combobox.set(value=self.sdc.mapping['G0'] if 'G0' in self.sdc.mapping.keys() else "")
        self.script1_button_combobox.set(value=self.sdc.mapping['G1'] if 'G1' in self.sdc.mapping.keys() else "")
        self.script2_button_combobox.set(value=self.sdc.mapping['G2'] if 'G2' in self.sdc.mapping.keys() else "")
        self.script3_button_combobox.set(value=self.sdc.mapping['G3'] if 'G3' in self.sdc.mapping.keys() else "")
        self.volume0_combobox.set(value=self.sdc.mapping['P0'] if 'P0' in self.sdc.mapping.keys() else "")
        self.volume1_combobox.set(value=self.sdc.mapping['P1'] if 'P1' in self.sdc.mapping.keys() else "")
        self.volume2_combobox.set(value=self.sdc.mapping['P2'] if 'P2' in self.sdc.mapping.keys() else "")
        self.volume3_combobox.set(value=self.sdc.mapping['P3'] if 'P3' in self.sdc.mapping.keys() else "")

    def update_mapping_page_parameters(self):
        combobox_scenes = [
            ('B0', self.scene0_button_combobox, self.scene0_button_canvas),
            ('B1', self.scene1_button_combobox, self.scene1_button_canvas),
            ('B2', self.scene2_button_combobox, self.scene2_button_canvas),
            ('B3', self.scene3_button_combobox, self.scene3_button_canvas)
        ]
        combobox_scripts = [
            ('G0', self.script0_button_combobox, self.script0_button_canvas),
            ('G1', self.script1_button_combobox, self.script1_button_canvas),
            ('G2', self.script2_button_combobox, self.script2_button_canvas),
            ('G3', self.script3_button_combobox, self.script3_button_canvas)
        ]
        combobox_volumes = [
            ('P0', self.volume0_combobox, self.volume0_pot),
            ('P1', self.volume1_combobox, self.volume1_pot),
            ('P2', self.volume2_combobox, self.volume2_pot),
            ('P3', self.volume3_combobox, self.volume3_pot)
        ]

        for button, combobox, canvas in combobox_scenes:
            if combobox.get() in self.var_combobox_scenes:
                self.sdc.mapping[button] = combobox.get()
                canvas.config(bg="grey")
            else:
                canvas.config(bg="red")

        for button, combobox, canvas in combobox_scripts:
            if combobox.get() in self.var_combobox_scripts:
                self.sdc.mapping[button] = combobox.get()
                canvas.config(bg="grey")
            else:
                canvas.config(bg="red")

        for pot, combobox, canvas in combobox_volumes:
            if combobox.get() in self.var_combobox_volumes:
                self.sdc.mapping[pot] = combobox.get()

        if self.var_combobox_scenes != self.sdc.get_scene_names() or \
                self.var_combobox_scripts != list(self.sdc.script.keys()) or \
                self.var_combobox_volumes != self.sdc.get_volumes_names():
            self.load_mapping_page_parameters()

        if self.page == pages['mapping']:
            self.after(100, self.update_mapping_page_parameters)
    # -----------------------------------------------------------------------------------------------------------------

    # ------------------- Script Page Methods ------------------------------------------------------------------------
    def create_script_page(self):
        self.create_script_page_frames()
        self.create_script_page_widgets_in_frames()
        self.configure_script_page_frames()
        self.grid_script_page_widgets_in_frames()

    def create_script_page_frames(self):
        self.script_page_title_frame = customtkinter.CTkFrame(self)
        self.script_page_script_frame = customtkinter.CTkFrame(self)
        self.script_page_bottom_frame = customtkinter.CTkFrame(self)

    def create_script_page_widgets_in_frames(self):
        # script_page_title_frame
        self.script_page_title_label = customtkinter.CTkLabel(self.script_page_title_frame, text="Script Page",
                                                              font=customtkinter.CTkFont(size=25, weight="bold"))
        # script_page_script_frame
        self.script_list_combobox = customtkinter.CTkComboBox(self.script_page_script_frame, values=[""], width=200)
        self.script_name_entry = customtkinter.CTkEntry(self.script_page_script_frame, width=200)
        self.script_scrollable_frame = customtkinter.CTkScrollableFrame(self.script_page_script_frame, width=100,
                                                                        height=200)
        self.add_step_button = customtkinter.CTkButton(self.script_page_script_frame, text="Add Step",
                                                       command=self.add_empty_step, width=90)
        self.delete_step_button = customtkinter.CTkButton(self.script_page_script_frame, text="Delete Step",
                                                          command=self.delete_step, width=90)
        self.save_script_button = customtkinter.CTkButton(self.script_page_script_frame, text="Save Script",
                                                          command=self.save_script, width=90)
        self.delete_script_button = customtkinter.CTkButton(self.script_page_script_frame, text="Delete Script",
                                                            command=self.delete_script, width=90)
        self.clear_script_button = customtkinter.CTkButton(self.script_page_script_frame, text="Clear Script",
                                                           command=self.clear_script, width=90)
        # script_page_bottom_frame
        self.back_to_online_button = customtkinter.CTkButton(self.script_page_bottom_frame, text="Back to Online",
                                                             command=self.from_script_page_to_online_page_event)

    def configure_script_page_frames(self):
        # script_page_title_frame
        self.script_page_title_frame.grid_rowconfigure(0, weight=1)
        self.script_page_title_frame.grid_columnconfigure(0, weight=1)
        # script_page_script_frame
        self.script_page_script_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.script_page_script_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.script_scrollable_frame.grid_rowconfigure((0, 1), weight=1)
        # script_page_bottom_frame
        self.script_page_bottom_frame.grid_rowconfigure(0, weight=1)
        self.script_page_bottom_frame.grid_columnconfigure(0, weight=1)
    
    def grid_script_page_widgets_in_frames(self):
        # script_page_title_frame
        self.script_page_title_label.grid(row=0, column=0)
        # script_page_script_frame
        self.script_list_combobox.grid(row=0, column=0)
        self.script_name_entry.grid(row=0, column=1)
        self.delete_step_button.grid(row=1, column=2)
        self.add_step_button.grid(row=2, column=2)
        self.clear_script_button.grid(row=3, column=2)
        self.delete_script_button.grid(row=4, column=2)
        self.save_script_button.grid(row=5, column=2)
        self.script_scrollable_frame.grid(row=1, column=0, columnspan=2, rowspan=5, pady=10, padx=10, sticky="nswe")
        # script_page_bottom_frame
        self.back_to_online_button.grid(row=0, column=0, sticky="w", padx=10)

    def grid_script_page(self):
        # configure window
        self.title("StreamDeck - Script")
        self.geometry(f"{800}x{400}")

        # configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.reset_column_row_configure(column=0, row=2)
        
        # grid
        self.script_page_title_frame.grid(row=0, column=0, sticky="nswe", padx=20, pady=(20, 5))
        self.script_page_script_frame.grid(row=1, column=0, sticky="nswe", padx=20, pady=(5, 5))
        self.script_page_bottom_frame.grid(row=2, column=0, sticky="nswe", padx=20, pady=(5, 20))
        
    def forget_script_page(self):
        self.script_page_title_frame.grid_forget()
        self.script_page_script_frame.grid_forget()
        self.script_page_bottom_frame.grid_forget()

    def add_empty_step(self):
        self.add_step("", "")

    def add_step(self, command, value):
        combobox = customtkinter.CTkComboBox(self.script_scrollable_frame, values=scripting.command_list)
        entry = customtkinter.CTkEntry(self.script_scrollable_frame)
        combobox.grid(row=len(self.current_script_combobox_list), column=0, padx=(0, 20), pady=5, sticky="")
        entry.grid(row=len(self.current_script_entry_list), column=1, padx=(20, 0), pady=5, sticky="")
        combobox.set(command)
        entry.insert(0, value)
        self.current_script_combobox_list.append(combobox)
        self.current_script_entry_list.append(entry)
        scripting.save_scripts(self.sdc.script)

    def delete_step(self):
        if len(self.current_script_combobox_list) > 0:
            self.current_script_combobox_list[-1].destroy()
            self.current_script_entry_list[-1].destroy()
            self.current_script_combobox_list.pop()
            self.current_script_entry_list.pop()
            scripting.save_scripts(self.sdc.script)

    def clear_script(self):
        for widget in self.script_scrollable_frame.winfo_children():
            widget.destroy()
        self.current_script_combobox_list = []
        self.current_script_entry_list = []

    def save_script(self):
        script_name = self.script_name_entry.get()
        if script_name != "":
            script = []
            for i in range(len(self.current_script_combobox_list)):
                command = self.current_script_combobox_list[i].get()
                value = self.current_script_entry_list[i].get()
                script.append(f"{command} {value}")
            self.sdc.script[script_name] = script
            self.load_script_page_parameters()
            self.script_list_combobox.set(value=script_name)
            self.script_selected = script_name
            scripting.save_scripts(self.sdc.script)

    def delete_script(self):
        script_name = self.script_name_entry.get()
        if script_name != "":
            del self.sdc.script[script_name]
            self.load_script_page_parameters()
            self.script_list_combobox.set(value="")
            self.script_selected = ""
            scripting.save_scripts(self.sdc.script)

            keys_to_remove = []
            for key, value in self.sdc.mapping.items():
                if value == script_name:
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del self.sdc.mapping[key]
            self.sdc.save_settings()

            self.clear_script()
            self.script_name_entry.insert(0, "")

    def load_script_page_parameters(self):
        script_list = self.sdc.script.keys()
        self.script_list_combobox.configure(values=script_list)
        self.script_list_combobox.set(value="")
        self.script_selected = self.script_list_combobox.get()
    
    def update_script_page_parameters(self):
        if self.script_list_combobox.get() != self.script_selected:
            self.script_selected = self.script_list_combobox.get()
            self.script_name_entry.delete(0, tk.END)
            self.script_name_entry.insert(0, self.script_selected)
            for widget in self.script_scrollable_frame.winfo_children():
                widget.destroy()
            self.current_script_combobox_list = []
            self.current_script_entry_list = []
            for step in self.sdc.script[self.script_selected]:
                command = step.split(" ")[0]
                value = step.split(" ")[1]
                self.add_step(command, value)

        if self.page == pages['script']:
            self.after(100, self.update_script_page_parameters)
    # -----------------------------------------------------------------------------------------------------------------
    
    # ------------------- Change Page Methods -------------------------------------------------------------------------
    def from_connection_page_to_online_page_event(self):
        self.page = pages['online']
        self.forget_connection_page()
        self.create_online_page()
        self.grid_online_page()
        self.load_online_page_parameters()
        self.after(100, self.update_online_page_parameters)

    def from_online_page_to_connection_page_event(self):
        self.page = pages['connection']
        self.forget_online_page()
        self.create_connection_page()
        self.grid_connection_page()
        self.after(500, self.reset_streamdeck_controller)

    def from_online_page_to_mapping_page_event(self):
        self.page = pages['mapping']
        self.forget_online_page()
        self.create_mapping_page()
        self.grid_mapping_page()
        self.load_mapping_page_parameters()
        self.after(100, self.update_mapping_page_parameters)

    def from_mapping_page_to_online_page_event(self):
        self.page = pages['online']
        self.sdc.save_settings()
        self.forget_mapping_page()
        self.create_online_page()
        self.grid_online_page()
        self.load_online_page_parameters()
        self.after(100, self.update_online_page_parameters)
        
    def from_online_page_to_script_page_event(self):
        self.page = pages['script']
        self.forget_online_page()
        self.create_script_page()
        self.grid_script_page()
        self.load_script_page_parameters()
        self.after(100, self.update_script_page_parameters)
        
    def from_script_page_to_online_page_event(self):
        self.page = pages['online']
        self.forget_script_page()
        self.create_online_page()
        self.grid_online_page()
        self.load_online_page_parameters()
        self.after(100, self.update_online_page_parameters)
    # -----------------------------------------------------------------------------------------------------------------

    # ------------------- Get Data Methods ----------------------------------------------------------------------------
    def get_dict_connection_page_data(self):
        obs_data = {'host': self.host_entry_var.get(),
                    'port': self.port_entry_var.get(),
                    'password': self.password_entry_var.get()}
        serial_data = {'com_port': self.com_port_entry_var.get(),
                       'baud_rate': int(self.baud_rate_var.get())}
        return {'obs_data': obs_data, 'serial_data': serial_data}

    def get_dict_data(self):
        settings = {'connection_page': self.get_dict_connection_page_data()}
        return settings
    # -----------------------------------------------------------------------------------------------------------------

    # ------------------- Save/Load Methods ---------------------------------------------------------------------------
    def save_settings(self):
        with open('settings.json', 'w') as file:
            json.dump(self.get_dict_data(), file)

    def load_settings(self):
        try:
            with open('settings.json', 'r') as file:
                settings = json.load(file)
                self.host_entry_var.set(settings['connection_page']['obs_data']['host'])
                self.port_entry_var.set(settings['connection_page']['obs_data']['port'])
                self.password_entry_var.set(settings['connection_page']['obs_data']['password'])
                self.com_port_entry_var.set(settings['connection_page']['serial_data']['com_port'])
                self.baud_rate_var.set(str(settings['connection_page']['serial_data']['baud_rate']))
        except FileNotFoundError as error:
            print(error)
    # -----------------------------------------------------------------------------------------------------------------

    def reset_column_row_configure(self, column, row):
        for i in range(row+1, 10):
            self.grid_rowconfigure(i, weight=0)
        for i in range(column+1, 10):
            self.grid_columnconfigure(i, weight=0)

    def reset_streamdeck_controller(self):
        self.sdc.ser.close()
        self.sdc = None

    def on_close(self):
        self.save_settings()
        if self.sdc is not None:
            self.sdc.ws.disconnect()
            self.sdc.ser.close()
            self.sdc.destroy()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
