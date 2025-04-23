"""
Base Page for StreamDeck application.
Provides a foundation for all application pages.
"""
import customtkinter
from typing import Dict, Any, Optional, List, Callable

class BasePage(customtkinter.CTkFrame):
    """
    Base page class for the StreamDeck application.
    
    Provides common functionality for all pages including frame structure,
    widget management, and page transitions.
    
    Attributes:
        parent: Parent widget
        frames (Dict): Dictionary of frames
        labels (Dict): Dictionary of labels
        entries (Dict): Dictionary of entry fields
        buttons (Dict): Dictionary of buttons
        canvas (Dict): Dictionary of canvases
        comboboxes (Dict): Dictionary of comboboxes
        scrollable (Dict): Dictionary of scrollable frames
        switches (Dict): Dictionary of switches
        sliders (Dict): Dictionary of sliders
        progressbars (Dict): Dictionary of progress bars
        tabs (Dict): Dictionary of tab views
        potentiometers (Dict): Dictionary of potentiometer widgets
    """
    def __init__(self, parent, **kwargs):
        """
        Initialize the base page.
        
        Args:
            parent: Parent widget
            **kwargs: Additional arguments for the frame
        """
        super().__init__(parent, **kwargs)
        self.parent = parent
        
        # Widget collections
        self.frames = {}
        self.labels = {}
        self.entries = {}
        self.buttons = {}
        self.canvas = {}
        self.comboboxes = {}
        self.scrollable = {}
        self.switches = {}
        self.sliders = {}
        self.progressbars = {}
        self.tabs = {}
        self.potentiometers = {}
        
        # Status message
        self.status_message = None
        self.status_timer = None
        
        # Page callbacks
        self.on_show_callbacks = []
        self.on_hide_callbacks = []
        
    def change_window_name(self):
        """Change window title for this page."""
        self.parent.title("StreamDeck - BasePage")

    def show(self):
        """Show the page and execute on_show callbacks."""
        # Show the page
        self.grid(row=0, column=0, sticky="nsew")
        self.change_window_name()
        
        # Execute on_show callbacks
        for callback in self.on_show_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in on_show callback: {e}")

    def hide(self):
        """Hide the page and execute on_hide callbacks."""
        # Execute on_hide callbacks
        for callback in self.on_hide_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in on_hide callback: {e}")
                
        # Hide the page
        self.grid_forget()

    def create_page(self):
        """Create the page structure and widgets."""
        self.create_frames()
        self.configure_frames()
        self.create_widgets()
        self.configure_widgets()
        self.grid_widgets()
        self.grid_frames()

    def create_frames(self):
        """Create frames for the page."""
        # Common layout with title, body, and bottom sections
        self.frames["title"] = customtkinter.CTkFrame(self, fg_color="gray25")
        self.frames["body"] = customtkinter.CTkFrame(self, corner_radius=0)
        self.frames["bottom"] = customtkinter.CTkFrame(self, fg_color="gray20", corner_radius=0)

    def configure_frames(self):
        """Configure frame layout."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=4)
        self.grid_rowconfigure(1, weight=10)
        self.grid_rowconfigure(2, weight=1)

    def grid_frames(self):
        """Position frames in the page."""
        self.frames["title"].grid(row=0, column=0, sticky="nswe", padx=20, pady=(20, 5))
        self.frames["body"].grid(row=1, column=0, sticky="nswe", padx=20, pady=(5, 0))
        self.frames["bottom"].grid(row=2, column=0, sticky="nswe", padx=20, pady=(0, 20))

    def create_widgets(self):
        """Create widgets for the page."""
        # To be implemented by subclasses
        pass

    def configure_widgets(self):
        """Configure widgets for the page."""
        # To be implemented by subclasses
        pass

    def grid_widgets(self):
        """Position widgets in the page."""
        # To be implemented by subclasses
        pass
    
    def add_title(self, text: str, font_size: int = 25):
        """
        Add a title to the title frame.
        
        Args:
            text (str): Title text
            font_size (int): Font size
        """
        self.labels["page_title"] = customtkinter.CTkLabel(
            self.frames["title"], 
            text=text, 
            font=customtkinter.CTkFont(size=font_size, weight="bold")
        )
        self.labels["page_title"].pack(pady=10)
    
    def add_status(self):
        """Add a status message label to the bottom frame."""
        self.labels["status"] = customtkinter.CTkLabel(
            self.frames["bottom"], 
            text="", 
            font=customtkinter.CTkFont(size=12)
        )
        self.labels["status"].pack(pady=10)
    
    def show_status(self, message: str, color: str = None, duration: int = 5000):
        """
        Show a status message.
        
        Args:
            message (str): Status message
            color (str, optional): Text color
            duration (int, optional): Duration in milliseconds
        """
        if "status" not in self.labels:
            self.add_status()
            
        # Cancel existing timer
        if self.status_timer:
            self.after_cancel(self.status_timer)
            self.status_timer = None
            
        # Update message
        self.labels["status"].configure(text=message)
        
        # Update color if provided
        if color:
            self.labels["status"].configure(text_color=color)
            
        # Set timer to clear message
        if duration > 0:
            self.status_timer = self.after(duration, self.clear_status)
    
    def clear_status(self):
        """Clear the status message."""
        if "status" in self.labels:
            self.labels["status"].configure(text="")
            self.status_timer = None
    
    def add_on_show_callback(self, callback: Callable):
        """
        Add a callback to be executed when the page is shown.
        
        Args:
            callback (Callable): Callback function
        """
        if callback not in self.on_show_callbacks:
            self.on_show_callbacks.append(callback)
    
    def remove_on_show_callback(self, callback: Callable):
        """
        Remove a callback from the on_show callbacks.
        
        Args:
            callback (Callable): Callback function to remove
        """
        if callback in self.on_show_callbacks:
            self.on_show_callbacks.remove(callback)
    
    def add_on_hide_callback(self, callback: Callable):
        """
        Add a callback to be executed when the page is hidden.
        
        Args:
            callback (Callable): Callback function
        """
        if callback not in self.on_hide_callbacks:
            self.on_hide_callbacks.append(callback)
    
    def remove_on_hide_callback(self, callback: Callable):
        """
        Remove a callback from the on_hide callbacks.
        
        Args:
            callback (Callable): Callback function to remove
        """
        if callback in self.on_hide_callbacks:
            self.on_hide_callbacks.remove(callback)
    
    def create_scrollable_frame(self, parent_frame: customtkinter.CTkFrame, name: str) -> customtkinter.CTkScrollableFrame:
        """
        Create a scrollable frame.
        
        Args:
            parent_frame (customtkinter.CTkFrame): Parent frame
            name (str): Name for the scrollable frame
            
        Returns:
            customtkinter.CTkScrollableFrame: The created scrollable frame
        """
        self.scrollable[name] = customtkinter.CTkScrollableFrame(parent_frame)
        return self.scrollable[name]
    
    def create_tab_view(self, parent_frame: customtkinter.CTkFrame, name: str) -> customtkinter.CTkTabview:
        """
        Create a tab view.
        
        Args:
            parent_frame (customtkinter.CTkFrame): Parent frame
            name (str): Name for the tab view
            
        Returns:
            customtkinter.CTkTabview: The created tab view
        """
        self.tabs[name] = customtkinter.CTkTabview(parent_frame)
        return self.tabs[name]
    
    def add_navigation_buttons(self, pages: List[str], callback: Callable[[str], None]):
        """
        Add navigation buttons to the bottom frame.
        
        Args:
            pages (List[str]): List of page names
            callback (Callable): Callback function for navigation
        """
        nav_frame = customtkinter.CTkFrame(self.frames["bottom"], fg_color="transparent")
        nav_frame.pack(fill="x", pady=5)
        
        # Add a button for each page
        for i, page in enumerate(pages):
            button = customtkinter.CTkButton(
                nav_frame, 
                text=page, 
                command=lambda p=page: callback(p),
                width=120,
                height=30
            )
            button.grid(row=0, column=i, padx=10, pady=5)
            
        # Add to buttons dictionary
        self.buttons["navigation"] = nav_frame 