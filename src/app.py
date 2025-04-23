"""
Main StreamDeck application module.
Provides a GUI for controlling OBS Studio with a StreamDeck hardware device.
"""
import os
import sys
import threading
import time
import customtkinter
from typing import Dict, Any, Optional

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import modules
from utils.logger import Logger
from utils.config_manager import ConfigManager
from obs.obs_controller import OBSController
from hardware.serial_controller import SerialController
from scripts.scripting import ScriptManager
from ui.base_page import BasePage

# Import UI pages
from ui.pages.connection_page import ConnectionPage
from ui.pages.online_page import OnlinePage
from ui.pages.mapping_page import MappingPage
from ui.pages.script_page import ScriptPage
from ui.pages.settings_page import SettingsPage

# Set appearance mode
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")

class StreamDeckApp(customtkinter.CTk):
    """
    Main application class for StreamDeck control application.
    
    Handles the application lifecycle, page management, and coordinating
    between the OBS WebSocket, StreamDeck hardware, and UI components.
    
    Attributes:
        logger (Logger): Application logger
        config (ConfigManager): Configuration manager
        script_manager (ScriptManager): Script manager
        obs (OBSController): OBS WebSocket controller
        serial (SerialController): StreamDeck hardware controller
        pages (Dict): Dictionary of application pages
        current_page (str): Name of the currently displayed page
    """
    def __init__(self):
        """Initialize the application."""
        super().__init__()
        
        # Initialize components
        self.logger = None
        self.config = None
        self.script_manager = None
        self.obs = None
        self.serial = None
        
        # UI components
        self.pages = {}
        self.current_page = None
        
        # Initialize application
        self.init()
    
    def init(self):
        """Initialize all application components."""
        self.init_logger()
        self.init_data()
        self.init_graphics()
        self.init_controllers()
        self.add_pages()
        self.show_page("connection")
        self.init_app_mainloop()
    
    def init_logger(self):
        """Initialize application logger."""
        self.logger = Logger(
            levels=["debug", "info", "warning", "error", "critical"],
            filename="streamdeck.log",
            console=True
        )
        self.logger.info("Application starting")
    
    def init_data(self):
        """Initialize data managers."""
        # Configuration manager
        self.config = ConfigManager()
        
        # Script manager
        self.script_manager = ScriptManager(logger=self.logger)
    
    def init_controllers(self):
        """Initialize hardware and OBS controllers."""
        # OBS controller
        obs_data = self.config.settings['connection']['obs_data']
        self.obs = OBSController(
            host=obs_data['host'],
            port=int(obs_data['port']),
            password=obs_data['password'],
            logger=self.logger
        )
        
        # Serial controller
        serial_data = self.config.settings['connection']['serial_data']
        self.serial = SerialController(
            port=serial_data['com_port'],
            baud_rate=int(serial_data['baud_rate']),
            logger=self.logger
        )
        
        # Register callbacks
        self._register_controller_callbacks()
    
    def _register_controller_callbacks(self):
        """Register callbacks between controllers."""
        # Serial -> OBS callbacks
        if self.serial and self.obs:
            # Recording control
            self.serial.register_callback('record_start', self.obs.start_recording)
            self.serial.register_callback('record_stop', self.obs.stop_recording)
            
            # Streaming control
            self.serial.register_callback('stream_start', self.obs.start_streaming)
            self.serial.register_callback('stream_stop', self.obs.stop_streaming)
            
            # Scene control
            self.serial.register_callback('scene_change', self._handle_scene_change)
            
            # Volume control
            self.serial.register_callback('volume_change', self._handle_volume_change)
            
            # Script execution
            self.serial.register_callback('execute_script', self._handle_script_execution)
        
        # OBS -> Serial callbacks
        if self.obs and self.serial:
            # Update LEDs based on streaming/recording state
            self.obs.register_callback('streaming_state', lambda state: self.serial.set_led(0, state))
            self.obs.register_callback('recording_state', lambda state: self.serial.set_led(1, state))
    
    def _handle_scene_change(self, button_id):
        """Handle scene change from StreamDeck."""
        if button_id in self.config.settings['mapping'] and self.config.settings['mapping'][button_id]:
            scene_name = self.config.settings['mapping'][button_id]
            self.obs.set_current_scene(scene_name)
    
    def _handle_volume_change(self, pot_id, pot_value):
        """Handle volume change from StreamDeck."""
        if pot_id in self.config.settings['mapping'] and self.config.settings['mapping'][pot_id]:
            volume_name = self.config.settings['mapping'][pot_id]
            _, db_value = self.obs.pot_to_db(pot_value)
            self.obs.set_volume(volume_name, db_value)
    
    def _handle_script_execution(self, button_id):
        """Handle script execution from StreamDeck."""
        if button_id in self.config.settings['mapping'] and self.config.settings['mapping'][button_id]:
            script_name = self.config.settings['mapping'][button_id]
            self.script_manager.execute_script(script_name, async_execution=True)
    
    def init_graphics(self):
        """Initialize application window and theme."""
        # Set window properties
        self.title("StreamDeck Control")
        self.geometry("800x600")
        self.minsize(800, 600)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Set theme based on configuration
        theme = self.config.settings.get('ui', {}).get('theme', 'dark')
        customtkinter.set_appearance_mode(theme)
    
    def add_pages(self):
        """Add application pages."""
        self.pages = {
            "connection": ConnectionPage(self),
            "online": OnlinePage(self),
            "mapping": MappingPage(self),
            "script": ScriptPage(self),
            "settings": SettingsPage(self)
        }
        
        # Create each page
        for page in self.pages.values():
            page.create_page()
    
    def show_page(self, page_name):
        """
        Show a specific page.
        
        Args:
            page_name (str): Name of the page to show
        """
        if page_name not in self.pages:
            self.logger.error(f"Page '{page_name}' not found")
            return
            
        # Hide current page if exists
        if self.current_page and self.current_page in self.pages:
            self.pages[self.current_page].hide()
            
        # Show new page
        self.pages[page_name].show()
        self.current_page = page_name
        self.logger.debug(f"Switched to page: {page_name}")
    
    def init_app_mainloop(self):
        """Initialize background tasks."""
        # Create task thread
        thread = threading.Thread(target=self.task_app_mainloop, daemon=True)
        thread.start()
    
    def task_app_mainloop(self):
        """Background task loop for periodic tasks."""
        while True:
            # Add periodic tasks here if needed
            time.sleep(1)
    
    def save_all_settings(self):
        """Save all application settings."""
        self.config.save_settings()
        self.config.save_mapping()
        self.config.save_scripts()
        self.logger.info("All settings saved")
    
    def exit(self):
        """Clean exit of the application."""
        # Stop controllers
        if self.serial and self.serial.is_connected():
            self.serial.disconnect()
            
        if self.obs and self.obs.is_connected():
            self.obs.disconnect()
            
        # Save settings
        self.save_all_settings()
        
        # Log exit
        self.logger.info("Application shutting down")
        
        # Exit
        self.quit()

# NOTA: Questa applicazione deve essere avviata utilizzando main.py
# Non avviare direttamente questo file 