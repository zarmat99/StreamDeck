"""
Logger module for StreamDeck application.
Provides a centralized logging mechanism with multiple output targets.
"""
import logging
from logging.handlers import RotatingFileHandler
import os

class Logger:
    """
    A configurable logger that can output to file and console.
    
    Attributes:
        logger (logging.Logger): The underlying logger instance
        levels (list): The logging levels that are enabled
    """
    def __init__(self, levels, filename=None, console=False):
        """
        Initialize the logger with specified configuration.
        
        Args:
            levels (list): List of logging levels to enable (debug, info, warning, error, critical)
            filename (str, optional): Log file name. If provided, logs will be written to this file
            console (bool, optional): Whether to output logs to console
        
        Raises:
            ValueError: If an invalid logging level is provided
        """
        self.accepted_levels = ['debug', 'info', 'warning', 'error', 'critical']
        self.levels = levels
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] > %(message)s')

        for level in self.levels:
            if level not in self.accepted_levels:
                raise ValueError(f'logging level {level} not valid. Please, select an accepted logging level: {self.accepted_levels}')

        if filename:
            # Ensure logs directory exists
            os.makedirs('logs', exist_ok=True)
            file_path = 'logs/' + filename
            file_handler = RotatingFileHandler(file_path, maxBytes=10*1024*1024, backupCount=5)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        if console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def debug(self, message):
        """Log a debug message if debug level is enabled."""
        if 'debug' in self.levels:
            self.logger.debug(message)

    def info(self, message):
        """Log an info message if info level is enabled."""
        if 'info' in self.levels:
            self.logger.info(message)

    def warning(self, message):
        """Log a warning message if warning level is enabled."""
        if 'warning' in self.levels:
            self.logger.warning(message)

    def error(self, message):
        """Log an error message if error level is enabled."""
        if 'error' in self.levels:
            self.logger.error(message)

    def critical(self, message):
        """Log a critical message if critical level is enabled."""
        if 'critical' in self.levels:
            self.logger.critical(message) 