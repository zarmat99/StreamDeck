"""
Script Page for StreamDeck application.
Provides interface for managing automation scripts.
"""
import customtkinter
import os
import tkinter as tk
from typing import Dict, Any, Optional, List

from ui.base_page import BasePage

class ScriptPage(BasePage):
    """
    Script page for managing automation scripts.
    
    Allows the user to create, edit, test, and delete scripts that can be bound
    to StreamDeck buttons.
    """
    def __init__(self, parent):
        """
        Initialize the script page.
        
        Args:
            parent: Parent application
        """
        super().__init__(parent)
        self.app = parent
        
        # Widget collections that aren't in BasePage
        self.textboxes = {}
        
        # Current script
        self.current_script = None
        self.unsaved_changes = False
        
    def change_window_name(self):
        """Change window title for this page."""
        self.parent.title("StreamDeck - Script Editor")
    
    def create_widgets(self):
        """Create widgets for the script page."""
        # Title frame
        self.add_title("StreamDeck Script Editor")
        
        # Add main sections
        self.frames["script_list"] = customtkinter.CTkFrame(self.frames["body"])
        self.frames["editor"] = customtkinter.CTkFrame(self.frames["body"])
        
        # ===== Script List Section =====
        self.labels["scripts_title"] = customtkinter.CTkLabel(
            self.frames["script_list"],
            text="Available Scripts",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        
        # Script list with scrollbar
        self.frames["list_container"] = customtkinter.CTkFrame(self.frames["script_list"])
        
        # Scrollable list frame
        self.frames["scrollable_frame"] = customtkinter.CTkScrollableFrame(
            self.frames["list_container"],
            width=250,
            height=350
        )
        
        # Add new script button
        self.buttons["new_script"] = customtkinter.CTkButton(
            self.frames["script_list"],
            text="New Script",
            command=self.new_script
        )
        
        # Delete script button
        self.buttons["delete_script"] = customtkinter.CTkButton(
            self.frames["script_list"],
            text="Delete Script",
            fg_color="#dc3545",
            hover_color="#c82333",
            command=self.delete_script
        )
        
        # ===== Script Editor Section =====
        self.labels["editor_title"] = customtkinter.CTkLabel(
            self.frames["editor"],
            text="Script Editor",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        
        # Script name entry
        self.frames["name_frame"] = customtkinter.CTkFrame(self.frames["editor"])
        
        self.labels["script_name"] = customtkinter.CTkLabel(
            self.frames["name_frame"],
            text="Script Name:",
            width=100
        )
        
        self.entries["script_name"] = customtkinter.CTkEntry(
            self.frames["name_frame"],
            width=300,
            placeholder_text="Enter script name"
        )
        
        # Text editor for Python code
        self.frames["code_frame"] = customtkinter.CTkFrame(self.frames["editor"])
        
        # Create text widget with line numbers
        self.frames["text_frame"] = customtkinter.CTkFrame(self.frames["code_frame"])
        
        # Line numbers
        self.textboxes["line_numbers"] = tk.Text(
            self.frames["text_frame"],
            width=4,
            padx=4,
            pady=4,
            takefocus=0,
            border=0,
            background='#343638',
            foreground='#aaaaaa',
            font=("Courier New", 12)
        )
        
        # Code editor
        self.textboxes["code_editor"] = customtkinter.CTkTextbox(
            self.frames["text_frame"],
            width=600,
            height=400,
            font=("Courier New", 12),
            activate_scrollbars=True
        )
        
        # Insert default script template
        self.textboxes["code_editor"].insert("1.0", self.get_script_template())
        
        # Description of available functions
        self.textboxes["help_text"] = customtkinter.CTkTextbox(
            self.frames["editor"],
            width=600,
            height=100,
            font=("Courier New", 10)
        )
        
        # Insert help text
        self.textboxes["help_text"].insert("1.0", self.get_help_text())
        self.textboxes["help_text"].configure(state="disabled")
        
        # Buttons for editor actions
        self.frames["editor_buttons"] = customtkinter.CTkFrame(self.frames["editor"])
        
        self.buttons["save_script"] = customtkinter.CTkButton(
            self.frames["editor_buttons"],
            text="Save Script",
            command=self.save_script
        )
        
        self.buttons["test_script"] = customtkinter.CTkButton(
            self.frames["editor_buttons"],
            text="Test Script",
            command=self.test_script
        )
        
        # Navigation buttons
        nav_buttons = ["connection", "online", "mapping", "settings"]
        self.add_navigation_buttons(nav_buttons, self.navigate_to_page)
        
        # Status message
        self.add_status()
    
    def configure_widgets(self):
        """Configure widget layout and behavior."""
        # Configure main frames
        self.frames["script_list"].configure(corner_radius=10)
        self.frames["editor"].configure(corner_radius=10)
        
        # Configure text editor
        self.textboxes["code_editor"].configure(wrap="none")
        
        # Configure the line numbers
        self.textboxes["line_numbers"].configure(state="disabled")
        
        # Bind text editor events
        self.textboxes["code_editor"].bind("<<Modified>>", self.on_text_modified)
        self.textboxes["code_editor"].bind("<KeyRelease>", self.update_line_numbers)
        
        # Set tab width
        tab_width = 4
        font = self.textboxes["code_editor"].cget("font")
        tab_size = font[1] * tab_width
        self.textboxes["code_editor"].configure(tabs=tab_size)
    
    def grid_widgets(self):
        """Position widgets in the page."""
        # Configure body layout
        self.frames["body"].grid_columnconfigure(0, weight=1)
        self.frames["body"].grid_columnconfigure(1, weight=3)
        self.frames["body"].grid_rowconfigure(0, weight=1)
        
        # Position section frames
        self.frames["script_list"].grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.frames["editor"].grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # ===== Script List Section =====
        self.labels["scripts_title"].pack(pady=(10, 15))
        
        # Script list container
        self.frames["list_container"].pack(fill="both", expand=True, padx=10, pady=10)
        self.frames["scrollable_frame"].pack(fill="both", expand=True)
        
        # Buttons
        self.buttons["new_script"].pack(side="left", padx=10, pady=10)
        self.buttons["delete_script"].pack(side="right", padx=10, pady=10)
        
        # ===== Script Editor Section =====
        self.labels["editor_title"].pack(pady=(10, 15))
        
        # Script name
        self.frames["name_frame"].pack(fill="x", padx=10, pady=5)
        self.labels["script_name"].pack(side="left", padx=5, pady=5)
        self.entries["script_name"].pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        # Code editor
        self.frames["code_frame"].pack(fill="both", expand=True, padx=10, pady=5)
        self.frames["text_frame"].pack(fill="both", expand=True, padx=0, pady=0)
        
        # Line numbers and code editor side by side
        self.textboxes["line_numbers"].pack(side="left", fill="y")
        self.textboxes["code_editor"].pack(side="left", fill="both", expand=True)
        
        # Help text
        self.textboxes["help_text"].pack(fill="x", padx=10, pady=5)
        
        # Editor buttons
        self.frames["editor_buttons"].pack(fill="x", padx=10, pady=10)
        self.buttons["save_script"].pack(side="left", padx=10)
        self.buttons["test_script"].pack(side="right", padx=10)
        
        # Update line numbers
        self.update_line_numbers()
    
    def on_show(self):
        """Handle actions when page is shown."""
        self.load_scripts()
        self.update_line_numbers()
    
    def load_scripts(self):
        """Load scripts from the script manager."""
        # Clear previous script buttons
        for widget in self.frames["scrollable_frame"].winfo_children():
            widget.destroy()
        
        # Check if script manager exists
        if not hasattr(self.app, 'script_manager') or not self.app.script_manager:
            self.show_status("Script manager not initialized", "red")
            return
        
        # Get scripts from manager
        scripts = self.app.script_manager.scripts
        
        if not scripts:
            # No scripts
            no_scripts_label = customtkinter.CTkLabel(
                self.frames["scrollable_frame"],
                text="No scripts available",
                font=customtkinter.CTkFont(size=12),
                padx=10,
                pady=10
            )
            no_scripts_label.pack(pady=5, fill="x")
            return
        
        # Add a button for each script
        for script_name in sorted(scripts.keys()):
            script_button = customtkinter.CTkButton(
                self.frames["scrollable_frame"],
                text=script_name,
                fg_color="transparent",
                hover_color="#444",
                anchor="w",
                command=lambda name=script_name: self.load_script(name)
            )
            script_button.pack(pady=2, fill="x")
    
    def load_script(self, script_name):
        """
        Load a script into the editor.
        
        Args:
            script_name (str): Name of the script to load
        """
        # Check for unsaved changes
        if self.unsaved_changes:
            # Show confirmation dialog
            self.show_unsaved_changes_dialog(lambda: self._load_script(script_name))
            return
        
        self._load_script(script_name)
    
    def _load_script(self, script_name):
        """
        Internal method to load a script without confirmation.
        
        Args:
            script_name (str): Name of the script to load
        """
        # Set current script
        self.current_script = script_name
        
        # Set script name in entry
        self.entries["script_name"].delete(0, "end")
        self.entries["script_name"].insert(0, script_name)
        
        # Get script code
        script_code = self.app.script_manager.get_script_code(script_name)
        
        # Update editor
        self.textboxes["code_editor"].delete("1.0", "end")
        self.textboxes["code_editor"].insert("1.0", script_code)
        
        # Update line numbers
        self.update_line_numbers()
        
        # Reset unsaved changes flag
        self.unsaved_changes = False
        
        self.show_status(f"Loaded script: {script_name}", "green")
    
    def new_script(self):
        """Create a new script."""
        # Check for unsaved changes
        if self.unsaved_changes:
            # Show confirmation dialog
            self.show_unsaved_changes_dialog(self._new_script)
            return
        
        self._new_script()
    
    def _new_script(self):
        """Internal method to create a new script without confirmation."""
        # Clear current script
        self.current_script = None
        
        # Clear script name
        self.entries["script_name"].delete(0, "end")
        
        # Set template code
        self.textboxes["code_editor"].delete("1.0", "end")
        self.textboxes["code_editor"].insert("1.0", self.get_script_template())
        
        # Update line numbers
        self.update_line_numbers()
        
        # Reset unsaved changes flag
        self.unsaved_changes = False
        
        self.show_status("Created new script", "green")
    
    def save_script(self):
        """Save the current script."""
        # Get script name
        script_name = self.entries["script_name"].get().strip()
        
        # Validate script name
        if not script_name:
            self.show_status("Please enter a script name", "red")
            return
        
        # Get script code
        script_code = self.textboxes["code_editor"].get("1.0", "end-1c")
        
        # Validate script code
        if not script_code.strip():
            self.show_status("Script code cannot be empty", "red")
            return
        
        # Check if this is a rename
        is_rename = self.current_script is not None and script_name != self.current_script
        
        # If renaming, check for existing script
        if is_rename and script_name in self.app.script_manager.scripts:
            # Show confirmation dialog
            title = "Overwrite Script"
            message = f"Script '{script_name}' already exists. Overwrite?"
            self.show_confirmation_dialog(
                title, message, 
                lambda: self._save_script(script_name, script_code, is_rename)
            )
            return
        
        self._save_script(script_name, script_code, is_rename)
    
    def _save_script(self, script_name, script_code, is_rename=False):
        """
        Internal method to save a script without confirmation.
        
        Args:
            script_name (str): Name of the script
            script_code (str): Python code for the script
            is_rename (bool): Whether this is a rename operation
        """
        # Save script
        self.app.script_manager.save_script(script_name, script_code)
        
        # If renamed, delete old script
        if is_rename:
            self.app.script_manager.delete_script(self.current_script)
        
        # Update current script
        self.current_script = script_name
        
        # Reset unsaved changes flag
        self.unsaved_changes = False
        
        # Reload script list
        self.load_scripts()
        
        self.show_status(f"Saved script: {script_name}", "green")
    
    def delete_script(self):
        """Delete the current script."""
        # Check if a script is loaded
        if not self.current_script:
            self.show_status("No script selected", "red")
            return
        
        # Show confirmation dialog
        title = "Delete Script"
        message = f"Are you sure you want to delete script '{self.current_script}'?"
        self.show_confirmation_dialog(
            title, message, 
            lambda: self._delete_script(self.current_script)
        )
    
    def _delete_script(self, script_name):
        """
        Internal method to delete a script without confirmation.
        
        Args:
            script_name (str): Name of the script to delete
        """
        # Delete script
        self.app.script_manager.delete_script(script_name)
        
        # Clear editor
        self.current_script = None
        self.entries["script_name"].delete(0, "end")
        self.textboxes["code_editor"].delete("1.0", "end")
        self.textboxes["code_editor"].insert("1.0", self.get_script_template())
        
        # Update line numbers
        self.update_line_numbers()
        
        # Reset unsaved changes flag
        self.unsaved_changes = False
        
        # Reload script list
        self.load_scripts()
        
        self.show_status(f"Deleted script: {script_name}", "green")
    
    def test_script(self):
        """Test the current script."""
        # Get script code
        script_code = self.textboxes["code_editor"].get("1.0", "end-1c")
        
        # Validate script code
        if not script_code.strip():
            self.show_status("Script code cannot be empty", "red")
            return
        
        # Get script name (temporary if not saved)
        script_name = self.entries["script_name"].get().strip()
        if not script_name:
            script_name = "temp_script"
        
        # Test script
        try:
            self.app.script_manager.test_script(script_code)
            self.show_status("Script test successful", "green")
        except Exception as e:
            self.show_status(f"Script error: {str(e)}", "red")
    
    def on_text_modified(self, event=None):
        """
        Handle text modification events.
        
        Args:
            event: Tkinter event
        """
        if self.textboxes["code_editor"].edit_modified():
            # Set unsaved changes flag
            self.unsaved_changes = True
            
            # Reset modified flag
            self.textboxes["code_editor"].edit_modified(False)
    
    def update_line_numbers(self, event=None):
        """
        Update line numbers in the text editor.
        
        Args:
            event: Tkinter event
        """
        # Get number of lines
        text = self.textboxes["code_editor"].get("1.0", "end-1c")
        num_lines = text.count("\n") + 1
        
        # Update line numbers
        line_numbers = "\n".join(str(i) for i in range(1, num_lines + 1))
        
        # Update the line numbers widget
        self.textboxes["line_numbers"].configure(state="normal")
        self.textboxes["line_numbers"].delete("1.0", "end")
        self.textboxes["line_numbers"].insert("1.0", line_numbers)
        self.textboxes["line_numbers"].configure(state="disabled")
    
    def show_unsaved_changes_dialog(self, callback):
        """
        Show dialog for unsaved changes.
        
        Args:
            callback: Function to call if user chooses to proceed
        """
        dialog = customtkinter.CTkToplevel(self)
        dialog.title("Unsaved Changes")
        dialog.geometry("350x150")
        dialog.transient(self)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        label = customtkinter.CTkLabel(
            dialog,
            text="You have unsaved changes. Proceed anyway?",
            font=customtkinter.CTkFont(size=14)
        )
        label.pack(pady=(20, 20))
        
        button_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)
        
        save_button = customtkinter.CTkButton(
            button_frame,
            text="Save",
            command=lambda: self.handle_unsaved_dialog_save(dialog, callback)
        )
        save_button.pack(side="left", padx=10)
        
        discard_button = customtkinter.CTkButton(
            button_frame,
            text="Discard",
            fg_color="#dc3545",
            hover_color="#c82333",
            command=lambda: self.handle_unsaved_dialog_discard(dialog, callback)
        )
        discard_button.pack(side="right", padx=10)
        
        cancel_button = customtkinter.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="#6c757d",
            hover_color="#5a6268",
            command=lambda: dialog.destroy()
        )
        cancel_button.pack(padx=10)
    
    def handle_unsaved_dialog_save(self, dialog, callback):
        """
        Handle save button in unsaved changes dialog.
        
        Args:
            dialog: Dialog window
            callback: Function to call after saving
        """
        dialog.destroy()
        
        # Save current script
        save_result = self.save_script()
        
        # If save was successful, call the callback
        if self.unsaved_changes is False:
            callback()
    
    def handle_unsaved_dialog_discard(self, dialog, callback):
        """
        Handle discard button in unsaved changes dialog.
        
        Args:
            dialog: Dialog window
            callback: Function to call after discarding
        """
        dialog.destroy()
        
        # Reset unsaved changes flag
        self.unsaved_changes = False
        
        # Call the callback
        callback()
    
    def show_confirmation_dialog(self, title, message, callback):
        """
        Show a confirmation dialog.
        
        Args:
            title (str): Dialog title
            message (str): Dialog message
            callback: Function to call if user confirms
        """
        dialog = customtkinter.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("350x150")
        dialog.transient(self)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        label = customtkinter.CTkLabel(
            dialog,
            text=message,
            font=customtkinter.CTkFont(size=14)
        )
        label.pack(pady=(20, 20))
        
        button_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)
        
        ok_button = customtkinter.CTkButton(
            button_frame,
            text="OK",
            command=lambda: self.handle_confirmation_ok(dialog, callback)
        )
        ok_button.pack(side="left", padx=10)
        
        cancel_button = customtkinter.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="#6c757d",
            hover_color="#5a6268",
            command=lambda: dialog.destroy()
        )
        cancel_button.pack(side="right", padx=10)
    
    def handle_confirmation_ok(self, dialog, callback):
        """
        Handle OK button in confirmation dialog.
        
        Args:
            dialog: Dialog window
            callback: Function to call after confirmation
        """
        dialog.destroy()
        callback()
    
    def get_script_template(self):
        """
        Get template code for a new script.
        
        Returns:
            str: Template code
        """
        return '''# StreamDeck Script
# Available functions:
# - obs.switch_to_scene(scene_name)
# - obs.start_streaming()
# - obs.stop_streaming()
# - obs.start_recording()
# - obs.stop_recording()
# - obs.set_volume(source_name, volume)

def run(obs, hardware):
    """Script entry point"""
    # Your code here
    
    # Example: Switch to a scene
    # obs.switch_to_scene("Scene 1")
    
    # Example: Toggle streaming
    # if not obs.is_streaming():
    #     obs.start_streaming()
    # else:
    #     obs.stop_streaming()
    
    pass  # Replace with your code
'''
    
    def get_help_text(self):
        """
        Get help text for script editor.
        
        Returns:
            str: Help text
        """
        return (
            "Functions available in scripts:\n"
            "- obs.switch_to_scene(scene_name): Switch to the specified scene\n"
            "- obs.start_streaming()/stop_streaming(): Control streaming\n"
            "- obs.start_recording()/stop_recording(): Control recording\n"
            "- obs.set_volume(source_name, volume): Set volume (0.0-1.0) for source\n"
            "- hardware.set_led(button_id, color): Set LED color (R, G, B)"
        )
    
    def navigate_to_page(self, page_name):
        """
        Navigate to another page.
        
        Args:
            page_name (str): Name of the page to navigate to
        """
        # Check for unsaved changes
        if self.unsaved_changes:
            # Show confirmation dialog
            self.show_unsaved_changes_dialog(
                lambda: self.app.show_page(page_name)
            )
            return
        
        self.app.show_page(page_name) 