#!/usr/bin/env python3
"""StreamDeck Control application entry point."""

import customtkinter

from src.app import run


def main():
    """Main entry point for the application."""
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")

    run()


if __name__ == "__main__":
    main()
