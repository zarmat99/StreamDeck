"""Connection setup for OBS WebSocket and the hardware serial link."""

from __future__ import annotations

from typing import Tuple

import customtkinter

from ..base_page import BasePage
from ..helpers import (
    INVALID_SERIAL_PORT_VALUES,
    validate_obs_values,
    validate_serial_values,
)


class ConnectionPage(BasePage):
    """Configure and independently connect the two external services."""

    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent

        connection = self.app.config.settings.setdefault("connection", {})
        obs_data = connection.setdefault("obs_data", {})
        serial_data = connection.setdefault("serial_data", {})
        self.vars = {
            "obs_data": {
                "host": customtkinter.StringVar(
                    value=str(obs_data.get("host") or "localhost")
                ),
                "port": customtkinter.StringVar(
                    value=str(obs_data.get("port") or "4455")
                ),
                "password": customtkinter.StringVar(
                    value=str(obs_data.get("password") or "")
                ),
            },
            "serial_data": {
                "com_port": customtkinter.StringVar(
                    value=str(serial_data.get("com_port") or "")
                ),
                "baud_rate": customtkinter.StringVar(
                    value=str(serial_data.get("baud_rate") or "9600")
                ),
            },
            "auto_connect": customtkinter.BooleanVar(
                value=bool(connection.get("auto_connect", False))
            ),
        }

        self.obs_connected = False
        self.serial_connected = False
        self.refresh_timer = None
        self._obs_operation = False
        self._serial_operation = False

        self.add_on_show_callback(self.on_show)
        self.add_on_hide_callback(self.on_hide)

    def change_window_name(self):
        self.parent.title("StreamDeck Control - Connections")

    def create_widgets(self):
        self.add_title("Connections")

        body = self.frames["body"]
        self.labels["obs_configuration"] = customtkinter.CTkLabel(
            body,
            text="OBS WebSocket",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.labels["host"] = customtkinter.CTkLabel(body, text="Host")
        self.entries["host"] = customtkinter.CTkEntry(
            body,
            textvariable=self.vars["obs_data"]["host"],
            placeholder_text="localhost",
        )
        self.labels["port"] = customtkinter.CTkLabel(body, text="Port")
        self.entries["port"] = customtkinter.CTkEntry(
            body, textvariable=self.vars["obs_data"]["port"], placeholder_text="4455"
        )
        self.labels["password"] = customtkinter.CTkLabel(body, text="Password")
        self.entries["password"] = customtkinter.CTkEntry(
            body, textvariable=self.vars["obs_data"]["password"], show="*"
        )
        self.buttons["connect_obs"] = customtkinter.CTkButton(
            body, text="Connect to OBS", command=self.connect_obs_button_click
        )
        self.labels["obs_status"] = customtkinter.CTkLabel(
            body, text="Disconnected", text_color="#e05d5d"
        )

        self.labels["streamdeck_configuration"] = customtkinter.CTkLabel(
            body,
            text="Hardware device",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.labels["com_port"] = customtkinter.CTkLabel(body, text="Serial port")
        self.comboboxes["com_port"] = customtkinter.CTkComboBox(
            body,
            values=["Select COM port"],
            variable=self.vars["serial_data"]["com_port"],
            command=self.com_port_selected,
        )
        self.buttons["refresh_ports"] = customtkinter.CTkButton(
            body, text="Refresh", width=76, command=self.refresh_com_ports
        )
        self.labels["baud_rate"] = customtkinter.CTkLabel(body, text="Baud rate")
        self.comboboxes["baud_rate"] = customtkinter.CTkComboBox(
            body,
            values=["9600", "19200", "38400", "57600", "115200"],
            variable=self.vars["serial_data"]["baud_rate"],
        )
        self.buttons["connect_serial"] = customtkinter.CTkButton(
            body, text="Connect hardware", command=self.connect_serial_button_click
        )
        self.labels["serial_status"] = customtkinter.CTkLabel(
            body, text="Disconnected", text_color="#e05d5d"
        )

        self.switches["auto_connect"] = customtkinter.CTkSwitch(
            self.frames["bottom"],
            text="Connect automatically at startup",
            variable=self.vars["auto_connect"],
            command=self.auto_connect_toggled,
        )
        self.buttons["continue"] = customtkinter.CTkButton(
            self.frames["bottom"],
            text="Open dashboard",
            command=self.continue_to_online,
        )
        self.add_status()

    def configure_widgets(self):
        body = self.frames["body"]
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=3)
        body.grid_columnconfigure(2, weight=1)
        self.refresh_com_ports()

    def grid_widgets(self):
        row = 0
        self.labels["obs_configuration"].grid(
            row=row, column=0, columnspan=3, sticky="w", padx=20, pady=(20, 10)
        )
        for label, entry in (
            ("host", "host"),
            ("port", "port"),
            ("password", "password"),
        ):
            row += 1
            self.labels[label].grid(row=row, column=0, sticky="e", padx=(20, 5), pady=5)
            self.entries[entry].grid(row=row, column=1, sticky="ew", padx=5, pady=5)

        row += 1
        self.buttons["connect_obs"].grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 5)
        )
        self.labels["obs_status"].grid(row=row, column=2, sticky="w", padx=5, pady=5)

        row += 1
        self.labels["streamdeck_configuration"].grid(
            row=row, column=0, columnspan=3, sticky="w", padx=20, pady=(24, 10)
        )
        row += 1
        self.labels["com_port"].grid(
            row=row, column=0, sticky="e", padx=(20, 5), pady=5
        )
        self.comboboxes["com_port"].grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        self.buttons["refresh_ports"].grid(
            row=row, column=2, sticky="w", padx=5, pady=5
        )
        row += 1
        self.labels["baud_rate"].grid(
            row=row, column=0, sticky="e", padx=(20, 5), pady=5
        )
        self.comboboxes["baud_rate"].grid(
            row=row, column=1, sticky="ew", padx=5, pady=5
        )
        row += 1
        self.buttons["connect_serial"].grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 5)
        )
        self.labels["serial_status"].grid(row=row, column=2, sticky="w", padx=5, pady=5)

        self.switches["auto_connect"].pack(side="left", padx=20, pady=10)
        self.buttons["continue"].pack(side="right", padx=20, pady=10)

    def on_show(self):
        self.update_connection_status()
        if self.refresh_timer:
            self.after_cancel(self.refresh_timer)
        self.refresh_timer = self.after(5000, self.auto_refresh_ports)

    def on_hide(self):
        if self.refresh_timer:
            self.after_cancel(self.refresh_timer)
            self.refresh_timer = None

    def auto_refresh_ports(self):
        self.refresh_timer = None
        self.refresh_com_ports()
        if self.app.current_page == "connection":
            self.refresh_timer = self.after(5000, self.auto_refresh_ports)

    def refresh_com_ports(self):
        current = self.vars["serial_data"]["com_port"].get().split(" ", 1)[0]
        try:
            available = list(self.app.serial.list_ports())
        except Exception as exc:
            self.app.logger.error(f"Could not enumerate serial ports: {exc}")
            available = []

        values = [f"{port} ({description})" for port, description in available]
        if not values:
            values = ["No COM ports available"]
        self.comboboxes["com_port"].configure(values=values)

        available_names = [str(port) for port, _description in available]
        if current in available_names:
            self.vars["serial_data"]["com_port"].set(current)
        elif available_names and current in INVALID_SERIAL_PORT_VALUES:
            self.vars["serial_data"]["com_port"].set(available_names[0])
        elif not available_names and not current:
            self.vars["serial_data"]["com_port"].set("No COM ports available")

    def com_port_selected(self, selection):
        if selection and selection not in INVALID_SERIAL_PORT_VALUES:
            self.vars["serial_data"]["com_port"].set(selection.split(" ", 1)[0])

    def _save_obs_values(self) -> Tuple[str, int]:
        host, port = validate_obs_values(
            self.vars["obs_data"]["host"].get(),
            self.vars["obs_data"]["port"].get(),
        )
        data = self.app.config.settings["connection"]["obs_data"]
        data.update(
            host=host,
            port=str(port),
            password=self.vars["obs_data"]["password"].get(),
        )
        if self.app.config.save_settings() is False:
            raise OSError("Could not save OBS connection settings.")
        return host, port

    def _save_serial_values(self) -> Tuple[str, int]:
        port, baud = validate_serial_values(
            self.vars["serial_data"]["com_port"].get(),
            self.vars["serial_data"]["baud_rate"].get(),
        )
        data = self.app.config.settings["connection"]["serial_data"]
        data.update(com_port=port, baud_rate=str(baud))
        if self.app.config.save_settings() is False:
            raise OSError("Could not save serial connection settings.")
        return port, baud

    def connect_obs_button_click(self):
        if self._obs_operation:
            return
        if self.app.obs.is_connected():
            self._disconnect_obs()
            return
        self._begin_obs_connection()

    def _begin_obs_connection(self, *, automatic: bool = False):
        try:
            host, port = self._save_obs_values()
        except (ValueError, OSError) as exc:
            self.show_status(str(exc), "#e05d5d")
            return

        self.app.obs.host = host
        self.app.obs.port = port
        self.app.obs.password = self.vars["obs_data"]["password"].get()
        self._obs_operation = True
        self.labels["obs_status"].configure(text="Connecting...", text_color="#e2a93b")
        self.buttons["connect_obs"].configure(state="disabled")
        self.app.submit_background(
            self.app.obs.connect,
            self._update_obs_status,
            self._obs_error,
            description="OBS connection",
        )
        if automatic:
            self.show_status("Connecting to configured services...", "#e2a93b")

    def _disconnect_obs(self):
        self._obs_operation = True
        self.labels["obs_status"].configure(
            text="Disconnecting...", text_color="#e2a93b"
        )
        self.buttons["connect_obs"].configure(state="disabled")
        self.app.submit_background(
            lambda: (self.app.obs.disconnect(), True)[1],
            lambda _result: self._update_obs_status(False, disconnected=True),
            self._obs_error,
            description="OBS disconnection",
        )

    def _obs_error(self, error):
        self._obs_operation = False
        self._update_obs_status(False)
        self.show_status(f"OBS connection error: {error}", "#e05d5d")

    def _update_obs_status(self, success, *, disconnected: bool = False):
        self._obs_operation = False
        self.obs_connected = bool(success and self.app.obs.is_connected())
        if self.obs_connected:
            self.labels["obs_status"].configure(text="Connected", text_color="#4caf6a")
            self.buttons["connect_obs"].configure(text="Disconnect", state="normal")
            password = self.vars["obs_data"]["password"].get()
            if password and not self.app.config.credential_persistence_available:
                self.show_status(
                    "OBS connected. The password is kept only for this session "
                    "because the OS credential store is unavailable.",
                    "#e2a93b",
                )
            else:
                self.show_status("OBS connected.", "#4caf6a")
        else:
            label = "Disconnected" if disconnected else "Connection failed"
            self.labels["obs_status"].configure(text=label, text_color="#e05d5d")
            self.buttons["connect_obs"].configure(text="Connect to OBS", state="normal")
            if not disconnected:
                self.show_status(
                    "Could not reach OBS. Check that OBS WebSocket is enabled and the credentials are correct.",
                    "#e05d5d",
                )
        self.update_continue_button()

    def connect_serial_button_click(self):
        if self._serial_operation:
            return
        if self.app.serial.is_connected():
            self._disconnect_serial()
            return
        self._begin_serial_connection()

    def _begin_serial_connection(self, *, automatic: bool = False):
        try:
            port, baud = self._save_serial_values()
        except (ValueError, OSError) as exc:
            self.show_status(str(exc), "#e05d5d")
            return

        self.app.serial.port = port
        self.app.serial.baud_rate = baud
        self._serial_operation = True
        self.labels["serial_status"].configure(
            text="Connecting...", text_color="#e2a93b"
        )
        self.buttons["connect_serial"].configure(state="disabled")
        self.app.submit_background(
            self.app.serial.connect,
            self._update_serial_status,
            self._serial_error,
            description="hardware connection",
        )
        if automatic:
            self.show_status("Connecting to configured services...", "#e2a93b")

    def _disconnect_serial(self):
        self._serial_operation = True
        self.labels["serial_status"].configure(
            text="Disconnecting...", text_color="#e2a93b"
        )
        self.buttons["connect_serial"].configure(state="disabled")
        self.app.submit_background(
            lambda: (self.app.serial.disconnect(), True)[1],
            lambda _result: self._update_serial_status(False, disconnected=True),
            self._serial_error,
            description="hardware disconnection",
        )

    def _serial_error(self, error):
        self._serial_operation = False
        self._update_serial_status(False)
        self.show_status(f"Hardware connection error: {error}", "#e05d5d")

    def _update_serial_status(self, success, *, disconnected: bool = False):
        self._serial_operation = False
        self.serial_connected = bool(success and self.app.serial.is_connected())
        if self.serial_connected:
            self.labels["serial_status"].configure(
                text="Connected", text_color="#4caf6a"
            )
            self.buttons["connect_serial"].configure(text="Disconnect", state="normal")
            self.show_status("Hardware connected.", "#4caf6a")
        else:
            label = "Disconnected" if disconnected else "Connection failed"
            self.labels["serial_status"].configure(text=label, text_color="#e05d5d")
            self.buttons["connect_serial"].configure(
                text="Connect hardware", state="normal"
            )
            if not disconnected:
                self.show_status(
                    "Could not open the serial device. Check the port and close other programs using it.",
                    "#e05d5d",
                )
        self.update_continue_button()

    def start_auto_connect(self):
        """Connect each configured service once, without blocking the UI."""
        if not self.app.obs.is_connected() and not self._obs_operation:
            self._begin_obs_connection(automatic=True)
        if not self.app.serial.is_connected() and not self._serial_operation:
            self._begin_serial_connection(automatic=True)

    def update_continue_button(self):
        both_connected = self.obs_connected and self.serial_connected
        self.buttons["continue"].configure(
            text="Open dashboard" if both_connected else "Open dashboard offline",
            state="normal",
        )

    def update_connection_status(self):
        self.obs_connected = bool(self.app.obs and self.app.obs.is_connected())
        self.serial_connected = bool(self.app.serial and self.app.serial.is_connected())
        self.labels["obs_status"].configure(
            text="Connected" if self.obs_connected else "Disconnected",
            text_color="#4caf6a" if self.obs_connected else "#e05d5d",
        )
        self.buttons["connect_obs"].configure(
            text="Disconnect" if self.obs_connected else "Connect to OBS",
            state="normal" if not self._obs_operation else "disabled",
        )
        self.labels["serial_status"].configure(
            text="Connected" if self.serial_connected else "Disconnected",
            text_color="#4caf6a" if self.serial_connected else "#e05d5d",
        )
        self.buttons["connect_serial"].configure(
            text="Disconnect" if self.serial_connected else "Connect hardware",
            state="normal" if not self._serial_operation else "disabled",
        )
        self.update_continue_button()

    def update_config_from_ui(self):
        """Validate and persist both connection groups."""
        self._save_obs_values()
        self._save_serial_values()

    def auto_connect_toggled(self):
        connection = self.app.config.settings.setdefault("connection", {})
        connection["auto_connect"] = bool(self.vars["auto_connect"].get())
        if self.app.config.save_settings() is False:
            self.show_status("Could not save the auto-connect preference.", "#e05d5d")

    def continue_to_online(self):
        # Navigation remains available offline so mappings/settings are never
        # hidden behind unavailable external services.
        self.app.show_page("online")
