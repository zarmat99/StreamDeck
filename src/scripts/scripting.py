"""
Scripting module for StreamDeck application.
Handles script execution and management for custom button actions.
"""
import time
import pyautogui
import json
import os
import threading
from typing import List, Dict, Any, Optional

# Reduce default pause to make scripting more responsive
pyautogui.PAUSE = 0.01

# List of supported commands
COMMAND_LIST = ["press", "hold", "release", "combo", "write", "delay", "move", "click"]

class ScriptManager:
    """
    Manages script creation, loading, saving and execution.
    
    Attributes:
        scripts (dict): Dictionary of available scripts
        scripts_path (str): Path to the scripts configuration file
        logger (Optional): Logger instance for logging events
        running_scripts (set): Set of currently running scripts
    """
    def __init__(self, scripts_path: str = 'config/scripts.json', logger=None):
        """
        Initialize the script manager.
        
        Args:
            scripts_path (str): Path to the scripts configuration file
            logger: Optional logger instance for logging events
        """
        self.scripts_path = scripts_path
        self.scripts = {}
        self.logger = logger
        self.running_scripts = set()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(scripts_path), exist_ok=True)
        
        # Load existing scripts
        self.load_scripts()
    
    def log(self, level: str, message: str):
        """Log a message if logger is available."""
        if self.logger:
            if hasattr(self.logger, level):
                getattr(self.logger, level)(message)
    
    def save_scripts(self):
        """Save scripts to the configuration file."""
        try:
            with open(self.scripts_path, 'w') as file:
                json.dump(self.scripts, file, indent=2)
            self.log('debug', f"Scripts saved to {self.scripts_path}")
            return True
        except Exception as e:
            self.log('error', f"Error saving scripts: {str(e)}")
            return False

    def load_scripts(self):
        """
        Load scripts from the configuration file.
        
        Returns:
            dict: The loaded scripts
        """
        try:
            with open(self.scripts_path, 'r') as file:
                self.scripts = json.load(file)
            self.log('debug', f"Scripts loaded from {self.scripts_path}")
        except FileNotFoundError:
            self.log('info', f"Scripts file not found, creating new one")
            self.save_scripts()
        except json.JSONDecodeError:
            self.log('error', f"Invalid JSON in scripts file, creating new one")
            self.save_scripts()
        except Exception as e:
            self.log('error', f"Error loading scripts: {str(e)}")
        
        return self.scripts

    def create_script(self, name: str, commands: List[str] = None) -> bool:
        """
        Create a new script with the given name and commands.
        
        Args:
            name (str): Name of the script
            commands (List[str], optional): List of commands for the script
            
        Returns:
            bool: True if script was created successfully
        """
        if not name:
            self.log('error', "Cannot create script without a name")
            return False
            
        if name in self.scripts:
            self.log('warning', f"Overwriting existing script '{name}'")
            
        self.scripts[name] = commands or []
        self.save_scripts()
        self.log('info', f"Script '{name}' created with {len(commands or [])} commands")
        return True
    
    def delete_script(self, name: str) -> bool:
        """
        Delete a script by name.
        
        Args:
            name (str): Name of the script to delete
            
        Returns:
            bool: True if script was deleted successfully
        """
        if name in self.scripts:
            del self.scripts[name]
            self.save_scripts()
            self.log('info', f"Script '{name}' deleted")
            return True
        
        self.log('warning', f"Script '{name}' not found, cannot delete")
        return False
    
    def get_script(self, name: str) -> Optional[List[str]]:
        """
        Get a script by name.
        
        Args:
            name (str): Name of the script to get
            
        Returns:
            Optional[List[str]]: The script commands or None if not found
        """
        if name in self.scripts:
            return self.scripts[name]
        
        self.log('warning', f"Script '{name}' not found")
        return None
    
    def execute_script(self, script_name: str, async_execution: bool = False) -> bool:
        """
        Execute a script by name.
        
        Args:
            script_name (str): Name of the script to execute
            async_execution (bool): Whether to run the script asynchronously
            
        Returns:
            bool: True if script execution started successfully
        """
        if script_name in self.running_scripts:
            self.log('warning', f"Script '{script_name}' is already running")
            return False
            
        script = self.get_script(script_name)
        if not script:
            return False
        
        if async_execution:
            thread = threading.Thread(
                target=self._execute_script_commands,
                args=(script_name, script),
                daemon=True
            )
            thread.start()
            return True
        else:
            return self._execute_script_commands(script_name, script)
    
    def _execute_script_commands(self, script_name: str, commands: List[str]) -> bool:
        """
        Execute a list of script commands.
        
        Args:
            script_name (str): Name of the script being executed
            commands (List[str]): List of commands to execute
            
        Returns:
            bool: True if script executed successfully
        """
        if not commands:
            self.log('warning', f"Script '{script_name}' has no commands")
            return False
            
        self.running_scripts.add(script_name)
        self.log('info', f"Executing script '{script_name}'")
        
        try:
            for command in commands:
                # Skip empty commands
                if not command.strip():
                    continue
                    
                if command.startswith("press "):
                    key = command[len("press "):].strip()
                    pyautogui.press(key)
                    
                elif command.startswith("hold "):
                    key = command[len("hold "):].strip()
                    pyautogui.keyDown(key)
                    
                elif command.startswith("release "):
                    key = command[len("release "):].strip()
                    pyautogui.keyUp(key)
                    
                elif command.startswith("combo "):
                    keys = command[len("combo "):].strip().split("$")
                    # Hold all keys first, then release them all
                    for key in keys:
                        if key.strip():
                            pyautogui.keyDown(key.strip())
                    for key in reversed(keys):  # Release in reverse order
                        if key.strip():
                            pyautogui.keyUp(key.strip())
                            
                elif command.startswith("write "):
                    text = command[len("write "):].strip()
                    pyautogui.write(text)
                    
                elif command.startswith("delay "):
                    delay_time = float(command[len("delay "):].strip())
                    time.sleep(delay_time)
                    
                elif command.startswith("move "):
                    coords = command[len("move "):].strip().split(',')
                    if len(coords) == 2:
                        try:
                            x, y = int(coords[0]), int(coords[1])
                            pyautogui.moveTo(x, y)
                        except ValueError:
                            self.log('error', f"Invalid move coordinates: {coords}")
                            
                elif command.startswith("click "):
                    params = command[len("click "):].strip().split(',')
                    if len(params) >= 1:
                        button = params[0].strip()
                        if button in ['left', 'right', 'middle']:
                            if len(params) >= 3:
                                try:
                                    x, y = int(params[1]), int(params[2])
                                    pyautogui.click(x, y, button=button)
                                except ValueError:
                                    self.log('error', f"Invalid click coordinates: {params[1:]}")
                            else:
                                pyautogui.click(button=button)
                else:
                    self.log('warning', f"Unknown command: {command}")
                    
            self.log('info', f"Script '{script_name}' executed successfully")
            return True
        except Exception as e:
            self.log('error', f"Error executing script '{script_name}': {str(e)}")
            return False
        finally:
            self.running_scripts.discard(script_name)


# Function to transform a write command into a combo command (legacy support)
def transform_to_combo(command):
    """
    Transform a write command to a series of key presses for compatibility.
    
    Args:
        command (str): The write command to transform
        
    Returns:
        str: The transformed combo command
    """
    command_tmp = ""
    for char in command[len("write "):]:
        command_tmp += "$" + char
    return command_tmp


# Legacy function for backward compatibility
def execute_script(script):
    """
    Legacy function to execute a script.
    
    Args:
        script (List[str]): List of commands to execute
    """
    manager = ScriptManager()
    manager._execute_script_commands("legacy_script", script)


# Legacy function for backward compatibility
def save_scripts(scripts):
    """
    Legacy function to save scripts.
    
    Args:
        scripts (Dict): Dictionary of scripts to save
    """
    with open('scripts.json', 'w') as file:
        json.dump(scripts, file, indent=2)


# Legacy function for backward compatibility
def load_scripts():
    """
    Legacy function to load scripts.
    
    Returns:
        Dict: The loaded scripts
    """
    dictionary = {}
    try:
        with open("scripts.json", 'r') as file:
            dictionary = json.load(file)
    except FileNotFoundError:
        print("Scripts file not found")
    return dictionary


# Legacy function for backward compatibility
def create_script(scripts):
    """
    Legacy function to create a script interactively.
    
    Args:
        scripts (Dict): Dictionary of existing scripts
        
    Returns:
        Dict: The updated scripts dictionary
    """
    script = []
    command = ""
    name = input("name: ")
    while command != "exit":
        command = input("key: ")
        script.append(command)
    script.pop(-1)
    scripts[name] = script
    return scripts 