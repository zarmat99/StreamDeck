#!/usr/bin/env python3
"""
StreamDeck Control application entry point.

This is the main entry point for the StreamDeck Control application.
It launches the application with the appropriate configuration.
"""
import os
import sys
from src.app import StreamDeckApp
import customtkinter

def main():
    """Main entry point for the application."""
    # Set default appearance mode and color theme
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")
    
    # Create and run the application
    app = StreamDeckApp()
    app.protocol("WM_DELETE_WINDOW", app.exit)  # Handle window close
    app.mainloop()

if __name__ == "__main__":
    main() 