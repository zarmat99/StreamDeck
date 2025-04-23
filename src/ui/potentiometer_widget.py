"""
Potentiometer Widget for StreamDeck application.
Provides a visual representation of a potentiometer with customizable appearance.
"""
import math
import customtkinter
from typing import Callable, Optional, Tuple

class PotentiometerWidget(customtkinter.CTkFrame):
    """
    A widget representing a potentiometer with a rotary dial and value display.
    
    Attributes:
        canvas (customtkinter.CTkCanvas): Drawing canvas for the potentiometer
        value (float): Current potentiometer value (0.0 to 1.0)
        angle (float): Current rotation angle
        callback (Callable): Callback function for value changes
    """
    def __init__(
        self, 
        master, 
        size: int = 150,
        initial_value: float = 0.0,
        min_angle: float = 45,
        max_angle: float = 315,
        color_fg: str = "#1f6aa5",
        color_bg: str = "#333333",
        color_line: str = "#ffffff",
        color_handle: str = "#ff5555",
        color_text: str = "#ffffff",
        knob_style: str = "round",
        show_text: bool = True,
        text_format: str = "{:.0f}%",
        callback: Optional[Callable[[float], None]] = None,
        logarithmic: bool = True,
        label: str = None,
        **kwargs
    ):
        """
        Initialize the potentiometer widget.
        
        Args:
            master: Parent widget
            size (int): Widget size in pixels
            initial_value (float): Initial value (0.0 to 1.0)
            min_angle (float): Minimum rotation angle in degrees
            max_angle (float): Maximum rotation angle in degrees
            color_fg (str): Foreground color (filled arc)
            color_bg (str): Background color (unfilled arc)
            color_line (str): Line color
            color_handle (str): Handle color
            color_text (str): Text color
            knob_style (str): Knob style ('round', 'notched', 'line')
            show_text (bool): Whether to show value text
            text_format (str): Format string for value text
            callback (Callable): Callback function for value changes
            logarithmic (bool): Whether to use logarithmic scale
            label (str): Optional label for the potentiometer
            **kwargs: Additional arguments for the frame
        """
        super().__init__(master, **kwargs)
        
        # Store parameters
        self.size = size
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.color_fg = color_fg
        self.color_bg = color_bg
        self.color_line = color_line
        self.color_handle = color_handle
        self.color_text = color_text
        self.knob_style = knob_style
        self.show_text = show_text
        self.text_format = text_format
        self.callback = callback
        self.logarithmic = logarithmic
        self.label_text = label
        
        # Internal state
        self._value = 0.0
        self._angle = self.min_angle
        self._dragging = False
        self._mouse_prev_y = 0
        
        # Create drawing canvas
        self.canvas = customtkinter.CTkCanvas(
            self,
            width=self.size,
            height=self.size + (30 if self.label_text else 0),
            bg=self._apply_appearance_mode(self._bg_color),
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Create label if provided
        if self.label_text:
            self.canvas.create_text(
                self.size // 2,
                self.size + 15,
                text=self.label_text,
                fill=self._apply_appearance_mode(self.color_text),
                font=("Helvetica", int(self.size * 0.12)),
                tags=("label",)
            )
        
        # Bind events
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)  # Linux scroll down
        
        # Initial drawing
        self.set_value(initial_value)
    
    def _apply_appearance_mode(self, color):
        """Convert color to current appearance mode (light/dark)."""
        return customtkinter.ThemeManager.theme["color"][color] if color in customtkinter.ThemeManager.theme["color"] else color
    
    def _angle_to_value(self, angle):
        """Convert angle to value (0.0 to 1.0)."""
        angle_range = self.max_angle - self.min_angle
        value = (angle - self.min_angle) / angle_range
        if self.logarithmic:
            # Logarithmic scale for more natural volume control
            # Avoid log(0) by using a small minimum
            MIN_VALUE = 0.01
            return (math.log10(MIN_VALUE + value * (1 - MIN_VALUE)) - math.log10(MIN_VALUE)) / (0 - math.log10(MIN_VALUE))
        return value
    
    def _value_to_angle(self, value):
        """Convert value (0.0 to 1.0) to angle."""
        if self.logarithmic:
            # Inverse of logarithmic scale
            MIN_VALUE = 0.01
            exp_val = math.pow(10, (value * (0 - math.log10(MIN_VALUE)) + math.log10(MIN_VALUE)))
            exp_val = max(0, exp_val - MIN_VALUE) / (1 - MIN_VALUE)
            value = exp_val
        
        angle_range = self.max_angle - self.min_angle
        return self.min_angle + value * angle_range
    
    def _on_mouse_down(self, event):
        """Handle mouse button press event."""
        self._dragging = True
        self._mouse_prev_y = event.y
        self.canvas.focus_set()
    
    def _on_mouse_up(self, event):
        """Handle mouse button release event."""
        self._dragging = False
    
    def _on_mouse_drag(self, event):
        """Handle mouse drag event."""
        if self._dragging:
            # Vertical movement for adjustment (up = increase, down = decrease)
            delta_y = self._mouse_prev_y - event.y
            self._mouse_prev_y = event.y
            
            # Adjust value based on drag amount
            sensitivity = 0.005  # Adjust sensitivity as needed
            new_value = max(0, min(1, self._value + delta_y * sensitivity))
            
            # Update value if changed
            if new_value != self._value:
                self.set_value(new_value)
    
    def _on_mouse_wheel(self, event):
        """Handle mouse wheel event."""
        # Get scroll direction
        if event.num == 4:  # Linux scroll up
            delta = 1
        elif event.num == 5:  # Linux scroll down
            delta = -1
        else:  # Windows wheel
            delta = event.delta / 120
        
        # Adjust value based on wheel direction
        sensitivity = 0.05  # Adjust as needed
        new_value = max(0, min(1, self._value + delta * sensitivity))
        
        # Update value if changed
        if new_value != self._value:
            self.set_value(new_value)
        
        return "break"  # Prevent event propagation
    
    def _draw(self):
        """Draw the potentiometer widget."""
        # Clear canvas
        self.canvas.delete("pot")
        
        # Calculate dimensions
        cx = self.size // 2
        cy = self.size // 2
        radius = int(self.size * 0.4)
        inner_radius = int(radius * 0.7)
        line_width = int(self.size * 0.04)
        
        # Create arc background (full circle)
        start_angle = self.min_angle
        extent_angle = self.max_angle - self.min_angle
        
        # Draw background arc
        self.canvas.create_arc(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            start=start_angle, extent=extent_angle,
            style="arc", width=line_width,
            outline=self._apply_appearance_mode(self.color_bg),
            tags=("pot", "bg_arc")
        )
        
        # Draw foreground arc (filled portion)
        if self._value > 0:
            self.canvas.create_arc(
                cx - radius, cy - radius,
                cx + radius, cy + radius,
                start=start_angle, extent=(self._angle - start_angle),
                style="arc", width=line_width,
                outline=self._apply_appearance_mode(self.color_fg),
                tags=("pot", "fg_arc")
            )
        
        # Draw center circle
        self.canvas.create_oval(
            cx - inner_radius, cy - inner_radius,
            cx + inner_radius, cy + inner_radius,
            fill=self._apply_appearance_mode(self.color_bg),
            outline=self._apply_appearance_mode(self.color_line),
            width=1,
            tags=("pot", "center")
        )
        
        # Draw handle based on style
        rads = math.radians(self._angle)
        endpoint_x = cx + int(inner_radius * math.cos(rads))
        endpoint_y = cy - int(inner_radius * math.sin(rads))
        
        if self.knob_style == "round":
            handle_size = int(self.size * 0.06)
            self.canvas.create_oval(
                endpoint_x - handle_size, endpoint_y - handle_size,
                endpoint_x + handle_size, endpoint_y + handle_size,
                fill=self._apply_appearance_mode(self.color_handle),
                outline=self._apply_appearance_mode(self.color_line),
                width=1,
                tags=("pot", "handle")
            )
        elif self.knob_style == "notched":
            handle_size = int(self.size * 0.08)
            inner_x = cx + int((inner_radius - handle_size) * math.cos(rads))
            inner_y = cy - int((inner_radius - handle_size) * math.sin(rads))
            self.canvas.create_line(
                inner_x, inner_y, endpoint_x, endpoint_y,
                fill=self._apply_appearance_mode(self.color_handle),
                width=line_width,
                tags=("pot", "handle")
            )
        else:  # "line"
            line_length = int(inner_radius * 0.8)
            inner_x = cx + int(0.2 * inner_radius * math.cos(rads))
            inner_y = cy - int(0.2 * inner_radius * math.sin(rads))
            outer_x = cx + int(line_length * math.cos(rads))
            outer_y = cy - int(line_length * math.sin(rads))
            self.canvas.create_line(
                inner_x, inner_y, outer_x, outer_y,
                fill=self._apply_appearance_mode(self.color_handle),
                width=int(line_width * 0.7),
                tags=("pot", "handle")
            )
        
        # Draw value text
        if self.show_text:
            percentage = self._value * 100
            text_value = self.text_format.format(percentage)
            self.canvas.create_text(
                cx, cy,
                text=text_value,
                fill=self._apply_appearance_mode(self.color_text),
                font=("Helvetica", int(self.size * 0.12)),
                tags=("pot", "value_text")
            )
    
    def set_value(self, value):
        """
        Set the potentiometer value.
        
        Args:
            value (float): New value (0.0 to 1.0)
        """
        # Clamp value to valid range
        value = max(0, min(1, value))
        
        # Update value and angle
        self._value = value
        self._angle = self._value_to_angle(value)
        
        # Redraw widget
        self._draw()
        
        # Call callback if provided
        if self.callback:
            self.callback(value)
    
    def get_value(self):
        """
        Get the current potentiometer value.
        
        Returns:
            float: Current value (0.0 to 1.0)
        """
        return self._value
    
    def set_colors(self, foreground=None, background=None, handle=None, text=None):
        """
        Set potentiometer colors.
        
        Args:
            foreground (str, optional): Foreground color
            background (str, optional): Background color
            handle (str, optional): Handle color
            text (str, optional): Text color
        """
        if foreground:
            self.color_fg = foreground
        if background:
            self.color_bg = background
        if handle:
            self.color_handle = handle
        if text:
            self.color_text = text
        
        # Redraw with new colors
        self._draw()
    
    def set_label(self, text):
        """
        Set or update the potentiometer label.
        
        Args:
            text (str): New label text
        """
        self.label_text = text
        self.canvas.delete("label")
        
        if text:
            self.canvas.create_text(
                self.size // 2,
                self.size + 15,
                text=text,
                fill=self._apply_appearance_mode(self.color_text),
                font=("Helvetica", int(self.size * 0.12)),
                tags=("label",)
            )

    def map_to_range(self, min_val: float, max_val: float) -> float:
        """
        Map the current value to a specific range.
        
        Args:
            min_val (float): Minimum range value
            max_val (float): Maximum range value
            
        Returns:
            float: Mapped value
        """
        return min_val + self._value * (max_val - min_val)
    
    def map_to_db(self, min_db: float = -60, max_db: float = 0) -> float:
        """
        Map the current value to a dB scale.
        
        Args:
            min_db (float): Minimum dB value
            max_db (float): Maximum dB value
            
        Returns:
            float: Volume in dB
        """
        # Use logarithmic mapping for more natural volume control
        if self._value == 0:
            return float('-inf')  # Muted
        
        # Logarithmic mapping
        db = min_db + math.log10(0.1 + 0.9 * self._value) / math.log10(1.0) * (max_db - min_db)
        return db 