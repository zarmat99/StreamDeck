"""
Online Page for StreamDeck application.
Provides interface for monitoring and controlling OBS while connected.
"""
import customtkinter
import threading
import time
from typing import Dict, List, Any, Optional

from ui.base_page import BasePage

class OnlinePage(BasePage):
    """
    Online page for monitoring and controlling OBS and StreamDeck.
    
    This is the main operation page for when the user is connected to
    both OBS and StreamDeck hardware.
    """
    def __init__(self, parent):
        """
        Initialize the online page.
        
        Args:
            parent: Parent application
        """
        super().__init__(parent)
        self.app = parent
        
        # Status variables
        self.vars = {
            'status': {
                'streaming': customtkinter.BooleanVar(value=False),
                'recording': customtkinter.BooleanVar(value=False),
                'current_scene': customtkinter.StringVar(value="None"),
                'obs_connected': customtkinter.BooleanVar(value=False),
                'serial_connected': customtkinter.BooleanVar(value=False)
            },
            'sources': {
                'list': []
            },
            'scenes': {
                'list': []
            }
        }
        
        # Update timers
        self.update_timer = None
        
        # Add callbacks for page show/hide
        self.add_on_show_callback(self.on_show)
        self.add_on_hide_callback(self.on_hide)
    
    def change_window_name(self):
        """Change window title for this page."""
        self.parent.title("StreamDeck - Online Mode")
    
    def create_widgets(self):
        """Create widgets for the online page."""
        # Title frame
        self.add_title("Online Mode")
        
        # ===== Create frames =====
        # Connection status frame
        self.frames["status"] = customtkinter.CTkFrame(self.frames["body"])
        
        # Scene control frame
        self.frames["scenes"] = customtkinter.CTkFrame(self.frames["body"])
        
        # Volume control frame
        self.frames["volume"] = customtkinter.CTkFrame(self.frames["body"])
        
        # Controls frame
        self.frames["controls"] = customtkinter.CTkFrame(self.frames["body"])
        
        # ===== Status frame content =====
        self.labels["status_title"] = customtkinter.CTkLabel(
            self.frames["status"],
            text="Connection Status",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        
        # OBS status
        self.frames["obs_status"] = customtkinter.CTkFrame(self.frames["status"], fg_color="transparent")
        
        self.labels["obs_status"] = customtkinter.CTkLabel(
            self.frames["obs_status"],
            text="OBS:",
            width=80
        )
        
        self.labels["obs_status_value"] = customtkinter.CTkLabel(
            self.frames["obs_status"],
            text="Disconnected",
            text_color="red"
        )
        
        # Serial status
        self.frames["serial_status"] = customtkinter.CTkFrame(self.frames["status"], fg_color="transparent")
        
        self.labels["serial_status"] = customtkinter.CTkLabel(
            self.frames["serial_status"],
            text="StreamDeck:",
            width=80
        )
        
        self.labels["serial_status_value"] = customtkinter.CTkLabel(
            self.frames["serial_status"],
            text="Disconnected",
            text_color="red"
        )
        
        # ===== Scene control frame content =====
        self.labels["scenes_title"] = customtkinter.CTkLabel(
            self.frames["scenes"],
            text="Current Scene",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        
        self.labels["current_scene"] = customtkinter.CTkLabel(
            self.frames["scenes"],
            textvariable=self.vars["status"]["current_scene"],
            font=customtkinter.CTkFont(size=14)
        )
        
        # Scene selector
        self.comboboxes["scene_select"] = customtkinter.CTkComboBox(
            self.frames["scenes"],
            values=["Loading scenes..."],
            command=self.scene_selected
        )
        
        self.buttons["set_scene"] = customtkinter.CTkButton(
            self.frames["scenes"],
            text="Set Scene",
            command=self.set_scene
        )
        
        # ===== Volume control frame content =====
        self.labels["volume_title"] = customtkinter.CTkLabel(
            self.frames["volume"],
            text="Audio Controls",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        
        # Source selector
        self.comboboxes["source_select"] = customtkinter.CTkComboBox(
            self.frames["volume"],
            values=["Loading sources..."]
        )
        
        # Volume slider
        self.sliders["volume"] = customtkinter.CTkSlider(
            self.frames["volume"],
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.volume_changed
        )
        
        self.labels["volume_value"] = customtkinter.CTkLabel(
            self.frames["volume"],
            text="0%"
        )
        
        self.buttons["mute"] = customtkinter.CTkButton(
            self.frames["volume"],
            text="Mute",
            command=self.toggle_mute
        )
        
        # ===== Controls frame content =====
        self.labels["controls_title"] = customtkinter.CTkLabel(
            self.frames["controls"],
            text="Stream Controls",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        
        # Streaming controls
        self.frames["stream_controls"] = customtkinter.CTkFrame(self.frames["controls"], fg_color="transparent")
        
        self.buttons["start_streaming"] = customtkinter.CTkButton(
            self.frames["stream_controls"],
            text="Start Streaming",
            fg_color="#28a745",
            hover_color="#218838",
            command=self.start_streaming
        )
        
        self.buttons["stop_streaming"] = customtkinter.CTkButton(
            self.frames["stream_controls"],
            text="Stop Streaming",
            fg_color="#dc3545",
            hover_color="#c82333",
            command=self.stop_streaming,
            state="disabled"
        )
        
        # Recording controls
        self.frames["record_controls"] = customtkinter.CTkFrame(self.frames["controls"], fg_color="transparent")
        
        self.buttons["start_recording"] = customtkinter.CTkButton(
            self.frames["record_controls"],
            text="Start Recording",
            fg_color="#28a745",
            hover_color="#218838",
            command=self.start_recording
        )
        
        self.buttons["stop_recording"] = customtkinter.CTkButton(
            self.frames["record_controls"],
            text="Stop Recording",
            fg_color="#dc3545",
            hover_color="#c82333",
            command=self.stop_recording,
            state="disabled"
        )
        
        # Status indicators
        self.frames["status_indicators"] = customtkinter.CTkFrame(self.frames["controls"], fg_color="transparent")
        
        self.labels["streaming_status"] = customtkinter.CTkLabel(
            self.frames["status_indicators"],
            text="Streaming:",
            width=80
        )
        
        self.labels["streaming_value"] = customtkinter.CTkLabel(
            self.frames["status_indicators"],
            text="Offline",
            text_color="gray"
        )
        
        self.labels["recording_status"] = customtkinter.CTkLabel(
            self.frames["status_indicators"],
            text="Recording:",
            width=80
        )
        
        self.labels["recording_value"] = customtkinter.CTkLabel(
            self.frames["status_indicators"],
            text="Offline",
            text_color="gray"
        )
        
        # ===== Bottom frame content =====
        # Navigation buttons
        nav_buttons = ["connection", "mapping", "script", "settings"]
        self.add_navigation_buttons(nav_buttons, self.navigate_to_page)
        
        # Status message
        self.add_status()
    
    def configure_widgets(self):
        """Configure widget layout and behavior."""
        # Configure section frames
        for frame_name in ["status", "scenes", "volume", "controls"]:
            self.frames[frame_name].configure(corner_radius=10)
    
    def grid_widgets(self):
        """Position widgets in the page."""
        # Configure body layout
        self.frames["body"].grid_columnconfigure(0, weight=1)
        self.frames["body"].grid_columnconfigure(1, weight=1)
        self.frames["body"].grid_rowconfigure(0, weight=1)
        self.frames["body"].grid_rowconfigure(1, weight=1)
        
        # Position section frames
        self.frames["status"].grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.frames["scenes"].grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.frames["volume"].grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.frames["controls"].grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        
        # ===== Status frame layout =====
        self.labels["status_title"].pack(pady=(10, 5))
        
        # OBS status
        self.frames["obs_status"].pack(fill="x", padx=10, pady=5)
        self.labels["obs_status"].pack(side="left", padx=5)
        self.labels["obs_status_value"].pack(side="left", padx=5)
        
        # Serial status
        self.frames["serial_status"].pack(fill="x", padx=10, pady=5)
        self.labels["serial_status"].pack(side="left", padx=5)
        self.labels["serial_status_value"].pack(side="left", padx=5)
        
        # ===== Scene control frame layout =====
        self.labels["scenes_title"].pack(pady=(10, 5))
        self.labels["current_scene"].pack(pady=5)
        self.comboboxes["scene_select"].pack(fill="x", padx=20, pady=5)
        self.buttons["set_scene"].pack(pady=10)
        
        # ===== Volume control frame layout =====
        self.labels["volume_title"].pack(pady=(10, 5))
        self.comboboxes["source_select"].pack(fill="x", padx=20, pady=5)
        
        # Volume slider and label
        slider_frame = customtkinter.CTkFrame(self.frames["volume"], fg_color="transparent")
        slider_frame.pack(fill="x", padx=20, pady=5)
        
        self.sliders["volume"].pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.labels["volume_value"].pack(side="right", padx=5)
        
        self.buttons["mute"].pack(pady=10)
        
        # ===== Controls frame layout =====
        self.labels["controls_title"].pack(pady=(10, 5))
        
        # Streaming controls
        self.frames["stream_controls"].pack(fill="x", padx=10, pady=5)
        self.buttons["start_streaming"].pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.buttons["stop_streaming"].pack(side="right", fill="x", expand=True, padx=5, pady=5)
        
        # Recording controls
        self.frames["record_controls"].pack(fill="x", padx=10, pady=5)
        self.buttons["start_recording"].pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.buttons["stop_recording"].pack(side="right", fill="x", expand=True, padx=5, pady=5)
        
        # Status indicators
        self.frames["status_indicators"].pack(fill="x", padx=10, pady=10)
        
        # Streaming status
        streaming_frame = customtkinter.CTkFrame(self.frames["status_indicators"], fg_color="transparent")
        streaming_frame.pack(fill="x", pady=2)
        self.labels["streaming_status"].pack(side="left", padx=5)
        self.labels["streaming_value"].pack(side="left", padx=5)
        
        # Recording status
        recording_frame = customtkinter.CTkFrame(self.frames["status_indicators"], fg_color="transparent")
        recording_frame.pack(fill="x", pady=2)
        self.labels["recording_status"].pack(side="left", padx=5)
        self.labels["recording_value"].pack(side="left", padx=5)
    
    def on_show(self):
        """Handle actions when page is shown."""
        # Start regular updates
        self.update_status()
        self.update_timer = self.after(1000, self.periodic_update)
        
        # Update scenes and sources lists
        self.update_scenes_list()
        self.update_sources_list()
    
    def on_hide(self):
        """Handle actions when page is hidden."""
        # Cancel update timer
        if self.update_timer:
            self.after_cancel(self.update_timer)
            self.update_timer = None
    
    def periodic_update(self):
        """Periodic update of status and controls."""
        self.update_status()
        self.update_timer = self.after(1000, self.periodic_update)
    
    def update_status(self):
        """Update connection and streaming status."""
        # Update OBS connection status
        obs_connected = self.app.obs and self.app.obs.is_connected()
        self.vars["status"]["obs_connected"].set(obs_connected)
        
        if obs_connected:
            self.labels["obs_status_value"].configure(text="Connected", text_color="green")
            
            # Update streaming status
            is_streaming = self.app.obs.get_streaming_status()
            self.vars["status"]["streaming"].set(is_streaming)
            
            if is_streaming:
                self.labels["streaming_value"].configure(text="Online", text_color="#28a745")
                self.buttons["start_streaming"].configure(state="disabled")
                self.buttons["stop_streaming"].configure(state="normal")
            else:
                self.labels["streaming_value"].configure(text="Offline", text_color="gray")
                self.buttons["start_streaming"].configure(state="normal")
                self.buttons["stop_streaming"].configure(state="disabled")
            
            # Update recording status
            is_recording = self.app.obs.get_recording_status()
            self.vars["status"]["recording"].set(is_recording)
            
            if is_recording:
                self.labels["recording_value"].configure(text="Active", text_color="#28a745")
                self.buttons["start_recording"].configure(state="disabled")
                self.buttons["stop_recording"].configure(state="normal")
            else:
                self.labels["recording_value"].configure(text="Inactive", text_color="gray")
                self.buttons["start_recording"].configure(state="normal")
                self.buttons["stop_recording"].configure(state="disabled")
            
            # Update current scene
            current_scene = self.app.obs.get_current_scene()
            if current_scene:
                self.vars["status"]["current_scene"].set(current_scene)
        else:
            self.labels["obs_status_value"].configure(text="Disconnected", text_color="red")
            self.labels["streaming_value"].configure(text="Offline", text_color="gray")
            self.labels["recording_value"].configure(text="Inactive", text_color="gray")
            self.vars["status"]["current_scene"].set("None")
            
            # Disable controls
            self.buttons["start_streaming"].configure(state="disabled")
            self.buttons["stop_streaming"].configure(state="disabled")
            self.buttons["start_recording"].configure(state="disabled")
            self.buttons["stop_recording"].configure(state="disabled")
        
        # Update StreamDeck connection status
        serial_connected = self.app.serial and self.app.serial.is_connected()
        self.vars["status"]["serial_connected"].set(serial_connected)
        
        if serial_connected:
            self.labels["serial_status_value"].configure(text="Connected", text_color="green")
        else:
            self.labels["serial_status_value"].configure(text="Disconnected", text_color="red")
    
    def update_scenes_list(self):
        """Update the list of available scenes."""
        if not self.app.obs or not self.app.obs.is_connected():
            self.comboboxes["scene_select"].configure(values=["OBS not connected"])
            return
        
        scenes = self.app.obs.get_scene_list()
        if not scenes:
            self.comboboxes["scene_select"].configure(values=["No scenes available"])
            return
            
        self.vars["scenes"]["list"] = scenes
        self.comboboxes["scene_select"].configure(values=scenes)
        
        # Select current scene
        current_scene = self.app.obs.get_current_scene()
        if current_scene in scenes:
            self.comboboxes["scene_select"].set(current_scene)
    
    def update_sources_list(self):
        """Update the list of available audio sources."""
        if not self.app.obs or not self.app.obs.is_connected():
            self.comboboxes["source_select"].configure(values=["OBS not connected"])
            return
        
        sources = self.app.obs.get_volume_sources()
        if not sources:
            self.comboboxes["source_select"].configure(values=["No sources available"])
            return
            
        self.vars["sources"]["list"] = sources
        self.comboboxes["source_select"].configure(values=sources)
        
        # Select first source
        if sources:
            self.comboboxes["source_select"].set(sources[0])
            self.update_volume_display(sources[0])
    
    def update_volume_display(self, source_name):
        """
        Update volume slider for the selected source.
        
        Args:
            source_name (str): Audio source name
        """
        if not self.app.obs or not self.app.obs.is_connected():
            return
            
        # Get volume and update slider
        volume = self.app.obs.get_volume(source_name)
        if volume is not None:
            # Convert from dB to percentage (approximately)
            volume_pct = min(100, max(0, (volume + 60) / 60 * 100)) if volume > -60 else 0
            self.sliders["volume"].set(volume_pct)
            self.labels["volume_value"].configure(text=f"{int(volume_pct)}%")
    
    def scene_selected(self, selection):
        """
        Handle scene selection from dropdown.
        
        Args:
            selection (str): Selected scene
        """
        # No immediate action, user must click Set Scene button
        pass
    
    def set_scene(self):
        """Set the currently selected scene in OBS."""
        if not self.app.obs or not self.app.obs.is_connected():
            self.show_status("OBS not connected", "red")
            return
            
        scene = self.comboboxes["scene_select"].get()
        if scene in self.vars["scenes"]["list"]:
            success = self.app.obs.set_current_scene(scene)
            if success:
                self.show_status(f"Changed scene to {scene}", "green")
                self.vars["status"]["current_scene"].set(scene)
            else:
                self.show_status(f"Failed to change scene", "red")
    
    def volume_changed(self, value):
        """
        Handle volume slider changes.
        
        Args:
            value (float): Slider value (0-100)
        """
        # Update volume display
        self.labels["volume_value"].configure(text=f"{int(value)}%")
        
        # Update OBS volume
        source = self.comboboxes["source_select"].get()
        if source in self.vars["sources"]["list"] and self.app.obs and self.app.obs.is_connected():
            # Convert percentage to dB (approximately)
            if value == 0:
                db_value = -100  # Fully muted
            else:
                db_value = (value / 100 * 60) - 60  # Range from -60 to 0 dB
                
            self.app.obs.set_volume(source, db_value)
    
    def toggle_mute(self):
        """Toggle mute for the selected source."""
        source = self.comboboxes["source_select"].get()
        if source not in self.vars["sources"]["list"] or not self.app.obs or not self.app.obs.is_connected():
            return
            
        current_volume = self.app.obs.get_volume(source)
        if current_volume is None:
            return
            
        if current_volume <= -60:  # Currently muted
            # Unmute to previous level
            self.sliders["volume"].set(50)  # Default to 50%
            self.app.obs.set_volume(source, -30)  # -30dB
            self.labels["volume_value"].configure(text="50%")
            self.buttons["mute"].configure(text="Mute")
        else:
            # Mute
            self.app.obs.set_volume(source, -100)
            self.sliders["volume"].set(0)
            self.labels["volume_value"].configure(text="0%")
            self.buttons["mute"].configure(text="Unmute")
    
    def start_streaming(self):
        """Start OBS streaming."""
        if not self.app.obs or not self.app.obs.is_connected():
            return
            
        # Start in a separate thread to avoid UI freeze
        threading.Thread(target=self._streaming_action, args=(True,), daemon=True).start()
    
    def stop_streaming(self):
        """Stop OBS streaming."""
        if not self.app.obs or not self.app.obs.is_connected():
            return
            
        # Stop in a separate thread to avoid UI freeze
        threading.Thread(target=self._streaming_action, args=(False,), daemon=True).start()
    
    def _streaming_action(self, start: bool):
        """
        Perform streaming action (start/stop).
        
        Args:
            start (bool): True to start, False to stop
        """
        if start:
            success = self.app.obs.start_streaming()
            if success:
                self.show_status("Streaming started", "green")
            else:
                self.show_status("Failed to start streaming", "red")
        else:
            success = self.app.obs.stop_streaming()
            if success:
                self.show_status("Streaming stopped", "green")
            else:
                self.show_status("Failed to stop streaming", "red")
    
    def start_recording(self):
        """Start OBS recording."""
        if not self.app.obs or not self.app.obs.is_connected():
            return
            
        # Start in a separate thread to avoid UI freeze
        threading.Thread(target=self._recording_action, args=(True,), daemon=True).start()
    
    def stop_recording(self):
        """Stop OBS recording."""
        if not self.app.obs or not self.app.obs.is_connected():
            return
            
        # Stop in a separate thread to avoid UI freeze
        threading.Thread(target=self._recording_action, args=(False,), daemon=True).start()
    
    def _recording_action(self, start: bool):
        """
        Perform recording action (start/stop).
        
        Args:
            start (bool): True to start, False to stop
        """
        if start:
            success = self.app.obs.start_recording()
            if success:
                self.show_status("Recording started", "green")
            else:
                self.show_status("Failed to start recording", "red")
        else:
            success = self.app.obs.stop_recording()
            if success:
                self.show_status("Recording stopped", "green")
            else:
                self.show_status("Failed to stop recording", "red")
    
    def navigate_to_page(self, page_name):
        """
        Navigate to another page.
        
        Args:
            page_name (str): Name of the page to navigate to
        """
        self.app.show_page(page_name) 