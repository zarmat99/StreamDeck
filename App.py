# implementation task:
# - aggiungere il metodo update generale che dipende dalla pagina corrente in cui ci si trova

# to do:
# - aggiungere la current scene illuminata e lo script illuminato mentre è in esecuzione

# to fix
# - corregere il bug che non cambia colore il pot del volume se questo non è mappato

import tkinter as tk
import tkinter.messagebox
import customtkinter
import PotentiometerWidget
import StreamDeckController
import json

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"
pages = {"connection": 0, "online": 1}


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        # ------------------- Variables -------------------------------------------------------------------------------
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
        self.host_entry_var = tkinter.StringVar()
        self.port_entry_var = tkinter.StringVar()
        self.com_port_entry_var = tkinter.StringVar()
        self.password_entry_var = tkinter.StringVar()
        self.baud_rate_var = tkinter.StringVar()
        # -------------------------------------------------------------------------------------------------------------

        # ------------------- Init ------------------------------------------------------------------------------------
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<Configure>", self.resize)
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
        # online_page_bottom_frame
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
        self.connection_info_button.grid(row=0, column=0, sticky="e")

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
        canvas_scene_list = [self.scene0_button_canvas, self.scene1_button_canvas, self.scene2_button_canvas,
                             self.scene3_button_canvas]
        label_scene_list = [self.scene0_button_label, self.scene1_button_label, self.scene2_button_label,
                            self.scene3_button_label]

        if self.sdc.get_record_state():
            self.record_button_canvas.config(bg="yellow")
        else:
            self.record_button_canvas.config(bg="red")
        if self.sdc.get_stream_state():
            self.stream_button_canvas.config(bg="yellow")
        else:
            self.stream_button_canvas.config(bg="red")

        for canvas in canvas_scene_list:
            canvas.configure(bg="gray")
        index_to_highlight = next(
            (i for i, label in enumerate(label_scene_list) if self.sdc.get_current_scene() == label.cget("text")), None)
        if index_to_highlight is not None:
            canvas_scene_list[index_to_highlight].configure(bg="yellow")

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

    # ------------------- Change Page Methods -------------------------------------------------------------------------
    def from_connection_page_to_online_page_event(self):
        self.page = pages['online']
        self.forget_connection_page()
        self.create_online_page()
        self.grid_online_page()
        self.load_online_page_parameters()
        self.after(100, self.update_online_page_parameters)

    def from_online_page_to_connection_page_event(self):
        self.forget_online_page()
        self.create_connection_page()
        self.grid_connection_page()
        self.page = pages['connection']
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
            print("settings.json saved successfully!")

    def load_settings(self):
        try:
            with open('settings.json', 'r') as file:
                settings = json.load(file)
                print("settings.json loaded successfully!")
                self.host_entry_var.set(settings['connection_page']['obs_data']['host'])
                self.port_entry_var.set(settings['connection_page']['obs_data']['port'])
                self.password_entry_var.set(settings['connection_page']['obs_data']['password'])
                self.com_port_entry_var.set(settings['connection_page']['serial_data']['com_port'])
                self.baud_rate_var.set(str(settings['connection_page']['serial_data']['baud_rate']))
        except FileNotFoundError:
            print(FileNotFoundError)
    # -----------------------------------------------------------------------------------------------------------------

    def reset_column_row_configure(self, column, row):
        for i in range(row+1, 10):
            self.grid_rowconfigure(i, weight=0)
        for i in range(column+1, 10):
            self.grid_columnconfigure(i, weight=0)

    def on_close(self):
        self.save_settings()
        self.sdc.destroy()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
