"""
Settings Page for StreamDeck application.
Provides interface for configuring application settings.
"""
import customtkinter
import os
import threading
from typing import Dict, Any, Optional

from ui.base_page import BasePage

class SettingsPage(BasePage):
    """
    Settings page for configuring general application settings.
    
    Provides controls for appearance, theme, logs, and other application settings.
    """
    def __init__(self, parent):
        """
        Initialize the settings page.
        
        Args:
            parent: Parent application
        """
        super().__init__(parent)
        self.app = parent
        
        # StringVars for settings
        self.vars = {
            'ui': {
                'theme': customtkinter.StringVar(value=self.app.config.settings.get('ui', {}).get('theme', 'dark')),
                'font_size': customtkinter.StringVar(value=self.app.config.settings.get('ui', {}).get('font_size', 'medium'))
            },
            'logs': {
                'level': customtkinter.StringVar(value='info'),
                'file_enabled': customtkinter.BooleanVar(value=True),
                'console_enabled': customtkinter.BooleanVar(value=True),
                'max_files': customtkinter.StringVar(value='5')
            }
        }
        
        # Theme options
        self.theme_options = ["dark", "light", "system"]
        self.font_size_options = ["small", "medium", "large"]
        
        # Log level options
        self.log_level_options = ["debug", "info", "warning", "error", "critical"]
    
    def change_window_name(self):
        """Change window title for this page."""
        self.parent.title("StreamDeck - Settings")
    
    def create_widgets(self):
        """Create widgets for the settings page."""
        # Title frame
        self.add_title("Application Settings")
        
        # Create tab view
        self.tabs["settings"] = customtkinter.CTkTabview(self.frames["body"])
        
        # Add tabs
        self.tabs["settings"].add("Appearance")
        self.tabs["settings"].add("Logs")
        self.tabs["settings"].add("About")
        
        # ===== Appearance Tab =====
        appearance_tab = self.tabs["settings"].tab("Appearance")
        
        # Theme section
        self.labels["theme"] = customtkinter.CTkLabel(
            appearance_tab,
            text="Theme:",
            font=customtkinter.CTkFont(size=15, weight="bold")
        )
        
        self.comboboxes["theme"] = customtkinter.CTkComboBox(
            appearance_tab,
            values=self.theme_options,
            variable=self.vars["ui"]["theme"],
            command=self.theme_changed
        )
        
        # Font size section
        self.labels["font_size"] = customtkinter.CTkLabel(
            appearance_tab,
            text="Font Size:",
            font=customtkinter.CTkFont(size=15, weight="bold")
        )
        
        self.comboboxes["font_size"] = customtkinter.CTkComboBox(
            appearance_tab,
            values=self.font_size_options,
            variable=self.vars["ui"]["font_size"],
            command=self.font_size_changed
        )
        
        # Preview frame
        self.frames["preview"] = customtkinter.CTkFrame(appearance_tab)
        
        self.labels["preview_title"] = customtkinter.CTkLabel(
            self.frames["preview"],
            text="Preview",
            font=customtkinter.CTkFont(size=18, weight="bold")
        )
        
        self.labels["preview_text"] = customtkinter.CTkLabel(
            self.frames["preview"],
            text="This is how text will appear in the application.",
            font=customtkinter.CTkFont(size=13)
        )
        
        self.buttons["preview_button"] = customtkinter.CTkButton(
            self.frames["preview"],
            text="Sample Button",
            width=150
        )
        
        # ===== Logs Tab =====
        logs_tab = self.tabs["settings"].tab("Logs")
        
        # Log level section
        self.labels["log_level"] = customtkinter.CTkLabel(
            logs_tab,
            text="Log Level:",
            font=customtkinter.CTkFont(size=15, weight="bold")
        )
        
        self.comboboxes["log_level"] = customtkinter.CTkComboBox(
            logs_tab,
            values=self.log_level_options,
            variable=self.vars["logs"]["level"],
            command=self.log_level_changed
        )
        
        # Log file section
        self.switches["file_logging"] = customtkinter.CTkSwitch(
            logs_tab,
            text="Enable file logging",
            variable=self.vars["logs"]["file_enabled"],
            command=self.log_settings_changed
        )
        
        # Console logging section
        self.switches["console_logging"] = customtkinter.CTkSwitch(
            logs_tab,
            text="Enable console logging",
            variable=self.vars["logs"]["console_enabled"],
            command=self.log_settings_changed
        )
        
        # Max log files
        self.labels["max_files"] = customtkinter.CTkLabel(
            logs_tab,
            text="Maximum log files:",
            font=customtkinter.CTkFont(size=15)
        )
        
        self.entries["max_files"] = customtkinter.CTkEntry(
            logs_tab,
            textvariable=self.vars["logs"]["max_files"],
            width=100
        )
        
        # Log file location
        log_file_path = os.path.abspath(os.path.join(os.getcwd(), "logs"))
        self.labels["log_path"] = customtkinter.CTkLabel(
            logs_tab,
            text=f"Log file location: {log_file_path}",
            font=customtkinter.CTkFont(size=13)
        )
        
        # Open logs button
        self.buttons["open_logs"] = customtkinter.CTkButton(
            logs_tab,
            text="Open Logs Folder",
            command=self.open_logs_folder
        )
        
        # Clear logs button
        self.buttons["clear_logs"] = customtkinter.CTkButton(
            logs_tab,
            text="Clear All Logs",
            fg_color="red",
            hover_color="#8B0000",
            command=self.clear_logs
        )
        
        # ===== About Tab =====
        about_tab = self.tabs["settings"].tab("About")
        
        self.labels["app_title"] = customtkinter.CTkLabel(
            about_tab,
            text="StreamDeck Control",
            font=customtkinter.CTkFont(size=24, weight="bold")
        )
        
        self.labels["app_version"] = customtkinter.CTkLabel(
            about_tab,
            text="Version 2.0.0",
            font=customtkinter.CTkFont(size=16)
        )
        
        self.labels["app_description"] = customtkinter.CTkLabel(
            about_tab,
            text="A control application for the StreamDeck hardware\nto interface with OBS Studio and run custom scripts.",
            font=customtkinter.CTkFont(size=14)
        )
        
        self.labels["copyright"] = customtkinter.CTkLabel(
            about_tab,
            text="© 2023 StreamDeck Control",
            font=customtkinter.CTkFont(size=12)
        )
        
        # Bottom buttons
        self.buttons["save"] = customtkinter.CTkButton(
            self.frames["bottom"],
            text="Save Settings",
            command=self.save_settings
        )
        
        self.buttons["back"] = customtkinter.CTkButton(
            self.frames["bottom"],
            text="Back",
            command=self.back_to_previous
        )
        
        # Status message
        self.add_status()
    
    def configure_widgets(self):
        """Configure widgets layout."""
        # Configure tab view
        self.tabs["settings"].set("Appearance")  # Default tab
        
        # Configure appearance tab
        appearance_tab = self.tabs["settings"].tab("Appearance")
        appearance_tab.grid_columnconfigure(0, weight=1)
        appearance_tab.grid_columnconfigure(1, weight=2)
        
        # Configure logs tab
        logs_tab = self.tabs["settings"].tab("Logs")
        logs_tab.grid_columnconfigure(0, weight=1)
        logs_tab.grid_columnconfigure(1, weight=2)
        
        # Configure about tab
        about_tab = self.tabs["settings"].tab("About")
        about_tab.grid_columnconfigure(0, weight=1)
    
    def grid_widgets(self):
        """Position widgets in the page."""
        # Tab view takes whole body area
        self.tabs["settings"].pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== Appearance Tab =====
        appearance_tab = self.tabs["settings"].tab("Appearance")
        
        row = 0
        # Theme section
        self.labels["theme"].grid(row=row, column=0, padx=20, pady=(20, 5), sticky="w")
        self.comboboxes["theme"].grid(row=row, column=1, padx=10, pady=(20, 5), sticky="ew")
        row += 1
        
        # Font size section
        self.labels["font_size"].grid(row=row, column=0, padx=20, pady=5, sticky="w")
        self.comboboxes["font_size"].grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        row += 1
        
        # Spacer
        spacer = customtkinter.CTkFrame(appearance_tab, height=20, fg_color="transparent")
        spacer.grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1
        
        # Preview frame
        self.frames["preview"].grid(row=row, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.frames["preview"].grid_columnconfigure(0, weight=1)
        
        # Preview content
        self.labels["preview_title"].pack(pady=(15, 5))
        self.labels["preview_text"].pack(pady=5)
        self.buttons["preview_button"].pack(pady=(5, 15))
        
        # ===== Logs Tab =====
        logs_tab = self.tabs["settings"].tab("Logs")
        
        row = 0
        # Log level section
        self.labels["log_level"].grid(row=row, column=0, padx=20, pady=(20, 5), sticky="w")
        self.comboboxes["log_level"].grid(row=row, column=1, padx=10, pady=(20, 5), sticky="ew")
        row += 1
        
        # Log file section
        self.switches["file_logging"].grid(row=row, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        row += 1
        
        # Console logging section
        self.switches["console_logging"].grid(row=row, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        row += 1
        
        # Max log files
        self.labels["max_files"].grid(row=row, column=0, padx=20, pady=5, sticky="w")
        self.entries["max_files"].grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1
        
        # Log file location
        self.labels["log_path"].grid(row=row, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="w")
        row += 1
        
        # Log buttons
        button_frame = customtkinter.CTkFrame(logs_tab, fg_color="transparent")
        button_frame.grid(row=row, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        self.buttons["open_logs"].grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")
        self.buttons["clear_logs"].grid(row=0, column=1, padx=(10, 0), pady=5, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # ===== About Tab =====
        about_tab = self.tabs["settings"].tab("About")
        
        # Center content
        self.labels["app_title"].pack(pady=(40, 5))
        self.labels["app_version"].pack(pady=5)
        self.labels["app_description"].pack(pady=20)
        self.labels["copyright"].pack(pady=(40, 20))
        
        # Bottom buttons
        self.buttons["save"].pack(side="right", padx=10)
        self.buttons["back"].pack(side="left", padx=10)
    
    def theme_changed(self, selection):
        """
        Handle theme selection change.
        
        Args:
            selection (str): Selected theme
        """
        # Update app theme
        customtkinter.set_appearance_mode(selection)
        
        # Update configuration
        self.app.config.settings.setdefault('ui', {})['theme'] = selection
    
    def font_size_changed(self, selection):
        """
        Handle font size selection change.
        
        Args:
            selection (str): Selected font size
        """
        # Update configuration
        self.app.config.settings.setdefault('ui', {})['font_size'] = selection
        
        # Update preview based on selection
        font_sizes = {
            "small": {"title": 16, "text": 11, "button": 11},
            "medium": {"title": 18, "text": 13, "button": 13},
            "large": {"title": 20, "text": 15, "button": 15}
        }
        
        sizes = font_sizes.get(selection, font_sizes["medium"])
        
        # Update preview text
        self.labels["preview_title"].configure(font=customtkinter.CTkFont(size=sizes["title"], weight="bold"))
        self.labels["preview_text"].configure(font=customtkinter.CTkFont(size=sizes["text"]))
        self.buttons["preview_button"].configure(font=customtkinter.CTkFont(size=sizes["button"]))
    
    def log_level_changed(self, selection):
        """
        Handle log level selection change.
        
        Args:
            selection (str): Selected log level
        """
        # Update configuration
        self.app.config.settings.setdefault('logs', {})['level'] = selection
    
    def log_settings_changed(self):
        """Handle log settings change."""
        # Update configuration
        self.app.config.settings.setdefault('logs', {})['file_enabled'] = self.vars["logs"]["file_enabled"].get()
        self.app.config.settings.setdefault('logs', {})['console_enabled'] = self.vars["logs"]["console_enabled"].get()
    
    def open_logs_folder(self):
        """Open the logs folder in file explorer."""
        log_dir = os.path.abspath(os.path.join(os.getcwd(), "logs"))
        
        # Create directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Open folder in file explorer
        if os.name == 'nt':  # Windows
            os.startfile(log_dir)
        elif os.name == 'posix':  # macOS and Linux
            import subprocess
            opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
            subprocess.call([opener, log_dir])
    
    def clear_logs(self):
        """Clear all log files."""
        # Get log directory
        log_dir = os.path.abspath(os.path.join(os.getcwd(), "logs"))
        
        # Check if directory exists
        if not os.path.exists(log_dir):
            self.show_status("No logs to clear", "orange")
            return
        
        # Confirm before clearing
        confirm = customtkinter.CTkInputDialog(
            text="Type 'clear' to confirm clearing all logs:",
            title="Confirm Clear Logs"
        )
        response = confirm.get_input()
        
        if response == "clear":
            # Delete all log files
            deleted = 0
            try:
                for file in os.listdir(log_dir):
                    if file.endswith('.log'):
                        os.remove(os.path.join(log_dir, file))
                        deleted += 1
                
                self.show_status(f"Cleared {deleted} log files", "green")
            except Exception as e:
                self.show_status(f"Error clearing logs: {str(e)}", "red")
        else:
            self.show_status("Log clearing cancelled", "orange")
    
    def save_settings(self):
        """Save all settings."""
        # Process max log files
        try:
            max_files = int(self.vars["logs"]["max_files"].get())
            if max_files < 1:
                raise ValueError("Invalid number")
            self.app.config.settings.setdefault('logs', {})['max_files'] = max_files
        except ValueError:
            self.show_status("Invalid max files value. Using default: 5", "orange")
            self.vars["logs"]["max_files"].set("5")
            self.app.config.settings.setdefault('logs', {})['max_files'] = 5
        
        # Save all settings
        self.app.save_all_settings()
        
        # Update logger if needed
        self._update_logger()
        
        # Show success message
        self.show_status("Settings saved successfully", "green")
    
    def _update_logger(self):
        """Update logger with new settings."""
        # Get configured log level
        log_level = self.app.config.settings.get('logs', {}).get('level', 'info')
        file_enabled = self.app.config.settings.get('logs', {}).get('file_enabled', True)
        console_enabled = self.app.config.settings.get('logs', {}).get('console_enabled', True)
        
        # TODO: Implement logger reconfiguration if the app supports it
        pass
    
    def back_to_previous(self):
        """Go back to the previous page."""
        if hasattr(self.app, 'previous_page') and self.app.previous_page:
            self.app.show_page(self.app.previous_page)
        else:
            # Default to connection page
            self.app.show_page("connection") 