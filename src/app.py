"""Main application window and application-service coordination."""

from __future__ import annotations

from queue import Empty, Queue
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Dict, Optional

import customtkinter

from .hardware.serial_controller import SerialController
from .obs.obs_controller import OBSController
from .scripts.scripting import ScriptManager
from .ui.pages.connection_page import ConnectionPage
from .ui.pages.mapping_page import MappingPage
from .ui.pages.online_page import OnlinePage
from .ui.pages.script_page import ScriptPage
from .ui.pages.settings_page import SettingsPage
from .utils.config_manager import ConfigManager
from .utils.logger import Logger
from .version import APP_NAME, APP_VERSION


customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")


UiCallback = Callable[[Any], None]
UiQueueItem = tuple[str, Optional[UiCallback], Any, str]


class StreamDeckApp(customtkinter.CTk):
    """Coordinate configuration, controllers and the Tk user interface.

    UI callbacks are never invoked by worker threads. Background work publishes
    a result to ``_ui_queue`` and the Tk main loop drains that queue periodically.
    This is the only supported async bridge for pages.
    """

    UI_QUEUE_INTERVAL_MS = 40

    def __init__(self) -> None:
        super().__init__()

        # These services are initialized synchronously by ``_initialize`` before
        # the event loop can dispatch any callback.
        self.logger: Logger
        self.config: ConfigManager
        self.script_manager: ScriptManager
        self.obs: OBSController
        self.serial: SerialController

        self.pages: Dict[str, Any] = {}
        self.current_page: Optional[str] = None
        self.previous_page: Optional[str] = None

        self._closing = False
        self._ui_queue: Queue[UiQueueItem] = Queue()
        self._ui_queue_timer: Optional[str] = None
        self._executor = ThreadPoolExecutor(
            max_workers=4,
            thread_name_prefix="streamdeck-worker",
        )
        self._pot_lock = threading.Lock()
        self._pending_pot_values: Dict[str, int] = {}
        self._active_pot_workers: set[str] = set()

        self._initialize()

    def _initialize(self) -> None:
        """Initialize services, controllers and pages in dependency order."""
        self.config = ConfigManager()
        self._initialize_logger()
        self._initialize_data_services()
        self._initialize_graphics()
        self._initialize_controllers()
        self._add_pages()

        self.protocol("WM_DELETE_WINDOW", self.exit)
        self._schedule_ui_queue()
        self.show_page("connection")
        self.after(250, self._auto_connect_if_enabled)

    def _initialize_logger(self) -> None:
        logs = self.config.settings.get("logs", {})
        selected_level = str(logs.get("level", "info")).lower()
        self.logger = Logger(
            level=selected_level,
            file_enabled=bool(logs.get("file_enabled", True)),
            console=bool(logs.get("console_enabled", True)),
            max_files=max(1, int(logs.get("max_files", 5))),
        )
        self.logger.info(f"{APP_NAME} {APP_VERSION} starting")

    def _initialize_data_services(self) -> None:
        self.script_manager = ScriptManager(
            scripts_path=str(self.config.scripts_path),
            logger=self.logger,
        )

    def _initialize_graphics(self) -> None:
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("960x720")
        self.minsize(820, 620)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        ui_settings = self.config.settings.get("ui", {})
        customtkinter.set_appearance_mode(ui_settings.get("theme", "dark"))
        self.apply_font_scale(ui_settings.get("font_size", "medium"))

    def _initialize_controllers(self) -> None:
        obs_data = self.config.settings["connection"]["obs_data"]
        self.obs = OBSController(
            host=obs_data["host"],
            port=int(obs_data["port"]),
            password=obs_data["password"],
            logger=self.logger,
        )

        serial_data = self.config.settings["connection"]["serial_data"]
        self.serial = SerialController(
            port=serial_data["com_port"],
            baud_rate=int(serial_data["baud_rate"]),
            logger=self.logger,
        )
        self._register_controller_callbacks()

    def _register_controller_callbacks(self) -> None:
        self.serial.register_callback(
            "record_start",
            lambda: self._submit_controller_action(
                self.obs.start_recording, "hardware start recording"
            ),
        )
        self.serial.register_callback(
            "record_stop",
            lambda: self._submit_controller_action(
                self.obs.stop_recording, "hardware stop recording"
            ),
        )
        self.serial.register_callback(
            "stream_start",
            lambda: self._submit_controller_action(
                self.obs.start_streaming, "hardware start streaming"
            ),
        )
        self.serial.register_callback(
            "stream_stop",
            lambda: self._submit_controller_action(
                self.obs.stop_streaming, "hardware stop streaming"
            ),
        )
        self.serial.register_callback("scene_change", self._handle_scene_change)
        self.serial.register_callback("volume_change", self._handle_volume_change)
        self.serial.register_callback("execute_script", self._handle_script_execution)

        self.obs.register_callback(
            "streaming_state", lambda state: self.serial.set_led(0, state)
        )
        self.obs.register_callback(
            "recording_state", lambda state: self.serial.set_led(1, state)
        )

    def _add_pages(self) -> None:
        self.pages = {
            "connection": ConnectionPage(self),
            "online": OnlinePage(self),
            "mapping": MappingPage(self),
            "script": ScriptPage(self),
            "settings": SettingsPage(self),
        }
        for page in self.pages.values():
            page.create_page()

    def show_page(self, page_name: str, *, remember: bool = True) -> None:
        """Show a page and retain the last distinct page for Back navigation."""
        if page_name not in self.pages:
            self.logger.error(f"Page '{page_name}' not found")
            return
        if page_name == self.current_page:
            return

        old_page = self.current_page
        if old_page and old_page in self.pages:
            self.pages[old_page].hide()
        if remember and old_page:
            self.previous_page = old_page

        # Set the state before on_show callbacks run, so asynchronous page code
        # can reliably check whether its result is still relevant.
        self.current_page = page_name
        self.pages[page_name].show()
        self.logger.debug(f"Switched to page: {page_name}")

    def go_back(self, fallback: str = "connection") -> None:
        destination = self.previous_page
        if destination == self.current_page or destination not in self.pages:
            destination = fallback
        self.show_page(destination)

    def submit_background(
        self,
        task: Callable[[], Any],
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[BaseException], None]] = None,
        *,
        description: str = "background task",
    ) -> Optional[Future[Any]]:
        """Run ``task`` off-thread and dispatch its callbacks on the Tk thread."""
        if self._closing:
            return None

        def run() -> None:
            try:
                result = task()
            except BaseException as exc:  # Preserve the exception for UI/logging.
                self._ui_queue.put(("error", on_error, exc, description))
            else:
                self._ui_queue.put(("success", on_success, result, description))

        try:
            return self._executor.submit(run)
        except RuntimeError as exc:
            if not self._closing:
                self.logger.error(f"Could not schedule {description}: {exc}")
            return None

    def dispatch_to_ui(self, callback: Callable[[], None]) -> None:
        """Queue a callback for the Tk thread (safe for controller callbacks)."""
        if not self._closing:
            self._ui_queue.put(
                ("success", lambda _result: callback(), None, "UI callback")
            )

    def _schedule_ui_queue(self) -> None:
        if not self._closing:
            self._ui_queue_timer = self.after(
                self.UI_QUEUE_INTERVAL_MS,
                self._drain_ui_queue,
            )

    def _drain_ui_queue(self) -> None:
        self._ui_queue_timer = None
        if self._closing:
            return

        while True:
            try:
                kind, callback, payload, description = self._ui_queue.get_nowait()
            except Empty:
                break

            if kind == "error":
                self.logger.error(f"{description} failed: {payload}")
            if callback is not None:
                try:
                    callback(payload)
                except Exception as exc:
                    self.logger.error(f"UI callback for {description} failed: {exc}")

        self._schedule_ui_queue()

    def _auto_connect_if_enabled(self) -> None:
        if self._closing:
            return
        enabled = bool(
            self.config.settings.get("connection", {}).get("auto_connect", False)
        )
        if enabled:
            self.logger.info("Auto-connect enabled; starting configured connections")
            self.pages["connection"].start_auto_connect()

    def _handle_scene_change(self, button_id: str) -> None:
        scene_name = self.config.settings.get("mapping", {}).get(button_id)
        if scene_name:
            self._submit_controller_action(
                lambda: self.obs.set_current_scene(scene_name),
                f"hardware scene {scene_name}",
            )

    def _handle_volume_change(self, pot_id: str, pot_value: int) -> None:
        # Serial input can arrive much faster than OBS round trips. Retain only
        # the newest value and allow at most one worker per potentiometer.
        with self._pot_lock:
            self._pending_pot_values[pot_id] = pot_value
            if pot_id in self._active_pot_workers:
                return
            self._active_pot_workers.add(pot_id)
        self.submit_background(
            lambda: self._drain_pot_values(pot_id),
            description=f"hardware volume {pot_id}",
        )

    def _drain_pot_values(self, pot_id: str) -> None:
        while not self._closing:
            with self._pot_lock:
                if pot_id not in self._pending_pot_values:
                    # Removal is atomic with the empty check: a concurrent serial
                    # callback will either be consumed here or schedule a new worker.
                    self._active_pot_workers.discard(pot_id)
                    return
                pot_value = self._pending_pot_values.pop(pot_id)
            source_name = self.config.settings.get("mapping", {}).get(pot_id)
            if source_name:
                try:
                    _, db_value = self.obs.pot_to_db(pot_value)
                    self.obs.set_volume(source_name, db_value)
                except Exception as exc:
                    self.logger.error(
                        f"Hardware volume update failed for {pot_id}: {exc}"
                    )

        with self._pot_lock:
            self._pending_pot_values.pop(pot_id, None)
            self._active_pot_workers.discard(pot_id)

    def _submit_controller_action(
        self, action: Callable[[], Any], description: str
    ) -> None:
        """Keep serial reader callbacks free of blocking OBS/automation work."""
        self.submit_background(action, description=description)

    def _handle_script_execution(self, button_id: str) -> None:
        script_name = self.config.settings.get("mapping", {}).get(button_id)
        if script_name:
            self._submit_controller_action(
                lambda: self.script_manager.execute_script(
                    script_name, async_execution=True
                ),
                f"hardware automation {script_name}",
            )

    def apply_font_scale(self, selection: str) -> None:
        """Apply the configured accessibility scale to all CTk widgets."""
        scaling = {"small": 0.9, "medium": 1.0, "large": 1.15}.get(selection, 1.0)
        customtkinter.set_widget_scaling(scaling)

    def apply_logging_settings(self) -> None:
        """Apply logging level and output settings without replacing references."""
        settings = self.config.settings.get("logs", {})
        self.logger.reconfigure(
            level=str(settings.get("level", "info")),
            file_enabled=bool(settings.get("file_enabled", True)),
            console_enabled=bool(settings.get("console_enabled", True)),
            max_files=max(1, int(settings.get("max_files", 5))),
        )

    def save_all_settings(self) -> None:
        """Persist application settings and hardware mappings."""
        settings_saved = self.config.save_settings()
        mapping_saved = self.config.save_mapping()
        if settings_saved is False or mapping_saved is False:
            raise OSError("one or more configuration files could not be saved")
        self.logger.info("Application settings saved")

    def exit(self) -> None:
        """Stop services, persist state and destroy the Tk interpreter once."""
        if self._closing:
            return
        self._closing = True

        if self._ui_queue_timer:
            try:
                self.after_cancel(self._ui_queue_timer)
            except Exception:
                pass
            self._ui_queue_timer = None

        for name, controller in (("serial", self.serial), ("OBS", self.obs)):
            try:
                controller.disconnect()
            except Exception as exc:
                self.logger.error(f"Error disconnecting {name}: {exc}")

        try:
            self.script_manager.cancel_all_scripts(timeout=0.5)
        except Exception as exc:
            self.logger.error(f"Error stopping automations: {exc}")

        try:
            self.save_all_settings()
        except Exception as exc:
            self.logger.error(f"Could not save settings during shutdown: {exc}")

        self._executor.shutdown(wait=False, cancel_futures=True)
        self.logger.info(f"{APP_NAME} shutting down")
        self.logger.shutdown()
        self.destroy()


def run() -> None:
    """Launch the desktop application (console-script entry point)."""
    app = StreamDeckApp()
    app.protocol("WM_DELETE_WINDOW", app.exit)
    app.mainloop()


# This module is intentionally launched through main.py.
