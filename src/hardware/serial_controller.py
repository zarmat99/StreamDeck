"""
Serial controller for StreamDeck hardware.
Handles communication with the Arduino-based StreamDeck device.
"""
import time
import threading
import serial
import serial.tools.list_ports
from typing import List, Dict, Any, Optional, Callable, Tuple

class SerialController:
    """
    Controller for serial communication with StreamDeck hardware.
    
    Attributes:
        ser (serial.Serial): Serial connection
        port (str): Serial port
        baud_rate (int): Serial baud rate
        connected (bool): Connection status
        logger: Optional logger for events
        callbacks (dict): Event callbacks
    """
    def __init__(self, port: str = None, baud_rate: int = 9600, logger=None):
        """
        Initialize serial controller.
        
        Args:
            port (str): Serial port (COM port)
            baud_rate (int): Serial baud rate
            logger: Optional logger for events
        """
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.connected = False
        self.logger = logger
        self.callbacks = {}
        
        # Last received data
        self.last_data = ""
        
        # Event listener thread
        self._listener_thread = None
        self._stop_listener = threading.Event()
        
        # Command queue for reliable communication
        self._command_queue = []
        self._command_lock = threading.Lock()
        self._command_thread = None
        self._stop_command = threading.Event()
    
    def log(self, level: str, message: str):
        """Log a message if logger is available."""
        if self.logger and hasattr(self.logger, level):
            getattr(self.logger, level)(message)
    
    def list_ports(self) -> List[Tuple[str, str]]:
        """
        List available serial ports.
        
        Returns:
            List[Tuple[str, str]]: List of (port, description) tuples
        """
        return [(port.device, port.description) for port in serial.tools.list_ports.comports()]
    
    def connect(self) -> bool:
        """
        Connect to StreamDeck hardware.
        
        Returns:
            bool: True if connection successful
        """
        if self.connected:
            return True
            
        if not self.port:
            self.log('error', "Cannot connect: No port specified")
            return False
            
        try:
            # Create serial connection
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            
            # Wait for Arduino reset after connection
            time.sleep(2)
            
            # Start device
            if not self.start_device():
                self.log('error', "Failed to start device")
                self.ser.close()
                self.ser = None
                return False
            
            # Start event listener
            self._stop_listener.clear()
            self._listener_thread = threading.Thread(target=self._event_listener, daemon=True)
            self._listener_thread.start()
            
            # Start command processor
            self._stop_command.clear()
            self._command_thread = threading.Thread(target=self._command_processor, daemon=True)
            self._command_thread.start()
            
            self.connected = True
            self.log('info', f"Connected to StreamDeck on {self.port}")
            return True
            
        except Exception as e:
            self.log('error', f"Failed to connect to StreamDeck: {str(e)}")
            if self.ser:
                try:
                    self.ser.close()
                except Exception:
                    pass
            self.ser = None
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from StreamDeck hardware."""
        if not self.connected:
            return
            
        # Stop device
        self.stop_device()
        
        # Stop event listener
        if self._listener_thread and self._listener_thread.is_alive():
            self._stop_listener.set()
            self._listener_thread.join(timeout=1.0)
        
        # Stop command processor
        if self._command_thread and self._command_thread.is_alive():
            self._stop_command.set()
            self._command_thread.join(timeout=1.0)
        
        # Close serial connection
        try:
            if self.ser:
                self.ser.close()
        except Exception as e:
            self.log('error', f"Error disconnecting from StreamDeck: {str(e)}")
        finally:
            self.ser = None
            self.connected = False
            self.log('info', "Disconnected from StreamDeck")
    
    def reconnect(self) -> bool:
        """
        Reconnect to StreamDeck hardware.
        
        Returns:
            bool: True if reconnection successful
        """
        self.disconnect()
        time.sleep(1)  # Brief delay before reconnecting
        return self.connect()
    
    def start_device(self) -> bool:
        """
        Start the StreamDeck device.
        
        Returns:
            bool: True if start successful
        """
        if not self.ser:
            return False
            
        try:
            # Send start command
            self.ser.write(b"start\n")
            
            # Wait for response with timeout
            start_time = time.time()
            response = ""
            
            while time.time() - start_time < 3:  # 3 second timeout
                if self.ser.in_waiting:
                    response += self.ser.readline().decode().strip()
                    if response == "start ok":
                        return True
                time.sleep(0.1)
            
            self.log('error', f"Invalid response to start command: {response}")
            return False
            
        except Exception as e:
            self.log('error', f"Error starting device: {str(e)}")
            return False
    
    def stop_device(self) -> bool:
        """
        Stop the StreamDeck device.
        
        Returns:
            bool: True if stop successful
        """
        if not self.ser or not self.connected:
            return False
            
        try:
            # Send stop command
            self.ser.write(b"stop\n")
            
            # Wait for response with timeout
            start_time = time.time()
            response = ""
            
            while time.time() - start_time < 3:  # 3 second timeout
                if self.ser.in_waiting:
                    response += self.ser.readline().decode().strip()
                    if response == "stop ok":
                        return True
                time.sleep(0.1)
            
            self.log('error', f"Invalid response to stop command: {response}")
            return False
            
        except Exception as e:
            self.log('error', f"Error stopping device: {str(e)}")
            return False
    
    def _event_listener(self):
        """Event listener thread function."""
        while not self._stop_listener.is_set():
            if self.ser and self.connected:
                try:
                    # Read data from serial
                    if self.ser.in_waiting:
                        data = self.ser.readline().decode().strip()
                        if data:
                            self.last_data = data
                            self._process_data(data)
                except Exception as e:
                    self.log('error', f"Serial read error: {str(e)}")
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
                        self.log('error', "Failed to reconnect to StreamDeck after multiple attempts")
                        self._stop_listener.set()
            
            # Sleep to avoid high CPU usage
            time.sleep(0.01)
    
    def _command_processor(self):
        """Command processor thread function."""
        while not self._stop_command.is_set():
            # Process command queue
            command = None
            with self._command_lock:
                if self._command_queue:
                    command = self._command_queue.pop(0)
            
            if command:
                self._send_command(command)
            
            # Sleep to avoid high CPU usage
            time.sleep(0.01)
    
    def _send_command(self, command: str) -> bool:
        """
        Send a command to the StreamDeck device.
        
        Args:
            command (str): Command to send
            
        Returns:
            bool: True if command sent successfully
        """
        if not self.ser or not self.connected:
            return False
            
        try:
            # Send command
            self.ser.write(f"{command}\n".encode())
            self.log('debug', f"Sent command: {command}")
            return True
        except Exception as e:
            self.log('error', f"Error sending command '{command}': {str(e)}")
            return False
    
    def send_command(self, command: str, priority: bool = False):
        """
        Queue a command to send to the StreamDeck device.
        
        Args:
            command (str): Command to send
            priority (bool): Whether to put command at front of queue
        """
        with self._command_lock:
            if priority:
                self._command_queue.insert(0, command)
            else:
                self._command_queue.append(command)
    
    def _process_data(self, data: str):
        """
        Process data received from StreamDeck.
        
        Args:
            data (str): Data received from serial
        """
        self.log('debug', f"Received: {data}")
        
        # Handle standard events
        if data == "StartRecord":
            self._trigger_callback('record_start')
        elif data == "StopRecord":
            self._trigger_callback('record_stop')
        elif data == "StartStream":
            self._trigger_callback('stream_start')
        elif data == "StopStream":
            self._trigger_callback('stream_stop')
        elif data.startswith("ChangeScene"):
            parts = data.split()
            if len(parts) >= 2:
                self._trigger_callback('scene_change', parts[1])
        elif data.startswith("SetInputVolume"):
            parts = data.split()
            if len(parts) >= 3:
                self._trigger_callback('volume_change', parts[1], int(parts[2]))
        elif data.startswith("ExecuteScript"):
            parts = data.split()
            if len(parts) >= 2:
                self._trigger_callback('execute_script', parts[1])
        else:
            # Generic data event
            self._trigger_callback('data', data)
    
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
    
    def set_led(self, led_index: int, state: bool) -> bool:
        """
        Set LED state.
        
        Args:
            led_index (int): LED index (0-1)
            state (bool): LED state (True=on, False=off)
            
        Returns:
            bool: True if command queued successfully
        """
        if led_index not in [0, 1]:
            return False
            
        led_type = "Stream" if led_index == 0 else "Record"
        state_str = "On" if state else "Off"
        command = f"{led_type}{state_str}Led"
        
        self.send_command(command)
        return True
    
    def enable_dumb_mode(self):
        """Enable dumb mode (ignores button presses)."""
        self.send_command("DumbMode", priority=True)
    
    def disable_dumb_mode(self):
        """Disable dumb mode."""
        self.send_command("NormalOperation", priority=True)
    
    def is_connected(self) -> bool:
        """
        Check if connected to StreamDeck.
        
        Returns:
            bool: True if connected
        """
        return self.connected 