"""Single source of truth for product identity and version information."""

from datetime import date


APP_NAME = "StreamDeck Control"
APP_VERSION = "3.0.0"
APP_DESCRIPTION = (
    "A configurable hardware control surface for OBS Studio and desktop automations."
)
COPYRIGHT = f"Copyright {date.today().year} StreamDeck Control contributors"

__version__ = APP_VERSION
