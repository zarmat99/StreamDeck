"""
Mapping Page for StreamDeck application.
Provides interface for mapping buttons and potentiometers to functions.
"""
import customtkinter
from typing import Dict, Any, Optional, List

from ui.base_page import BasePage

class MappingPage(BasePage):
    """
    Mapping page for configuring StreamDeck button and potentiometer mappings.
    
    Allows the user to assign scenes, audio sources, and scripts to hardware buttons
    and potentiometers.
    """
    def __init__(self, parent):
        """
        Initialize the mapping page.
        
        Args:
            parent: Parent application
        """
        super().__init__(parent)
        self.app = parent
        
        # Button types and their descriptions
        self.button_types = {
            "B": "Button (Scene)",
            "P": "Potentiometer (Volume)",
            "G": "General (Script)"
        }
        
        # Current button being configured
        self.current_button = None
        
        # Add callbacks for page show/hide
        self.add_on_show_callback(self.on_show)
    
    def change_window_name(self):
        """Change window title for this page."""
        self.parent.title("StreamDeck - Button Mapping")
    
    def create_widgets(self):
        """Create widgets for the mapping page."""
        # Title frame
        self.add_title("StreamDeck Button Mapping")
        
        # Add main sections
        self.frames["layout"] = customtkinter.CTkFrame(self.frames["body"])
        self.frames["config"] = customtkinter.CTkFrame(self.frames["body"])
        
        # ===== Layout Section =====
        self.labels["layout_title"] = customtkinter.CTkLabel(
            self.frames["layout"],
            text="StreamDeck Layout",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        
        # Create StreamDeck layout
        self.frames["deck_layout"] = customtkinter.CTkFrame(self.frames["layout"])
        
        # Button grid (4 rows x 3 columns)
        for i in range(4):
            for j in range(3):
                if i == 0:
                    # Buttons (B0-B3)
                    button_id = f"B{j}"
                    self.create_mapping_button(button_id, i, j)
                elif i == 1:
                    # Potentiometers (P0-P3)
                    button_id = f"P{j}"
                    self.create_mapping_button(button_id, i, j)
                elif i == 2:
                    # General buttons (G0-G3)
                    button_id = f"G{j}"
                    self.create_mapping_button(button_id, i, j)
                elif i == 3 and j == 1:
                    # StreamDeck label
                    self.labels["deck_label"] = customtkinter.CTkLabel(
                        self.frames["deck_layout"],
                        text="StreamDeck",
                        font=customtkinter.CTkFont(size=12, weight="bold")
                    )
                    self.labels["deck_label"].grid(row=i, column=j, padx=5, pady=5)
        
        # ===== Configuration Section =====
        self.labels["config_title"] = customtkinter.CTkLabel(
            self.frames["config"],
            text="Button Configuration",
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        
        # Button type indicator
        self.labels["button_type"] = customtkinter.CTkLabel(
            self.frames["config"],
            text="Select a button to configure",
            font=customtkinter.CTkFont(size=14)
        )
        
        # Current assignment
        self.labels["current_assignment"] = customtkinter.CTkLabel(
            self.frames["config"],
            text="Current Assignment: None",
            font=customtkinter.CTkFont(size=12)
        )
        
        # Tabs for different button types
        self.tabs["config"] = customtkinter.CTkTabview(self.frames["config"])
        self.tabs["config"].add("Scene")
        self.tabs["config"].add("Volume")
        self.tabs["config"].add("Script")
        
        # Scene Tab
        scene_tab = self.tabs["config"].tab("Scene")
        
        self.labels["scene_desc"] = customtkinter.CTkLabel(
            scene_tab,
            text="Assign an OBS scene to a button",
            font=customtkinter.CTkFont(size=12)
        )
        
        self.comboboxes["scene_select"] = customtkinter.CTkComboBox(
            scene_tab,
            values=["Loading scenes..."]
        )
        
        self.buttons["assign_scene"] = customtkinter.CTkButton(
            scene_tab,
            text="Assign Scene",
            command=self.assign_scene
        )
        
        # Volume Tab
        volume_tab = self.tabs["config"].tab("Volume")
        
        self.labels["volume_desc"] = customtkinter.CTkLabel(
            volume_tab,
            text="Assign an audio source to a potentiometer",
            font=customtkinter.CTkFont(size=12)
        )
        
        self.comboboxes["source_select"] = customtkinter.CTkComboBox(
            volume_tab,
            values=["Loading sources..."]
        )
        
        self.buttons["assign_source"] = customtkinter.CTkButton(
            volume_tab,
            text="Assign Source",
            command=self.assign_source
        )
        
        # Script Tab
        script_tab = self.tabs["config"].tab("Script")
        
        self.labels["script_desc"] = customtkinter.CTkLabel(
            script_tab,
            text="Assign a script to a button",
            font=customtkinter.CTkFont(size=12)
        )
        
        self.comboboxes["script_select"] = customtkinter.CTkComboBox(
            script_tab,
            values=["Loading scripts..."]
        )
        
        self.buttons["assign_script"] = customtkinter.CTkButton(
            script_tab,
            text="Assign Script",
            command=self.assign_script
        )
        
        # Clear button (for all types)
        self.buttons["clear_assignment"] = customtkinter.CTkButton(
            self.frames["config"],
            text="Clear Assignment",
            fg_color="#dc3545",
            hover_color="#c82333",
            command=self.clear_assignment
        )
        
        # Save button
        self.buttons["save_mappings"] = customtkinter.CTkButton(
            self.frames["bottom"],
            text="Save Mappings",
            command=self.save_mappings
        )
        
        # Navigation buttons
        nav_buttons = ["connection", "online", "script", "settings"]
        self.add_navigation_buttons(nav_buttons, self.navigate_to_page)
        
        # Status message
        self.add_status()
    
    def configure_widgets(self):
        """Configure widget layout and behavior."""
        # Configure main frames
        self.frames["layout"].configure(corner_radius=10)
        self.frames["config"].configure(corner_radius=10)
        
        # Configure deck layout
        self.frames["deck_layout"].configure(fg_color="gray20", corner_radius=5)
    
    def grid_widgets(self):
        """Position widgets in the page."""
        # Configure body layout
        self.frames["body"].grid_columnconfigure(0, weight=1)
        self.frames["body"].grid_columnconfigure(1, weight=1)
        self.frames["body"].grid_rowconfigure(0, weight=1)
        
        # Position section frames
        self.frames["layout"].grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.frames["config"].grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # ===== Layout Section =====
        self.labels["layout_title"].pack(pady=(10, 15))
        self.frames["deck_layout"].pack(padx=20, pady=10, expand=True)
        
        # ===== Configuration Section =====
        self.labels["config_title"].pack(pady=(10, 5))
        self.labels["button_type"].pack(pady=(5, 0))
        self.labels["current_assignment"].pack(pady=(0, 10))
        
        # Configuration tabs
        self.tabs["config"].pack(fill="both", expand=True, padx=20, pady=10)
        
        # Scene Tab
        scene_tab = self.tabs["config"].tab("Scene")
        self.labels["scene_desc"].pack(pady=(10, 5))
        self.comboboxes["scene_select"].pack(fill="x", padx=20, pady=10)
        self.buttons["assign_scene"].pack(pady=10)
        
        # Volume Tab
        volume_tab = self.tabs["config"].tab("Volume")
        self.labels["volume_desc"].pack(pady=(10, 5))
        self.comboboxes["source_select"].pack(fill="x", padx=20, pady=10)
        self.buttons["assign_source"].pack(pady=10)
        
        # Script Tab
        script_tab = self.tabs["config"].tab("Script")
        self.labels["script_desc"].pack(pady=(10, 5))
        self.comboboxes["script_select"].pack(fill="x", padx=20, pady=10)
        self.buttons["assign_script"].pack(pady=10)
        
        # Clear button
        self.buttons["clear_assignment"].pack(pady=10)
        
        # Save button in bottom frame
        self.buttons["save_mappings"].pack(side="right", padx=10)
    
    def create_mapping_button(self, button_id, row, col):
        """
        Create a button for the StreamDeck layout.
        
        Args:
            button_id (str): Button identifier (e.g., "B0", "P1", "G2")
            row (int): Grid row
            col (int): Grid column
        """
        # Get button type and index
        button_type = button_id[0]
        
        # Button color and text based on type
        if button_type == "B":
            fg_color = "#3498db"  # Blue for scene buttons
            text = f"Scene\n{button_id}"
            height = 60
        elif button_type == "P":
            fg_color = "#e67e22"  # Orange for potentiometers
            text = f"Volume\n{button_id}"
            height = 60
        else:  # "G"
            fg_color = "#2ecc71"  # Green for general/script buttons
            text = f"Script\n{button_id}"
            height = 60
        
        # Create button
        self.buttons[button_id] = customtkinter.CTkButton(
            self.frames["deck_layout"],
            text=text,
            fg_color=fg_color,
            hover_color=self.darken_color(fg_color),
            height=height,
            width=80,
            command=lambda bid=button_id: self.button_clicked(bid)
        )
        
        # Add to grid
        self.buttons[button_id].grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # Update button text with current assignment
        self.update_button_text(button_id)
    
    def darken_color(self, hex_color):
        """
        Darken a hex color for hover effect.
        
        Args:
            hex_color (str): Hex color code
            
        Returns:
            str: Darkened hex color
        """
        # Strip # if present
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
            
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Darken (multiply by 0.8)
        r = int(r * 0.8)
        g = int(g * 0.8)
        b = int(b * 0.8)
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def button_clicked(self, button_id):
        """
        Handle button click in the layout.
        
        Args:
            button_id (str): Button identifier
        """
        # Set as current button
        self.current_button = button_id
        
        # Get button type
        button_type = button_id[0]
        
        # Update UI to show button type
        self.labels["button_type"].configure(
            text=f"Configuring: {self.button_types.get(button_type, 'Unknown')} {button_id}"
        )
        
        # Show current assignment
        assignment = self.get_button_assignment(button_id)
        if assignment:
            self.labels["current_assignment"].configure(text=f"Current Assignment: {assignment}")
        else:
            self.labels["current_assignment"].configure(text="Current Assignment: None")
        
        # Switch to appropriate tab
        if button_type == "B":
            self.tabs["config"].set("Scene")
        elif button_type == "P":
            self.tabs["config"].set("Volume")
        else:  # "G"
            self.tabs["config"].set("Script")
    
    def get_button_assignment(self, button_id):
        """
        Get the current assignment for a button.
        
        Args:
            button_id (str): Button identifier
            
        Returns:
            str: Current assignment or None
        """
        if not hasattr(self.app, 'config') or not self.app.config:
            return None
            
        # Check if button is in mapping
        return self.app.config.settings['mapping'].get(button_id)
    
    def update_button_text(self, button_id):
        """
        Update button text to show its assignment.
        
        Args:
            button_id (str): Button identifier
        """
        if button_id not in self.buttons:
            return
            
        # Get current assignment
        assignment = self.get_button_assignment(button_id)
        button_type = button_id[0]
        
        # Base text
        if button_type == "B":
            base_text = "Scene"
        elif button_type == "P":
            base_text = "Volume"
        else:  # "G"
            base_text = "Script"
        
        # Update text
        if assignment:
            # Truncate long assignments
            short_name = assignment
            if len(short_name) > 10:
                short_name = short_name[:8] + "..."
                
            self.buttons[button_id].configure(text=f"{base_text} {button_id}\n{short_name}")
        else:
            self.buttons[button_id].configure(text=f"{base_text}\n{button_id}")
    
    def update_all_buttons(self):
        """Update text for all buttons with current assignments."""
        for button_id in self.buttons:
            # Skip navigation and other buttons
            if len(button_id) == 2 and button_id[0] in ["B", "P", "G"]:
                self.update_button_text(button_id)
    
    def on_show(self):
        """Handle actions when page is shown."""
        # Update button assignments
        self.update_all_buttons()
        
        # Load scenes, sources and scripts
        self.load_scenes()
        self.load_sources()
        self.load_scripts()
    
    def load_scenes(self):
        """Load OBS scenes into scene combobox."""
        if not self.app.obs or not self.app.obs.is_connected():
            self.comboboxes["scene_select"].configure(values=["OBS not connected"])
            return
            
        scenes = self.app.obs.get_scene_list()
        if not scenes:
            self.comboboxes["scene_select"].configure(values=["No scenes available"])
            return
            
        self.comboboxes["scene_select"].configure(values=scenes)
        if scenes:
            self.comboboxes["scene_select"].set(scenes[0])
    
    def load_sources(self):
        """Load OBS audio sources into source combobox."""
        if not self.app.obs or not self.app.obs.is_connected():
            self.comboboxes["source_select"].configure(values=["OBS not connected"])
            return
            
        sources = self.app.obs.get_volume_sources()
        if not sources:
            self.comboboxes["source_select"].configure(values=["No sources available"])
            return
            
        self.comboboxes["source_select"].configure(values=sources)
        if sources:
            self.comboboxes["source_select"].set(sources[0])
    
    def load_scripts(self):
        """Load available scripts into script combobox."""
        scripts = list(self.app.script_manager.scripts.keys())
        
        if not scripts:
            self.comboboxes["script_select"].configure(values=["No scripts available"])
            return
            
        self.comboboxes["script_select"].configure(values=scripts)
        if scripts:
            self.comboboxes["script_select"].set(scripts[0])
    
    def assign_scene(self):
        """Assign selected scene to current button."""
        if not self.current_button or self.current_button[0] != "B":
            self.show_status("Please select a Scene button (B0-B3) first", "orange")
            return
            
        scene = self.comboboxes["scene_select"].get()
        if scene in ["OBS not connected", "No scenes available"]:
            self.show_status("No valid scene selected", "red")
            return
            
        # Update mapping
        self.app.config.settings['mapping'][self.current_button] = scene
        
        # Update button
        self.update_button_text(self.current_button)
        
        # Update current assignment label
        self.labels["current_assignment"].configure(text=f"Current Assignment: {scene}")
        
        self.show_status(f"Assigned scene '{scene}' to button {self.current_button}", "green")
    
    def assign_source(self):
        """Assign selected audio source to current button."""
        if not self.current_button or self.current_button[0] != "P":
            self.show_status("Please select a Volume potentiometer (P0-P3) first", "orange")
            return
            
        source = self.comboboxes["source_select"].get()
        if source in ["OBS not connected", "No sources available"]:
            self.show_status("No valid audio source selected", "red")
            return
            
        # Update mapping
        self.app.config.settings['mapping'][self.current_button] = source
        
        # Update button
        self.update_button_text(self.current_button)
        
        # Update current assignment label
        self.labels["current_assignment"].configure(text=f"Current Assignment: {source}")
        
        self.show_status(f"Assigned source '{source}' to potentiometer {self.current_button}", "green")
    
    def assign_script(self):
        """Assign selected script to current button."""
        if not self.current_button or self.current_button[0] != "G":
            self.show_status("Please select a Script button (G0-G3) first", "orange")
            return
            
        script = self.comboboxes["script_select"].get()
        if script in ["No scripts available"]:
            self.show_status("No valid script selected", "red")
            return
            
        # Update mapping
        self.app.config.settings['mapping'][self.current_button] = script
        
        # Update button
        self.update_button_text(self.current_button)
        
        # Update current assignment label
        self.labels["current_assignment"].configure(text=f"Current Assignment: {script}")
        
        self.show_status(f"Assigned script '{script}' to button {self.current_button}", "green")
    
    def clear_assignment(self):
        """Clear assignment for current button."""
        if not self.current_button:
            self.show_status("Please select a button first", "orange")
            return
            
        # Clear mapping
        if self.current_button in self.app.config.settings['mapping']:
            self.app.config.settings['mapping'][self.current_button] = None
        
        # Update button
        self.update_button_text(self.current_button)
        
        # Update current assignment label
        self.labels["current_assignment"].configure(text="Current Assignment: None")
        
        self.show_status(f"Cleared assignment for {self.current_button}", "green")
    
    def save_mappings(self):
        """Save button mappings to configuration."""
        self.app.config.save_mapping()
        self.show_status("Mappings saved successfully", "green")
    
    def navigate_to_page(self, page_name):
        """
        Navigate to another page.
        
        Args:
            page_name (str): Name of the page to navigate to
        """
        self.app.show_page(page_name) 