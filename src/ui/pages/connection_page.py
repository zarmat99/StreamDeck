"""
Connection Page for StreamDeck application.
Provides interface for configuring and connecting to OBS and StreamDeck hardware.
"""
import customtkinter
import serial.tools.list_ports
from typing import Dict, Any, Optional
import threading
import time

from ui.base_page import BasePage

class ConnectionPage(BasePage):
    """
    Connection page for configuring and connecting to OBS and StreamDeck hardware.
    
    Provides input fields for OBS WebSocket settings and StreamDeck serial settings,
    as well as connection status information and connection buttons.
    """
    def __init__(self, parent):
        """
        Initialize the connection page.
        
        Args:
            parent: Parent application
        """
        super().__init__(parent)
        self.app = parent
        
        # StringVars for input fields
        self.vars = {
            'obs_data': {
                'host': customtkinter.StringVar(value=self.app.config.settings['connection']['obs_data']['host'] or "localhost"),
                'port': customtkinter.StringVar(value=self.app.config.settings['connection']['obs_data']['port'] or "4455"),
                'password': customtkinter.StringVar(value=self.app.config.settings['connection']['obs_data']['password'] or "")
            },
            'serial_data': {
                'com_port': customtkinter.StringVar(value=self.app.config.settings['connection']['serial_data']['com_port'] or ""),
                'baud_rate': customtkinter.StringVar(value=self.app.config.settings['connection']['serial_data']['baud_rate'] or "9600")
            }
        }
        
        # Connection status variables
        self.obs_connected = False
        self.serial_connected = False
        
        # Auto refresh timer
        self.refresh_timer = None
        
        # Add show/hide callbacks
        self.add_on_show_callback(self.on_show)
        self.add_on_hide_callback(self.on_hide)
    
    def change_window_name(self):
        """Change window title for this page."""
        self.parent.title("StreamDeck - Connection")
    
    def create_widgets(self):
        """Create widgets for the connection page."""
        # Title frame
        self.add_title("Connection Setup")
        
        # OBS Configuration section
        self.labels["obs_configuration"] = customtkinter.CTkLabel(
            self.frames["body"], 
            text="OBS WebSocket Configuration", 
            font=customtkinter.CTkFont(size=20)
        )
        
        # OBS input fields
        self.labels["host"] = customtkinter.CTkLabel(
            self.frames["body"], 
            text="Host", 
            font=customtkinter.CTkFont(size=15)
        )
        self.entries["host"] = customtkinter.CTkEntry(
            self.frames["body"], 
            textvariable=self.vars["obs_data"]["host"]
        )
        
        self.labels["port"] = customtkinter.CTkLabel(
            self.frames["body"], 
            text="Port", 
            font=customtkinter.CTkFont(size=15)
        )
        self.entries["port"] = customtkinter.CTkEntry(
            self.frames["body"], 
            textvariable=self.vars["obs_data"]["port"]
        )
        
        self.labels["password"] = customtkinter.CTkLabel(
            self.frames["body"], 
            text="Password", 
            font=customtkinter.CTkFont(size=15)
        )
        self.entries["password"] = customtkinter.CTkEntry(
            self.frames["body"], 
            textvariable=self.vars["obs_data"]["password"],
            show="*"
        )
        
        # OBS connection button
        self.buttons["connect_obs"] = customtkinter.CTkButton(
            self.frames["body"],
            text="Connect to OBS",
            command=self.connect_obs_button_click
        )
        
        # OBS connection status
        self.labels["obs_status"] = customtkinter.CTkLabel(
            self.frames["body"],
            text="Not Connected",
            text_color="red"
        )
        
        # StreamDeck Configuration section
        self.labels["streamdeck_configuration"] = customtkinter.CTkLabel(
            self.frames["body"], 
            text="StreamDeck Configuration", 
            font=customtkinter.CTkFont(size=20)
        )
        
        # StreamDeck input fields
        self.labels["com_port"] = customtkinter.CTkLabel(
            self.frames["body"], 
            text="COM Port", 
            font=customtkinter.CTkFont(size=15)
        )
        
        # COM Port dropdown
        self.comboboxes["com_port"] = customtkinter.CTkComboBox(
            self.frames["body"],
            values=["Select COM port"],
            variable=self.vars["serial_data"]["com_port"],
            command=self.com_port_selected
        )
        
        # Refresh button for COM ports
        self.buttons["refresh_ports"] = customtkinter.CTkButton(
            self.frames["body"],
            text="↻",
            width=30,
            command=self.refresh_com_ports
        )
        
        self.labels["baud_rate"] = customtkinter.CTkLabel(
            self.frames["body"], 
            text="Baud Rate", 
            font=customtkinter.CTkFont(size=15)
        )
        
        # Baud rate dropdown
        self.comboboxes["baud_rate"] = customtkinter.CTkComboBox(
            self.frames["body"],
            values=["9600", "19200", "38400", "57600", "115200"],
            variable=self.vars["serial_data"]["baud_rate"]
        )
        
        # StreamDeck connection button
        self.buttons["connect_serial"] = customtkinter.CTkButton(
            self.frames["body"],
            text="Connect to StreamDeck",
            command=self.connect_serial_button_click
        )
        
        # StreamDeck connection status
        self.labels["serial_status"] = customtkinter.CTkLabel(
            self.frames["body"],
            text="Not Connected",
            text_color="red"
        )
        
        # Continue button
        self.buttons["continue"] = customtkinter.CTkButton(
            self.frames["bottom"],
            text="Continue to Online Mode",
            command=self.continue_to_online,
            state="disabled"
        )
        
        # Auto-connect checkbox
        self.switches["auto_connect"] = customtkinter.CTkSwitch(
            self.frames["bottom"],
            text="Auto-connect on startup",
            command=self.auto_connect_toggled
        )
        
        # Status message
        self.add_status()
    
    def configure_widgets(self):
        """Configure widgets layout."""
        # Configure layouts
        self.frames["body"].grid_columnconfigure(0, weight=1)
        self.frames["body"].grid_columnconfigure(1, weight=3)
        self.frames["body"].grid_columnconfigure(2, weight=1)
        
        # Load initial data
        self.refresh_com_ports()
    
    def grid_widgets(self):
        """Position widgets in the page."""
        row = 0
        
        # OBS Configuration section
        self.labels["obs_configuration"].grid(row=row, column=0, columnspan=3, sticky="w", padx=20, pady=(20, 10))
        row += 1
        
        # OBS input fields
        self.labels["host"].grid(row=row, column=0, sticky="e", padx=(20, 5), pady=5)
        self.entries["host"].grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        self.labels["port"].grid(row=row, column=0, sticky="e", padx=(20, 5), pady=5)
        self.entries["port"].grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        self.labels["password"].grid(row=row, column=0, sticky="e", padx=(20, 5), pady=5)
        self.entries["password"].grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # OBS connection button and status
        self.buttons["connect_obs"].grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 5))
        self.labels["obs_status"].grid(row=row, column=2, sticky="w", padx=5, pady=5)
        row += 1
        
        # Spacer
        spacer = customtkinter.CTkFrame(self.frames["body"], height=20, fg_color="transparent")
        spacer.grid(row=row, column=0, columnspan=3, sticky="ew", padx=20, pady=10)
        row += 1
        
        # StreamDeck Configuration section
        self.labels["streamdeck_configuration"].grid(row=row, column=0, columnspan=3, sticky="w", padx=20, pady=(10, 10))
        row += 1
        
        # StreamDeck input fields
        self.labels["com_port"].grid(row=row, column=0, sticky="e", padx=(20, 5), pady=5)
        self.comboboxes["com_port"].grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        self.buttons["refresh_ports"].grid(row=row, column=2, sticky="w", padx=5, pady=5)
        row += 1
        
        self.labels["baud_rate"].grid(row=row, column=0, sticky="e", padx=(20, 5), pady=5)
        self.comboboxes["baud_rate"].grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1
        
        # StreamDeck connection button and status
        self.buttons["connect_serial"].grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 5))
        self.labels["serial_status"].grid(row=row, column=2, sticky="w", padx=5, pady=5)
        row += 1
        
        # Bottom frame layout
        self.switches["auto_connect"].pack(side="left", padx=20, pady=10)
        self.buttons["continue"].pack(side="right", padx=20, pady=10)
    
    def on_show(self):
        """Handle page becoming visible."""
        # Update connection status indicators
        self.update_connection_status()
        
        # Start port refresh timer
        self.refresh_timer = self.after(5000, self.auto_refresh_ports)
    
    def on_hide(self):
        """Handle page being hidden."""
        # Cancel refresh timer
        if self.refresh_timer:
            self.after_cancel(self.refresh_timer)
            self.refresh_timer = None
    
    def auto_refresh_ports(self):
        """Automatically refresh ports periodically."""
        self.refresh_com_ports()
        self.refresh_timer = self.after(5000, self.auto_refresh_ports)
    
    def refresh_com_ports(self):
        """Refresh the list of available COM ports."""
        # Get current selection
        current_selection = self.vars["serial_data"]["com_port"].get()
        
        # Get available ports
        ports = []
        for port, desc in self.app.serial.list_ports():
            ports.append(f"{port} ({desc})")
        
        if not ports:
            ports = ["No COM ports available"]
            
        # Update combobox values
        self.comboboxes["com_port"].configure(values=ports)
        
        # Try to restore previous selection if it's still available
        if current_selection and any(current_selection in port for port in ports):
            self.vars["serial_data"]["com_port"].set(current_selection)
        elif ports:
            # Select first port
            self.vars["serial_data"]["com_port"].set(ports[0])
    
    def com_port_selected(self, selection):
        """
        Handle COM port selection.
        
        Args:
            selection (str): Selected COM port
        """
        if selection and selection != "No COM ports available":
            # Extract just the port part (COM3) from "COM3 (USB Serial Device)"
            port = selection.split(" ")[0]
            self.vars["serial_data"]["com_port"].set(port)
    
    def connect_obs_button_click(self):
        """Handle OBS connect button click."""
        # Update config with current values
        self.update_config_from_ui()
        
        # Update OBS controller settings
        obs_data = self.app.config.settings['connection']['obs_data']
        self.app.obs.host = obs_data['host']
        self.app.obs.port = int(obs_data['port'])
        self.app.obs.password = obs_data['password']
        
        # Attempt connection
        if self.app.obs.is_connected():
            # Disconnect if already connected
            self.app.obs.disconnect()
            self.obs_connected = False
            self.buttons["connect_obs"].configure(text="Connect to OBS")
        else:
            # Connect if not connected
            connection_thread = threading.Thread(
                target=self._connect_obs_async,
                daemon=True
            )
            connection_thread.start()
            
            # Show connecting status
            self.labels["obs_status"].configure(text="Connecting...", text_color="orange")
            self.buttons["connect_obs"].configure(state="disabled")
    
    def _connect_obs_async(self):
        """Connect to OBS asynchronously."""
        success = self.app.obs.connect()
        
        # Update UI from main thread
        self.after(0, lambda: self._update_obs_status(success))
    
    def _update_obs_status(self, success):
        """
        Update OBS connection status in UI.
        
        Args:
            success (bool): Whether connection was successful
        """
        if success:
            self.obs_connected = True
            self.labels["obs_status"].configure(text="Connected", text_color="green")
            self.buttons["connect_obs"].configure(text="Disconnect", state="normal")
            self.show_status("Connected to OBS successfully", "green")
        else:
            self.obs_connected = False
            self.labels["obs_status"].configure(text="Connection Failed", text_color="red")
            self.buttons["connect_obs"].configure(text="Connect to OBS", state="normal")
            self.show_status("Failed to connect to OBS", "red")
        
        self.update_continue_button()
    
    def connect_serial_button_click(self):
        """Handle StreamDeck connect button click."""
        # Update config with current values
        self.update_config_from_ui()
        
        # Update serial controller settings
        serial_data = self.app.config.settings['connection']['serial_data']
        self.app.serial.port = serial_data['com_port']
        self.app.serial.baud_rate = int(serial_data['baud_rate'])
        
        # Attempt connection
        if self.app.serial.is_connected():
            # Disconnect if already connected
            self.app.serial.disconnect()
            self.serial_connected = False
            self.buttons["connect_serial"].configure(text="Connect to StreamDeck")
        else:
            # Connect if not connected
            connection_thread = threading.Thread(
                target=self._connect_serial_async,
                daemon=True
            )
            connection_thread.start()
            
            # Show connecting status
            self.labels["serial_status"].configure(text="Connecting...", text_color="orange")
            self.buttons["connect_serial"].configure(state="disabled")
    
    def _connect_serial_async(self):
        """Connect to StreamDeck asynchronously."""
        success = self.app.serial.connect()
        
        # Update UI from main thread
        self.after(0, lambda: self._update_serial_status(success))
    
    def _update_serial_status(self, success):
        """
        Update StreamDeck connection status in UI.
        
        Args:
            success (bool): Whether connection was successful
        """
        if success:
            self.serial_connected = True
            self.labels["serial_status"].configure(text="Connected", text_color="green")
            self.buttons["connect_serial"].configure(text="Disconnect", state="normal")
            self.show_status("Connected to StreamDeck successfully", "green")
        else:
            self.serial_connected = False
            self.labels["serial_status"].configure(text="Connection Failed", text_color="red")
            self.buttons["connect_serial"].configure(text="Connect to StreamDeck", state="normal")
            self.show_status("Failed to connect to StreamDeck", "red")
        
        self.update_continue_button()
    
    def update_continue_button(self):
        """Update the state of the continue button based on connection status."""
        if self.obs_connected and self.serial_connected:
            self.buttons["continue"].configure(state="normal")
        else:
            self.buttons["continue"].configure(state="disabled")
    
    def update_connection_status(self):
        """Update connection status indicators based on actual connection state."""
        # Update OBS status
        if self.app.obs and self.app.obs.is_connected():
            self.obs_connected = True
            self.labels["obs_status"].configure(text="Connected", text_color="green")
            self.buttons["connect_obs"].configure(text="Disconnect")
        else:
            self.obs_connected = False
            self.labels["obs_status"].configure(text="Not Connected", text_color="red")
            self.buttons["connect_obs"].configure(text="Connect to OBS")
        
        # Update StreamDeck status
        if self.app.serial and self.app.serial.is_connected():
            self.serial_connected = True
            self.labels["serial_status"].configure(text="Connected", text_color="green")
            self.buttons["connect_serial"].configure(text="Disconnect")
        else:
            self.serial_connected = False
            self.labels["serial_status"].configure(text="Not Connected", text_color="red")
            self.buttons["connect_serial"].configure(text="Connect to StreamDeck")
        
        # Update continue button
        self.update_continue_button()
    
    def update_config_from_ui(self):
        """Update configuration with values from UI."""
        # OBS settings
        self.app.config.settings['connection']['obs_data']['host'] = self.vars['obs_data']['host'].get()
        self.app.config.settings['connection']['obs_data']['port'] = self.vars['obs_data']['port'].get()
        self.app.config.settings['connection']['obs_data']['password'] = self.vars['obs_data']['password'].get()
        
        # Serial settings
        self.app.config.settings['connection']['serial_data']['com_port'] = self.vars['serial_data']['com_port'].get()
        self.app.config.settings['connection']['serial_data']['baud_rate'] = self.vars['serial_data']['baud_rate'].get()
        
        # Save settings
        self.app.config.save_settings()
    
    def auto_connect_toggled(self):
        """Handle auto-connect toggle."""
        # Save setting
        self.app.config.settings['connection']['auto_connect'] = self.switches["auto_connect"].get()
        self.app.config.save_settings()
    
    def continue_to_online(self):
        """Continue to online page."""
        self.update_config_from_ui()
        self.app.show_page("online") 