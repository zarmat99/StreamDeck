"""Application logging with bounded files and runtime reconfiguration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import sys
import threading
from typing import Iterable, Optional


_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def _default_log_dir() -> Path:
    """Return a per-user writable log directory without requiring a dependency."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "StreamDeckControl" / "logs"
    state_home = os.environ.get("XDG_STATE_HOME")
    base = Path(state_home) if state_home else Path.home() / ".local" / "state"
    return base / "streamdeck-control" / "logs"


class _RedactingFilter(logging.Filter):
    """Best-effort redaction for common secret fields in diagnostic logs."""

    _pattern = re.compile(
        r"(?i)(password|passwd|secret|authorization|token)\s*[:=]\s*([^\s,;]+)"
    )

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._pattern.sub(r"\1=<redacted>", record.msg)
        return True


class Logger:
    """Small compatibility wrapper around a named, non-propagating logger.

    The previous implementation configured the root logger at DEBUG level, which
    also captured very verbose third-party WebSocket traffic.  This wrapper owns
    only ``streamdeck_control`` handlers and can be safely reconfigured at runtime.
    """

    def __init__(
        self,
        levels: Optional[Iterable[str]] = None,
        filename: Optional[str] = "streamdeck.log",
        console: bool = False,
        *,
        level: Optional[str] = None,
        file_enabled: Optional[bool] = None,
        max_files: int = 5,
        log_dir: Optional[os.PathLike[str] | str] = None,
    ) -> None:
        requested = [item.lower() for item in (levels or ["info"])]
        invalid = [item for item in requested if item not in _LEVELS]
        if invalid:
            raise ValueError(f"Invalid logging levels: {', '.join(invalid)}")

        # Preserve the old list-based constructor: its lowest enabled level is
        # equivalent to the threshold users expected.
        selected_level = level.lower() if level else min(requested, key=_LEVELS.get)
        self.accepted_levels = list(_LEVELS)
        self.levels = requested
        self.filename = filename or "streamdeck.log"
        self.log_dir = Path(log_dir) if log_dir else _default_log_dir()
        self.logger = logging.getLogger("streamdeck_control")
        self.logger.propagate = False
        self._lock = threading.RLock()
        self._filter = _RedactingFilter()

        self.reconfigure(
            level=selected_level,
            file_enabled=bool(filename) if file_enabled is None else file_enabled,
            console_enabled=console,
            max_files=max_files,
        )

    def reconfigure(
        self,
        *,
        level: str = "info",
        file_enabled: bool = True,
        console_enabled: bool = False,
        max_files: int = 5,
    ) -> None:
        """Replace handlers atomically using the supplied user settings."""
        normalized = level.lower()
        if normalized not in _LEVELS:
            raise ValueError(f"Invalid logging level: {level}")
        if max_files < 1:
            raise ValueError("max_files must be at least 1")

        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(threadName)s %(name)s - %(message)s"
        )
        with self._lock:
            for handler in list(self.logger.handlers):
                self.logger.removeHandler(handler)
                handler.close()

            self.logger.setLevel(_LEVELS[normalized])
            self.levels = [
                name for name, numeric in _LEVELS.items() if numeric >= _LEVELS[normalized]
            ]

            if file_enabled:
                self.log_dir.mkdir(parents=True, exist_ok=True)
                handler = RotatingFileHandler(
                    self.log_dir / self.filename,
                    maxBytes=5 * 1024 * 1024,
                    backupCount=max_files,
                    encoding="utf-8",
                    delay=True,
                )
                handler.setFormatter(formatter)
                handler.addFilter(self._filter)
                self.logger.addHandler(handler)

            if console_enabled:
                handler = logging.StreamHandler()
                handler.setFormatter(formatter)
                handler.addFilter(self._filter)
                self.logger.addHandler(handler)

            # A NullHandler keeps library usage quiet when both outputs are off.
            if not self.logger.handlers:
                self.logger.addHandler(logging.NullHandler())

            # Keep dependencies from flooding the root logger if the embedding
            # application configures it independently.
            logging.getLogger("obswebsocket").setLevel(logging.WARNING)
            logging.getLogger("websocket").setLevel(logging.WARNING)

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def critical(self, message: str) -> None:
        self.logger.critical(message)

    def exception(self, message: str) -> None:
        self.logger.exception(message)

    def shutdown(self) -> None:
        """Flush and close owned handlers during application shutdown."""
        with self._lock:
            for handler in list(self.logger.handlers):
                handler.flush()
                handler.close()
                self.logger.removeHandler(handler)
