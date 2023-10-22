import tkinter
import tkinter.messagebox
import customtkinter

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.a = 0
        # ------------------- Connection Page -------------------------------------------------------------------------
        # create page title label
        self.connection_page_title_label = customtkinter.CTkLabel(self, text="Connection Page",
                                                                  font=customtkinter.CTkFont(size=25, weight="bold"))

        # create obs configurations frame
        self.obs_conf_frame = customtkinter.CTkFrame(self)
        self.obs_conf_frame.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.obs_conf_frame.grid_columnconfigure((0, 1), weight=1)
        #   row 0 -> frame label
        self.obs_configuration_label = customtkinter.CTkLabel(self.obs_conf_frame, text="OBS Configurations",
                                                 font=customtkinter.CTkFont(size=20))
        self.obs_configuration_label.grid(row=0, column=0, columnspan=2)
        #   row 1 -> host (label + entry)
        #       host label
        self.host_label = customtkinter.CTkLabel(self.obs_conf_frame, text="Host",
                                                 font=customtkinter.CTkFont(size=15))
        self.host_label.grid(row=1, column=0)
        #       host entry
        host_entry_var = tkinter.StringVar()
        self.host_entry = customtkinter.CTkEntry(self.obs_conf_frame, textvariable=host_entry_var)
        self.host_entry.grid(row=1, column=1)
        #   row 2 -> port (label + entry)
        #       port label
        self.port_label = customtkinter.CTkLabel(self.obs_conf_frame, text="Port",
                                                 font=customtkinter.CTkFont(size=15))
        self.port_label.grid(row=2, column=0)
        #       port entry
        port_entry_var = tkinter.StringVar()
        self.port_entry = customtkinter.CTkEntry(self.obs_conf_frame, textvariable=port_entry_var)
        self.port_entry.grid(row=2, column=1)
        #   row 3 -> password (label + entry)
        #       password label
        self.password_label = customtkinter.CTkLabel(self.obs_conf_frame, text="Password",
                                                     font=customtkinter.CTkFont(size=15))
        self.password_label.grid(row=3, column=0)
        #       password entry
        password_entry_var = tkinter.StringVar()
        self.password_entry = customtkinter.CTkEntry(self.obs_conf_frame, textvariable=password_entry_var)
        self.password_entry.grid(row=3, column=1)

        # create streamdeck configuration frame
        self.streamdeck_conf_frame = customtkinter.CTkFrame(self)
        self.streamdeck_conf_frame.grid_rowconfigure((0, 1, 2), weight=1)
        self.streamdeck_conf_frame.grid_columnconfigure((0, 1), weight=1)
        #   row 0 -> frame label
        self.obs_configuration_label = customtkinter.CTkLabel(self.streamdeck_conf_frame,
                                                              text="StreamDeck Configurations",
                                                              font=customtkinter.CTkFont(size=20))
        self.obs_configuration_label.grid(row=0, column=0, columnspan=2)
        #   row 1 -> com port (label + entry)
        #       com port label
        self.com_port_label = customtkinter.CTkLabel(self.streamdeck_conf_frame, text="Com Port",
                                                     font=customtkinter.CTkFont(size=15))
        self.com_port_label.grid(row=1, column=0)
        #       com port entry
        com_port_var = tkinter.StringVar()
        self.com_port_entry = customtkinter.CTkEntry(self.streamdeck_conf_frame, textvariable=com_port_var)
        self.com_port_entry.grid(row=1, column=1)
        #   row 2 -> baud rate (label + entry)
        #       baud rate label
        self.baud_rate_label = customtkinter.CTkLabel(self.streamdeck_conf_frame, text="Baud Rate",
                                                      font=customtkinter.CTkFont(size=15))
        self.baud_rate_label.grid(row=2, column=0)
        #       port entry
        baud_rate_var = tkinter.StringVar()
        self.baud_rate_entry = customtkinter.CTkEntry(self.streamdeck_conf_frame, textvariable=baud_rate_var)
        self.baud_rate_entry.grid(row=2, column=1)

        # create Connect Button
        self.connect_button = customtkinter.CTkButton(self, text="Connect",
                                                      command=self.connect_event)
        # -------------------------------------------------------------------------------------------------------------

        # ------------------- Page 2 ----------------------------------------------------------------------------------
        self.back_button = customtkinter.CTkButton(self, text="Back",
                                                      command=self.back_button_event)
        # -------------------------------------------------------------------------------------------------------------

        # ------------------- Init ------------------------------------------------------------------------------------
        self.connection_page_grid()

    def connection_page_grid(self):
        # configure window
        self.title("StreamDeck - Connection")
        self.geometry(f"{800}x{400}")

        # configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure((1, 2), weight=1)
        self.grid_rowconfigure(3, weight=0)

        # grid
        self.connection_page_title_label.grid(row=0, column=0, columnspan=2, pady=10)
        self.obs_conf_frame.grid(row=1, column=0, columnspan=2, sticky="nswe", padx=20, pady=(0, 10))
        self.streamdeck_conf_frame.grid(row=2, column=0, columnspan=2, sticky="nswe", padx=20, pady=(10, 10))
        self.connect_button.grid(row=3, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="e")

    def connection_page_forget(self):
        self.obs_conf_frame.grid_forget()
        self.streamdeck_conf_frame.grid_forget()
        self.connection_page_title_label.grid_forget()
        self.connect_button.grid_forget()

    def page_2_grid(self):
        # configure window
        self.title("StreamDeck - Page 2")
        self.geometry(f"{800}x{400}")

        # configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # grid
        self.back_button.grid(row=0, column=0)

    def page_2_forget(self):
        self.back_button.grid_forget()

    def connect_event(self):
        self.connection_page_forget()
        self.page_2_grid()

    def back_button_event(self):
        self.page_2_forget()
        self.connection_page_grid()


if __name__ == "__main__":
    app = App()
    app.mainloop()