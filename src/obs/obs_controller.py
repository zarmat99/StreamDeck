"""
OBS WebSocket controller for StreamDeck application.
Handles communication with OBS Studio via WebSocket protocol.
"""
import math
import threading
import time
from typing import List, Dict, Any, Optional, Tuple, Callable
from obswebsocket import obsws, requests, events

class OBSController:
    """
    Controller for OBS Studio via WebSocket protocol.
    
    Attributes:
        ws (obsws): WebSocket connection to OBS
        host (str): OBS WebSocket host
        port (int): OBS WebSocket port
        password (str): OBS WebSocket password
        connected (bool): Connection status
        logger: Optional logger for events
        callbacks (dict): Event callbacks
    """
    def __init__(self, host: str = 'localhost', port: int = 4455, password: str = '', logger=None):
        """
        Initialize OBS WebSocket controller.
        
        Args:
            host (str): OBS WebSocket host
            port (int): OBS WebSocket port
            password (str): OBS WebSocket password
            logger: Optional logger for events
        """
        self.host = host
        self.port = port
        self.password = password
        self.ws = None
        self.connected = False
        self.logger = logger
        self.callbacks = {}
        self.version = None
        
        # Event listener thread
        self._listener_thread = None
        self._stop_listener = threading.Event()
    
    def log(self, level: str, message: str):
        """Log a message if logger is available."""
        if self.logger and hasattr(self.logger, level):
            getattr(self.logger, level)(message)
    
    def connect(self) -> bool:
        """
        Connect to OBS WebSocket.
        
        Returns:
            bool: True if connection successful
        """
        if self.connected:
            return True
            
        try:
            # Create WebSocket connection
            self.ws = obsws(host=self.host, port=self.port, password=self.password, timeout=3)
            
            # Connect to the WebSocket server
            self.ws.connect()
            
            # Get OBS version to confirm connection
            version_response = self.ws.call(requests.GetVersion())
            self.version = version_response.getObsVersion()
            
            # Register for events
            self._register_events()
            
            # Start event listener
            self._stop_listener.clear()
            self._listener_thread = threading.Thread(target=self._event_listener, daemon=True)
            self._listener_thread.start()
            
            self.connected = True
            self.log('info', f"Connected to OBS WebSocket v{self.version}")
            return True
            
        except Exception as e:
            self.log('error', f"Failed to connect to OBS WebSocket: {str(e)}")
            self.ws = None
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from OBS WebSocket."""
        if not self.connected:
            return
            
        # Stop event listener
        if self._listener_thread and self._listener_thread.is_alive():
            self._stop_listener.set()
            self._listener_thread.join(timeout=1.0)
        
        # Disconnect WebSocket
        try:
            if self.ws:
                self.ws.disconnect()
        except Exception as e:
            self.log('error', f"Error disconnecting from OBS WebSocket: {str(e)}")
        finally:
            self.ws = None
            self.connected = False
            self.log('info', "Disconnected from OBS WebSocket")
    
    def reconnect(self) -> bool:
        """
        Reconnect to OBS WebSocket.
        
        Returns:
            bool: True if reconnection successful
        """
        self.disconnect()
        time.sleep(1)  # Brief delay before reconnecting
        return self.connect()
    
    def _register_events(self):
        """Register for OBS WebSocket events."""
        if not self.ws:
            return
        
        # Register for stream state changes
        self.ws.register(self._on_stream_status_change, events.StreamStateChanged)
        
        # Register for recording state changes
        self.ws.register(self._on_record_status_change, events.RecordStateChanged)
        
        # Register for scene changes
        self.ws.register(self._on_scene_change, events.CurrentProgramSceneChanged)
        
        # Register for input volume changes
        self.ws.register(self._on_input_volume_change, events.InputVolumeChanged)
    
    def _event_listener(self):
        """Event listener thread function."""
        while not self._stop_listener.is_set():
            # Check if connection is still alive
            if self.ws and self.connected:
                try:
                    # Simple ping to check connection
                    self.ws.call(requests.GetVersion())
                except Exception:
                    self.log('warning', "OBS WebSocket connection lost, attempting to reconnect")
                    self.connected = False
                    
                    # Try to reconnect
                    reconnect_success = False
                    for _ in range(3):  # Try 3 times
                        try:
                            reconnect_success = self.reconnect()
                            if reconnect_success:
                                break
                        except Exception:
                            pass
                        time.sleep(2)
                    
                    if not reconnect_success:
                        self.log('error', "Failed to reconnect to OBS WebSocket after multiple attempts")
                        self._stop_listener.set()
            
            # Sleep to avoid high CPU usage
            time.sleep(2)
    
    def _on_stream_status_change(self, message):
        """Handle stream status change events."""
        streaming = message.getOutputActive()
        self.log('info', f"Streaming {'started' if streaming else 'stopped'}")
        self._trigger_callback('streaming_state', streaming)
    
    def _on_record_status_change(self, message):
        """Handle record status change events."""
        recording = message.getOutputActive()
        self.log('info', f"Recording {'started' if recording else 'stopped'}")
        self._trigger_callback('recording_state', recording)
    
    def _on_scene_change(self, message):
        """Handle scene change events."""
        scene_name = message.getSceneName()
        self.log('info', f"Scene changed to '{scene_name}'")
        self._trigger_callback('scene_change', scene_name)
    
    def _on_input_volume_change(self, message):
        """Handle input volume change events."""
        input_name = message.getInputName()
        volume_db = message.getInputVolumeDb()
        self.log('debug', f"Volume changed for '{input_name}': {volume_db} dB")
        self._trigger_callback('volume_change', input_name, volume_db)
    
    def _trigger_callback(self, event_name: str, *args):
        """
        Trigger event callbacks.
        
        Args:
            event_name (str): Name of the event
            *args: Arguments to pass to the callback
        """
        if event_name in self.callbacks:
            for callback in self.callbacks[event_name]:
                try:
                    callback(*args)
                except Exception as e:
                    self.log('error', f"Error in callback for {event_name}: {str(e)}")
    
    def register_callback(self, event_name: str, callback: Callable):
        """
        Register a callback for an event.
        
        Args:
            event_name (str): Name of the event
            callback (Callable): Callback function
        """
        if event_name not in self.callbacks:
            self.callbacks[event_name] = []
        self.callbacks[event_name].append(callback)
    
    def unregister_callback(self, event_name: str, callback: Callable) -> bool:
        """
        Unregister a callback for an event.
        
        Args:
            event_name (str): Name of the event
            callback (Callable): Callback function
            
        Returns:
            bool: True if callback was unregistered
        """
        if event_name in self.callbacks and callback in self.callbacks[event_name]:
            self.callbacks[event_name].remove(callback)
            return True
        return False
    
    def start_streaming(self) -> bool:
        """
        Start streaming in OBS.
        
        Returns:
            bool: True if successful
        """
        if not self.connected:
            self.log('error', "Cannot start streaming: Not connected to OBS")
            return False
            
        try:
            self.ws.call(requests.StartStream())
            self.log('info', "Streaming started")
            return True
        except Exception as e:
            self.log('error', f"Failed to start streaming: {str(e)}")
            return False
    
    def stop_streaming(self) -> bool:
        """
        Stop streaming in OBS.
        
        Returns:
            bool: True if successful
        """
        if not self.connected:
            self.log('error', "Cannot stop streaming: Not connected to OBS")
            return False
            
        try:
            self.ws.call(requests.StopStream())
            self.log('info', "Streaming stopped")
            return True
        except Exception as e:
            self.log('error', f"Failed to stop streaming: {str(e)}")
            return False
    
    def start_recording(self) -> bool:
        """
        Start recording in OBS.
        
        Returns:
            bool: True if successful
        """
        if not self.connected:
            self.log('error', "Cannot start recording: Not connected to OBS")
            return False
            
        try:
            self.ws.call(requests.StartRecord())
            self.log('info', "Recording started")
            return True
        except Exception as e:
            self.log('error', f"Failed to start recording: {str(e)}")
            return False
    
    def stop_recording(self) -> bool:
        """
        Stop recording in OBS.
        
        Returns:
            bool: True if successful
        """
        if not self.connected:
            self.log('error', "Cannot stop recording: Not connected to OBS")
            return False
            
        try:
            self.ws.call(requests.StopRecord())
            self.log('info', "Recording stopped")
            return True
        except Exception as e:
            self.log('error', f"Failed to stop recording: {str(e)}")
            return False
    
    def get_streaming_status(self) -> bool:
        """
        Get streaming status from OBS.
        
        Returns:
            bool: True if streaming is active
        """
        if not self.connected:
            return False
            
        try:
            response = self.ws.call(requests.GetStreamStatus())
            return response.getOutputActive()
        except Exception as e:
            self.log('error', f"Failed to get streaming status: {str(e)}")
            return False
    
    def get_recording_status(self) -> bool:
        """
        Get recording status from OBS.
        
        Returns:
            bool: True if recording is active
        """
        if not self.connected:
            return False
            
        try:
            response = self.ws.call(requests.GetRecordStatus())
            return response.getOutputActive()
        except Exception as e:
            self.log('error', f"Failed to get recording status: {str(e)}")
            return False
    
    def get_scene_list(self) -> List[str]:
        """
        Get list of scenes from OBS.
        
        Returns:
            List[str]: List of scene names
        """
        if not self.connected:
            return []
            
        try:
            response = self.ws.call(requests.GetSceneList())
            scenes = []
            for scene in response.getScenes():
                scenes.append(scene['sceneName'])
            return scenes
        except Exception as e:
            self.log('error', f"Failed to get scene list: {str(e)}")
            return []
    
    def get_current_scene(self) -> Optional[str]:
        """
        Get current scene from OBS.
        
        Returns:
            Optional[str]: Current scene name or None if error
        """
        if not self.connected:
            return None
            
        try:
            response = self.ws.call(requests.GetCurrentProgramScene())
            return response.getCurrentProgramSceneName()
        except Exception as e:
            self.log('error', f"Failed to get current scene: {str(e)}")
            return None
    
    def set_current_scene(self, scene_name: str) -> bool:
        """
        Set current scene in OBS.
        
        Args:
            scene_name (str): Scene name
            
        Returns:
            bool: True if successful
        """
        if not self.connected:
            self.log('error', "Cannot set scene: Not connected to OBS")
            return False
            
        try:
            self.ws.call(requests.SetCurrentProgramScene(sceneName=scene_name))
            self.log('info', f"Scene changed to '{scene_name}'")
            return True
        except Exception as e:
            self.log('error', f"Failed to set scene '{scene_name}': {str(e)}")
            return False
    
    def get_volume_sources(self) -> List[str]:
        """
        Get list of volume sources from OBS.
        
        Returns:
            List[str]: List of volume source names
        """
        if not self.connected:
            return []
            
        try:
            accepted_inputs = ['wasapi_output_capture', 'wasapi_input_capture']
            response = self.ws.call(requests.GetInputList())
            inputs = []
            
            for input_info in response.getInputs():
                if input_info['inputKind'] in accepted_inputs:
                    inputs.append(input_info['inputName'])
            
            return inputs
        except Exception as e:
            self.log('error', f"Failed to get volume sources: {str(e)}")
            return []
    
    def get_volume(self, source_name: str) -> Optional[float]:
        """
        Get volume of a source in OBS.
        
        Args:
            source_name (str): Source name
            
        Returns:
            Optional[float]: Volume in dB or None if error
        """
        if not self.connected:
            return None
            
        try:
            response = self.ws.call(requests.GetInputVolume(inputName=source_name))
            return response.getInputVolumeDb()
        except Exception as e:
            self.log('error', f"Failed to get volume for '{source_name}': {str(e)}")
            return None
    
    def set_volume(self, source_name: str, volume_db: float) -> bool:
        """
        Set volume of a source in OBS.
        
        Args:
            source_name (str): Source name
            volume_db (float): Volume in dB
            
        Returns:
            bool: True if successful
        """
        if not self.connected:
            self.log('error', "Cannot set volume: Not connected to OBS")
            return False
            
        try:
            self.ws.call(requests.SetInputVolume(inputName=source_name, inputVolumeDb=volume_db))
            self.log('debug', f"Volume set for '{source_name}': {volume_db} dB")
            return True
        except Exception as e:
            self.log('error', f"Failed to set volume for '{source_name}': {str(e)}")
            return False
    
    def pot_to_db(self, pot_value: int) -> Tuple[int, float]:
        """
        Convert potentiometer value to dB.
        
        Args:
            pot_value (int): Potentiometer value (0-1023)
            
        Returns:
            Tuple[int, float]: (clamped pot value, dB value)
        """
        min_pot = 94
        max_pot = 1022
        min_db = -100
        max_db = 0
        
        # Clamp pot value
        if pot_value <= min_pot:
            return min_pot, min_db
        elif pot_value >= max_pot:
            return max_pot, max_db
        
        # Logarithmic conversion for more natural volume control
        db = ((math.log10(pot_value - min_pot + 1)) / 
              (math.log10(max_pot - min_pot + 1))) * (max_db - min_db) + min_db
        
        return pot_value, db
    
    def is_connected(self) -> bool:
        """
        Check if connected to OBS.
        
        Returns:
            bool: True if connected
        """
        return self.connected 