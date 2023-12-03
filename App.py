import tkinter
import tkinter.messagebox
import customtkinter

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # ------------------- Variables -------------------------------------------------------------------------------
        self.page_2_title_label = None
        self.page_2_title_frame = None
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
        self.host_entry_var = tkinter.StringVar()
        self.port_entry_var = tkinter.StringVar()
        self.com_port_entry_var = tkinter.StringVar()
        self.password_entry_var = tkinter.StringVar()
        self.baud_rate_var = tkinter.StringVar()
        # -------------------------------------------------------------------------------------------------------------

        # ------------------- Init ------------------------------------------------------------------------------------
        self.create_connection_page()
        self.create_page_2()
        self.grid_connection_page()
        # -------------------------------------------------------------------------------------------------------------
        self.back_button = customtkinter.CTkButton(self, text="Back", command=self.back_button_event)

    # ----------------------------------------- M E T H O D S ---------------------------------------------------------

    # ------------------- Connection Page Methods ---------------------------------------------------------------------
    def create_connection_page(self):
        print("ciao")
        self.create_connection_page_frames()
        self.create_connection_page_widgets_in_frames()
        self.configure_connection_page_frames()
        self.grid_connection_page_widgets_in_frames()

    def create_connection_page_frames(self):
        self.connection_page_title_frame = customtkinter.CTkFrame(self)
        print(self.connection_page_title_frame)
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
                                                      command=self.connect_event)

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
    # -----------------------------------------------------------------------------------------------------------------

    # ------------------- Page 2 Methods ------------------------------------------------------------------------------
    def create_page_2(self):
        self.create_page_2_frames()
        self.create_page_2_widgets_in_frames()
        self.configure_page_2_frames()
        self.grid_page_2_widgets_in_frames()

    def create_page_2_frames(self):
        self.page_2_title_frame = customtkinter.CTkFrame(self)

    def configure_page_2_frames(self):
        # page_2_title_frame
        self.page_2_title_frame.grid_rowconfigure(0, weight=1)
        self.page_2_title_frame.grid_columnconfigure(0, weight=1)

    def create_page_2_widgets_in_frames(self):
        # page_2_title_frame
        self.page_2_title_label = customtkinter.CTkLabel(self.page_2_title_frame,
                                                         text="Page 2",
                                                         font=customtkinter.CTkFont(size=25, weight="bold"))

    def grid_page_2_widgets_in_frames(self):
        # page_2_title_frame
        self.page_2_title_label.grid(row=0, column=0)

    def grid_page_2(self):
        # configure window
        self.title("StreamDeck - Page 2")
        self.geometry(f"{800}x{400}")

        # configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # grid
        self.page_2_title_frame.grid(row=0, column=0, sticky="nswe", padx=20, pady=(20, 5))

    def forget_page_2(self):
        self.page_2_title_frame.grid_forget()
    # -----------------------------------------------------------------------------------------------------------------

    def connect_event(self):
        self.forget_connection_page()
        self.grid_page_2()

    def back_button_event(self):
        self.forget_page_2()
        self.grid_connection_page()


if __name__ == "__main__":
    app = App()
    app.mainloop()
