"""
Configuration manager for the StreamDeck application.
Handles loading, saving, and secure storage of configuration data.
"""
import json
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ConfigManager:
    """
    Manages application configuration with secure password storage.
    
    Attributes:
        config_path (str): Path to the main configuration file
        encryption_key (bytes): Encryption key for sensitive data
    """
    def __init__(self, config_dir='config'):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir (str): Directory to store configuration files
        """
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
        
        self.config_path = os.path.join(config_dir, 'settings.json')
        self.mapping_path = os.path.join(config_dir, 'mapping.json')
        self.scripts_path = os.path.join(config_dir, 'scripts.json')
        
        # Generate encryption key from a fixed salt for simplicity
        # For production, use a more secure approach with a properly stored key
        salt = b'streamdeck_salt'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        self.encryption_key = base64.urlsafe_b64encode(kdf.derive(b'streamdeck_app'))
        self.cipher = Fernet(self.encryption_key)
        
        # Default configuration
        self.settings = {
            'connection': {
                'obs_data': {
                    'host': 'localhost',
                    'port': '4455',
                    'password': ''  # Will be stored encrypted
                },
                'serial_data': {
                    'com_port': None,
                    'baud_rate': '9600'
                }
            },
            'online': {},
            'script': {},
            'mapping': {
                "B0": None, "B1": None, "B2": None, "B3": None,
                "P0": None, "P1": None, "P2": None, "P3": None,
                "G0": None, "G1": None, "G2": None, "G3": None
            },
            'ui': {
                'theme': 'dark',
                'font_size': 'medium'
            }
        }
        
        # Initialize configuration files if they don't exist
        self.load_settings()
        self.load_mapping()
        self.load_scripts()
    
    def encrypt_password(self, password):
        """
        Encrypt a password string.
        
        Args:
            password (str): Password to encrypt
            
        Returns:
            str: Base64 encoded encrypted password
        """
        if not password:
            return ''
        encrypted = self.cipher.encrypt(password.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_password(self, encrypted_password):
        """
        Decrypt an encrypted password.
        
        Args:
            encrypted_password (str): Encrypted password to decrypt
            
        Returns:
            str: Decrypted password or empty string if invalid
        """
        if not encrypted_password:
            return ''
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_password)
            return self.cipher.decrypt(encrypted).decode()
        except Exception:
            return ''
    
    def save_settings(self):
        """Save settings to the configuration file with encrypted password."""
        # Create a copy to avoid modifying the original
        settings_copy = json.loads(json.dumps(self.settings))
        
        # Encrypt the password before saving
        if settings_copy['connection']['obs_data']['password']:
            plain_password = settings_copy['connection']['obs_data']['password']
            if not plain_password.startswith('encrypted:'):
                settings_copy['connection']['obs_data']['password'] = 'encrypted:' + self.encrypt_password(plain_password)
        
        with open(self.config_path, 'w') as file:
            json.dump(settings_copy, file, indent=2)
    
    def load_settings(self):
        """
        Load settings from the configuration file, decrypting sensitive data.
        
        Returns:
            dict: The loaded settings
        """
        try:
            with open(self.config_path, 'r') as file:
                loaded_settings = json.load(file)
                
                # Decrypt password if it's encrypted
                if loaded_settings['connection']['obs_data']['password'] and \
                   loaded_settings['connection']['obs_data']['password'].startswith('encrypted:'):
                    encrypted = loaded_settings['connection']['obs_data']['password'][10:]  # Remove 'encrypted:' prefix
                    loaded_settings['connection']['obs_data']['password'] = self.decrypt_password(encrypted)
                
                self.settings = loaded_settings
        except FileNotFoundError:
            # Create the file if it doesn't exist
            self.save_settings()
        except json.JSONDecodeError:
            # Handle corrupted file by creating a new one
            self.save_settings()
        
        return self.settings
    
    def save_mapping(self):
        """Save button mapping configuration to a separate file."""
        with open(self.mapping_path, 'w') as file:
            json.dump(self.settings['mapping'], file, indent=2)
    
    def load_mapping(self):
        """
        Load button mapping from file.
        
        Returns:
            dict: The loaded mapping
        """
        try:
            with open(self.mapping_path, 'r') as file:
                self.settings['mapping'] = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_mapping()
        
        return self.settings['mapping']
    
    def save_scripts(self):
        """Save scripts configuration to a separate file."""
        with open(self.scripts_path, 'w') as file:
            json.dump(self.settings['script'], file, indent=2)
    
    def load_scripts(self):
        """
        Load scripts from file.
        
        Returns:
            dict: The loaded scripts
        """
        try:
            with open(self.scripts_path, 'r') as file:
                self.settings['script'] = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_scripts()
        
        return self.settings['script'] 