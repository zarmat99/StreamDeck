"""
Script Page for StreamDeck application.
Provides interface for managing automation scripts.
"""

import re
import tkinter as tk

import customtkinter

from ..base_page import BasePage


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

        # Script lists must be refreshed every time another page may have
        # created/deleted an automation.
        self.add_on_show_callback(self.on_show)

    def change_window_name(self):
        """Change window title for this page."""
        self.parent.title("StreamDeck Control - Automations")

    def create_widgets(self):
        """Create widgets for the script page."""
        # Title frame
        self.add_title("Automation Editor")

        # Add main sections
        self.frames["script_list"] = customtkinter.CTkFrame(self.frames["body"])
        self.frames["editor"] = customtkinter.CTkFrame(self.frames["body"])

        # ===== Script List Section =====
        self.labels["scripts_title"] = customtkinter.CTkLabel(
            self.frames["script_list"],
            text="Automations",
            font=customtkinter.CTkFont(size=16, weight="bold"),
        )

        # Script list with scrollbar
        self.frames["list_container"] = customtkinter.CTkFrame(
            self.frames["script_list"]
        )

        # Scrollable list frame
        self.frames["scrollable_frame"] = customtkinter.CTkScrollableFrame(
            self.frames["list_container"], width=250, height=350
        )

        # Add new script button
        self.buttons["new_script"] = customtkinter.CTkButton(
            self.frames["script_list"], text="New automation", command=self.new_script
        )

        # Delete script button
        self.buttons["delete_script"] = customtkinter.CTkButton(
            self.frames["script_list"],
            text="Delete automation",
            fg_color="#dc3545",
            hover_color="#c82333",
            command=self.delete_script,
        )

        # ===== Script Editor Section =====
        self.labels["editor_title"] = customtkinter.CTkLabel(
            self.frames["editor"],
            text="Action sequence",
            font=customtkinter.CTkFont(size=16, weight="bold"),
        )

        # Script name entry
        self.frames["name_frame"] = customtkinter.CTkFrame(self.frames["editor"])

        self.labels["script_name"] = customtkinter.CTkLabel(
            self.frames["name_frame"], text="Name:", width=100
        )

        self.entries["script_name"] = customtkinter.CTkEntry(
            self.frames["name_frame"], width=300, placeholder_text="e.g. Start show"
        )

        # Text editor for the constrained, line-oriented action DSL.
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
            background="#343638",
            foreground="#aaaaaa",
            font=("Courier New", 12),
        )

        # Action editor
        self.textboxes["code_editor"] = customtkinter.CTkTextbox(
            self.frames["text_frame"],
            width=600,
            height=400,
            font=("Courier New", 12),
            activate_scrollbars=True,
        )

        # Insert default script template
        self.textboxes["code_editor"].insert("1.0", self.get_script_template())

        # Description of available functions
        self.textboxes["help_text"] = customtkinter.CTkTextbox(
            self.frames["editor"], width=600, height=100, font=("Courier New", 10)
        )

        # Insert help text
        self.textboxes["help_text"].insert("1.0", self.get_help_text())
        self.textboxes["help_text"].configure(state="disabled")

        # Buttons for editor actions
        self.frames["editor_buttons"] = customtkinter.CTkFrame(self.frames["editor"])

        self.buttons["save_script"] = customtkinter.CTkButton(
            self.frames["editor_buttons"],
            text="Save automation",
            command=self.save_script,
        )

        self.buttons["test_script"] = customtkinter.CTkButton(
            self.frames["editor_buttons"], text="Run test", command=self.test_script
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
        self.frames["script_list"].grid(
            row=0, column=0, padx=10, pady=10, sticky="nsew"
        )
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
        self.entries["script_name"].pack(
            side="left", fill="x", expand=True, padx=5, pady=5
        )

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
        if not hasattr(self.app, "script_manager") or not self.app.script_manager:
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
                pady=10,
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
                command=lambda name=script_name: self.load_script(name),
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
        script_code = self.app.script_manager.get_script_code(script_name) or ""

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

        # Keep names human-readable while preventing ambiguous/control values.
        if not script_name:
            self.show_status("Enter an automation name.", "#e05d5d")
            return
        if len(script_name) > 64 or not re.fullmatch(r"[\w .-]+", script_name):
            self.show_status(
                "Use at most 64 letters, numbers, spaces, dots, dashes or underscores.",
                "#e05d5d",
            )
            return

        # Get script code
        script_code = self.textboxes["code_editor"].get("1.0", "end-1c")

        # Validate script code
        if not script_code.strip():
            self.show_status("Add at least one action before saving.", "#e05d5d")
            return

        # Check if this is a rename
        is_rename = (
            self.current_script is not None and script_name != self.current_script
        )

        # If renaming, check for existing script
        if is_rename and script_name in self.app.script_manager.scripts:
            # Show confirmation dialog
            title = "Overwrite Script"
            message = f"Script '{script_name}' already exists. Overwrite?"
            self.show_confirmation_dialog(
                title,
                message,
                lambda: self._save_script(script_name, script_code, is_rename),
            )
            return

        self._save_script(script_name, script_code, is_rename)

    def _save_script(self, script_name, script_code, is_rename=False):
        """
        Internal method to save a script without confirmation.

        Args:
            script_name (str): Name of the script
            script_code (str): Line-oriented action DSL
            is_rename (bool): Whether this is a rename operation
        """
        try:
            saved = self.app.script_manager.save_script(script_name, script_code)
        except (TypeError, ValueError) as exc:
            self.show_status(f"Invalid automation: {exc}", "#e05d5d")
            return
        except Exception as exc:
            self.show_status(f"Could not save automation: {exc}", "#e05d5d")
            return
        if saved is False:
            self.show_status(
                "Could not save the automation. Check the application log.", "#e05d5d"
            )
            return

        # If renamed, delete old script
        mapping_saved = True
        if is_rename:
            previous_name = self.current_script
            deleted = self.app.script_manager.delete_script(previous_name)
            if deleted is not False:
                mapping_saved = self._replace_script_mappings(
                    previous_name, script_name
                )

        # Update current script
        self.current_script = script_name

        # Reset unsaved changes flag
        self.unsaved_changes = False

        # Reload script list
        self.load_scripts()

        if not mapping_saved:
            self.show_status(
                "Automation saved, but its button mappings could not be updated.",
                "#e2a93b",
            )
        else:
            self.show_status(f"Saved automation: {script_name}", "#4caf6a")

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
            title, message, lambda: self._delete_script(self.current_script)
        )

    def _delete_script(self, script_name):
        """
        Internal method to delete a script without confirmation.

        Args:
            script_name (str): Name of the script to delete
        """
        try:
            deleted = self.app.script_manager.delete_script(script_name)
        except Exception as exc:
            self.show_status(f"Could not delete automation: {exc}", "#e05d5d")
            return
        if deleted is False:
            self.show_status(f"Automation '{script_name}' no longer exists.", "#e05d5d")
            self.load_scripts()
            return

        mapping_saved = self._replace_script_mappings(script_name, None)

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

        if mapping_saved:
            self.show_status(f"Deleted automation: {script_name}", "#4caf6a")
        else:
            self.show_status(
                "Automation deleted, but its button mappings could not be cleared.",
                "#e2a93b",
            )

    def _replace_script_mappings(self, old_name, new_name):
        """Keep general-button mappings consistent after rename or deletion."""
        mapping = self.app.config.settings.setdefault("mapping", {})
        changed = False
        for control_id, assignment in list(mapping.items()):
            if control_id.startswith("G") and assignment == old_name:
                mapping[control_id] = new_name
                changed = True
        if not changed:
            return True
        try:
            return self.app.config.save_mapping() is not False
        except Exception as exc:
            self.app.logger.error(f"Could not update automation mappings: {exc}")
            return False

    def test_script(self):
        """Test the current script."""
        # Get script code
        script_code = self.textboxes["code_editor"].get("1.0", "end-1c")

        # Validate script code
        if not script_code.strip():
            self.show_status("Add at least one action before testing.", "#e05d5d")
            return

        # Testing intentionally executes the sequence, but never blocks Tk.
        self.buttons["test_script"].configure(state="disabled")
        self.show_status("Running actions now...", "#e2a93b", duration=0)
        self.app.submit_background(
            lambda: self.app.script_manager.test_script(script_code),
            self._test_script_complete,
            self._test_script_error,
            description="automation test",
        )

    def _test_script_complete(self, result):
        self.buttons["test_script"].configure(state="normal")
        if result is False:
            self.show_status("The automation could not be completed.", "#e05d5d")
        else:
            self.show_status("Automation test completed.", "#4caf6a")

    def _test_script_error(self, error):
        self.buttons["test_script"].configure(state="normal")
        if isinstance(error, (TypeError, ValueError)):
            self.show_status(f"Invalid action sequence: {error}", "#e05d5d")
        else:
            self.show_status(f"Automation test failed: {error}", "#e05d5d")

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
            font=customtkinter.CTkFont(size=14),
        )
        label.pack(pady=(20, 20))

        button_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)

        save_button = customtkinter.CTkButton(
            button_frame,
            text="Save",
            command=lambda: self.handle_unsaved_dialog_save(dialog, callback),
        )
        save_button.pack(side="left", padx=10)

        discard_button = customtkinter.CTkButton(
            button_frame,
            text="Discard",
            fg_color="#dc3545",
            hover_color="#c82333",
            command=lambda: self.handle_unsaved_dialog_discard(dialog, callback),
        )
        discard_button.pack(side="right", padx=10)

        cancel_button = customtkinter.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="#6c757d",
            hover_color="#5a6268",
            command=lambda: dialog.destroy(),
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
        self.save_script()

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
            dialog, text=message, font=customtkinter.CTkFont(size=14)
        )
        label.pack(pady=(20, 20))

        button_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)

        ok_button = customtkinter.CTkButton(
            button_frame,
            text="OK",
            command=lambda: self.handle_confirmation_ok(dialog, callback),
        )
        ok_button.pack(side="left", padx=10)

        cancel_button = customtkinter.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="#6c757d",
            hover_color="#5a6268",
            command=lambda: dialog.destroy(),
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
        return """# One action per line. Lines beginning with # are ignored.
# This constrained format is intentionally not Python.
press space
delay 0.25
combo ctrl+shift+m
"""

    def get_help_text(self):
        """
        Get help text for script editor.

        Returns:
            str: Help text
        """
        return (
            "Available actions (one per line):\n"
            "press KEY | hold KEY | release KEY | combo KEY+KEY\n"
            "write TEXT | delay SECONDS | move X,Y | click left|right|middle[,X,Y]\n"
            "Run test executes these keyboard/mouse actions immediately.\n"
            "Example: combo ctrl+shift+m"
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
            self.show_unsaved_changes_dialog(lambda: self.app.show_page(page_name))
            return

        self.app.show_page(page_name)
