"""Responsive OBS dashboard and hardware connection monitor."""

from __future__ import annotations

from typing import Any, Dict

import customtkinter

from ..base_page import BasePage
from ..helpers import db_to_percent, percent_to_db


class OnlinePage(BasePage):
    """Monitor OBS using asynchronous snapshots and expose common controls."""

    POLL_INTERVAL_MS = 1000
    VOLUME_DEBOUNCE_MS = 120

    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent
        self.vars = {
            "status": {
                "streaming": customtkinter.BooleanVar(value=False),
                "recording": customtkinter.BooleanVar(value=False),
                "current_scene": customtkinter.StringVar(value="None"),
                "obs_connected": customtkinter.BooleanVar(value=False),
                "serial_connected": customtkinter.BooleanVar(value=False),
            },
            "sources": {"list": []},
            "scenes": {"list": []},
        }

        self.update_timer = None
        self._volume_timer = None
        self._poll_in_flight = False
        self._resources_in_flight = False
        self._last_obs_connected = False
        self._setting_volume_control = False
        self._pending_volume = None
        self._source_request_id = 0

        self.add_on_show_callback(self.on_show)
        self.add_on_hide_callback(self.on_hide)

    def change_window_name(self):
        self.parent.title("StreamDeck Control - Dashboard")

    def create_widgets(self):
        self.add_title("Dashboard")
        body = self.frames["body"]
        for frame_name in ("status", "scenes", "volume", "controls"):
            self.frames[frame_name] = customtkinter.CTkFrame(body)

        self.labels["status_title"] = self._section_title("status", "Connections")
        self.frames["obs_status"] = customtkinter.CTkFrame(
            self.frames["status"], fg_color="transparent"
        )
        self.labels["obs_status"] = customtkinter.CTkLabel(
            self.frames["obs_status"], text="OBS:", width=100, anchor="w"
        )
        self.labels["obs_status_value"] = customtkinter.CTkLabel(
            self.frames["obs_status"], text="Disconnected", text_color="#e05d5d"
        )
        self.frames["serial_status"] = customtkinter.CTkFrame(
            self.frames["status"], fg_color="transparent"
        )
        self.labels["serial_status"] = customtkinter.CTkLabel(
            self.frames["serial_status"], text="Hardware:", width=100, anchor="w"
        )
        self.labels["serial_status_value"] = customtkinter.CTkLabel(
            self.frames["serial_status"], text="Disconnected", text_color="#e05d5d"
        )

        self.labels["scenes_title"] = self._section_title("scenes", "Scene")
        self.labels["current_scene"] = customtkinter.CTkLabel(
            self.frames["scenes"],
            textvariable=self.vars["status"]["current_scene"],
            font=customtkinter.CTkFont(size=14),
        )
        self.comboboxes["scene_select"] = customtkinter.CTkComboBox(
            self.frames["scenes"], values=["OBS not connected"]
        )
        self.buttons["set_scene"] = customtkinter.CTkButton(
            self.frames["scenes"], text="Activate scene", command=self.set_scene
        )

        self.labels["volume_title"] = self._section_title("volume", "Audio")
        self.comboboxes["source_select"] = customtkinter.CTkComboBox(
            self.frames["volume"],
            values=["OBS not connected"],
            command=self.source_selected,
        )
        self.sliders["volume"] = customtkinter.CTkSlider(
            self.frames["volume"],
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.volume_changed,
        )
        self.labels["volume_value"] = customtkinter.CTkLabel(
            self.frames["volume"], text="--"
        )
        self.buttons["mute"] = customtkinter.CTkButton(
            self.frames["volume"],
            text="Mute",
            command=self.toggle_mute,
            state="disabled",
        )

        self.labels["controls_title"] = self._section_title(
            "controls", "Stream and recording"
        )
        self.frames["stream_controls"] = customtkinter.CTkFrame(
            self.frames["controls"], fg_color="transparent"
        )
        self.buttons["start_streaming"] = customtkinter.CTkButton(
            self.frames["stream_controls"],
            text="Start streaming",
            fg_color="#268a49",
            hover_color="#1f713c",
            command=self.start_streaming,
            state="disabled",
        )
        self.buttons["stop_streaming"] = customtkinter.CTkButton(
            self.frames["stream_controls"],
            text="Stop streaming",
            fg_color="#b64040",
            hover_color="#923333",
            command=self.stop_streaming,
            state="disabled",
        )
        self.frames["record_controls"] = customtkinter.CTkFrame(
            self.frames["controls"], fg_color="transparent"
        )
        self.buttons["start_recording"] = customtkinter.CTkButton(
            self.frames["record_controls"],
            text="Start recording",
            fg_color="#268a49",
            hover_color="#1f713c",
            command=self.start_recording,
            state="disabled",
        )
        self.buttons["stop_recording"] = customtkinter.CTkButton(
            self.frames["record_controls"],
            text="Stop recording",
            fg_color="#b64040",
            hover_color="#923333",
            command=self.stop_recording,
            state="disabled",
        )
        self.frames["status_indicators"] = customtkinter.CTkFrame(
            self.frames["controls"], fg_color="transparent"
        )
        self.labels["streaming_status"] = customtkinter.CTkLabel(
            self.frames["status_indicators"], text="Streaming:", width=100, anchor="w"
        )
        self.labels["streaming_value"] = customtkinter.CTkLabel(
            self.frames["status_indicators"], text="Offline", text_color="gray"
        )
        self.labels["recording_status"] = customtkinter.CTkLabel(
            self.frames["status_indicators"], text="Recording:", width=100, anchor="w"
        )
        self.labels["recording_value"] = customtkinter.CTkLabel(
            self.frames["status_indicators"], text="Inactive", text_color="gray"
        )

        self.add_navigation_buttons(
            ["connection", "mapping", "script", "settings"], self.navigate_to_page
        )
        self.add_status()

    def _section_title(self, frame_name, text):
        return customtkinter.CTkLabel(
            self.frames[frame_name],
            text=text,
            font=customtkinter.CTkFont(size=16, weight="bold"),
        )

    def configure_widgets(self):
        for frame_name in ("status", "scenes", "volume", "controls"):
            self.frames[frame_name].configure(corner_radius=10)

    def grid_widgets(self):
        body = self.frames["body"]
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)
        self.frames["status"].grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.frames["scenes"].grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.frames["volume"].grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.frames["controls"].grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.labels["status_title"].pack(pady=(12, 8))
        self.frames["obs_status"].pack(fill="x", padx=20, pady=5)
        self.labels["obs_status"].pack(side="left")
        self.labels["obs_status_value"].pack(side="left")
        self.frames["serial_status"].pack(fill="x", padx=20, pady=5)
        self.labels["serial_status"].pack(side="left")
        self.labels["serial_status_value"].pack(side="left")

        self.labels["scenes_title"].pack(pady=(12, 5))
        self.labels["current_scene"].pack(pady=5)
        self.comboboxes["scene_select"].pack(fill="x", padx=20, pady=5)
        self.buttons["set_scene"].pack(pady=10)

        self.labels["volume_title"].pack(pady=(12, 5))
        self.comboboxes["source_select"].pack(fill="x", padx=20, pady=5)
        slider_frame = customtkinter.CTkFrame(
            self.frames["volume"], fg_color="transparent"
        )
        slider_frame.pack(fill="x", padx=20, pady=8)
        self.sliders["volume"].pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.labels["volume_value"].pack(side="right")
        self.buttons["mute"].pack(pady=8)

        self.labels["controls_title"].pack(pady=(12, 5))
        self.frames["stream_controls"].pack(fill="x", padx=10, pady=4)
        self.buttons["start_streaming"].pack(side="left", fill="x", expand=True, padx=4)
        self.buttons["stop_streaming"].pack(side="right", fill="x", expand=True, padx=4)
        self.frames["record_controls"].pack(fill="x", padx=10, pady=4)
        self.buttons["start_recording"].pack(side="left", fill="x", expand=True, padx=4)
        self.buttons["stop_recording"].pack(side="right", fill="x", expand=True, padx=4)
        self.frames["status_indicators"].pack(fill="x", padx=20, pady=8)
        self.labels["streaming_status"].grid(row=0, column=0, sticky="w", pady=2)
        self.labels["streaming_value"].grid(row=0, column=1, sticky="w", pady=2)
        self.labels["recording_status"].grid(row=1, column=0, sticky="w", pady=2)
        self.labels["recording_value"].grid(row=1, column=1, sticky="w", pady=2)

    def on_show(self):
        self._request_snapshot()
        self._schedule_next_poll()

    def on_hide(self):
        if self.update_timer:
            self.after_cancel(self.update_timer)
            self.update_timer = None
        if self._volume_timer:
            self.after_cancel(self._volume_timer)
            self._volume_timer = None

    def _schedule_next_poll(self):
        if self.update_timer:
            self.after_cancel(self.update_timer)
        if self.app.current_page == "online":
            self.update_timer = self.after(self.POLL_INTERVAL_MS, self.periodic_update)

    def periodic_update(self):
        self.update_timer = None
        self._request_snapshot()
        self._schedule_next_poll()

    def _request_snapshot(self):
        if self._poll_in_flight:
            return
        self._poll_in_flight = True
        self.app.submit_background(
            self._collect_snapshot,
            self._apply_snapshot,
            self._snapshot_error,
            description="OBS dashboard snapshot",
        )

    def _collect_snapshot(self) -> Dict[str, Any]:
        obs_connected = bool(self.app.obs and self.app.obs.is_connected())
        serial_connected = bool(self.app.serial and self.app.serial.is_connected())
        snapshot = {
            "obs_connected": obs_connected,
            "serial_connected": serial_connected,
            "streaming": False,
            "recording": False,
            "scene": None,
        }
        if obs_connected:
            snapshot.update(
                streaming=bool(self.app.obs.get_streaming_status()),
                recording=bool(self.app.obs.get_recording_status()),
                scene=self.app.obs.get_current_scene(),
            )
        return snapshot

    def _snapshot_error(self, error):
        self._poll_in_flight = False
        self.app.logger.error(f"Dashboard refresh failed: {error}")
        if self.app.current_page == "online":
            self._apply_snapshot({"obs_connected": False, "serial_connected": False})

    def _apply_snapshot(self, snapshot):
        self._poll_in_flight = False
        if self.app.current_page != "online":
            return
        obs_connected = bool(snapshot.get("obs_connected"))
        serial_connected = bool(snapshot.get("serial_connected"))
        streaming = bool(snapshot.get("streaming"))
        recording = bool(snapshot.get("recording"))

        self.vars["status"]["obs_connected"].set(obs_connected)
        self.vars["status"]["serial_connected"].set(serial_connected)
        self.vars["status"]["streaming"].set(streaming)
        self.vars["status"]["recording"].set(recording)
        self.labels["obs_status_value"].configure(
            text="Connected" if obs_connected else "Disconnected",
            text_color="#4caf6a" if obs_connected else "#e05d5d",
        )
        self.labels["serial_status_value"].configure(
            text="Connected" if serial_connected else "Disconnected",
            text_color="#4caf6a" if serial_connected else "#e05d5d",
        )
        self.labels["streaming_value"].configure(
            text="Online" if streaming else "Offline",
            text_color="#4caf6a" if streaming else "gray",
        )
        self.labels["recording_value"].configure(
            text="Active" if recording else "Inactive",
            text_color="#4caf6a" if recording else "gray",
        )
        self.vars["status"]["current_scene"].set(snapshot.get("scene") or "None")
        self.buttons["start_streaming"].configure(
            state="normal" if obs_connected and not streaming else "disabled"
        )
        self.buttons["stop_streaming"].configure(
            state="normal" if obs_connected and streaming else "disabled"
        )
        self.buttons["start_recording"].configure(
            state="normal" if obs_connected and not recording else "disabled"
        )
        self.buttons["stop_recording"].configure(
            state="normal" if obs_connected and recording else "disabled"
        )
        self.buttons["set_scene"].configure(
            state="normal" if obs_connected else "disabled"
        )
        if obs_connected and not self._last_obs_connected:
            self.refresh_resources()
        elif not obs_connected:
            self._set_offline_resources()
        self._last_obs_connected = obs_connected

    # Public compatibility name retained for callers/tests.
    def update_status(self):
        self._request_snapshot()

    def refresh_resources(self):
        if self._resources_in_flight:
            return
        if not self.app.obs or not self.app.obs.is_connected():
            self._set_offline_resources()
            return
        self._resources_in_flight = True

        def fetch():
            return {
                "scenes": self.app.obs.get_scene_list() or [],
                "sources": self.app.obs.get_volume_sources() or [],
                "current_scene": self.app.obs.get_current_scene(),
            }

        self.app.submit_background(
            fetch,
            self._apply_resources,
            self._resources_error,
            description="OBS scenes and audio sources",
        )

    def _set_offline_resources(self):
        self.vars["scenes"]["list"] = []
        self.vars["sources"]["list"] = []
        self.comboboxes["scene_select"].configure(values=["OBS not connected"])
        self.comboboxes["scene_select"].set("OBS not connected")
        self.comboboxes["source_select"].configure(values=["OBS not connected"])
        self.comboboxes["source_select"].set("OBS not connected")
        self.buttons["mute"].configure(text="Mute", state="disabled")
        self.labels["volume_value"].configure(text="--")

    def _apply_resources(self, resources):
        self._resources_in_flight = False
        if self.app.current_page != "online":
            return
        scenes = list(resources.get("scenes") or [])
        sources = list(resources.get("sources") or [])
        self.vars["scenes"]["list"] = scenes
        self.vars["sources"]["list"] = sources

        scene_values = scenes or ["No scenes available"]
        source_values = sources or ["No audio sources available"]
        self.comboboxes["scene_select"].configure(values=scene_values)
        self.comboboxes["source_select"].configure(values=source_values)
        current_scene = resources.get("current_scene")
        self.comboboxes["scene_select"].set(
            current_scene if current_scene in scenes else scene_values[0]
        )
        self.comboboxes["source_select"].set(source_values[0])
        if sources:
            self.source_selected(sources[0])
        else:
            self.buttons["mute"].configure(state="disabled")

    def _resources_error(self, error):
        self._resources_in_flight = False
        if self.app.current_page == "online":
            self.show_status(f"Could not load OBS resources: {error}", "#e05d5d")

    def update_scenes_list(self):
        self.refresh_resources()

    def update_sources_list(self):
        self.refresh_resources()

    def source_selected(self, selection):
        if selection not in self.vars["sources"]["list"]:
            self.buttons["mute"].configure(state="disabled")
            return
        self._source_request_id += 1
        request_id = self._source_request_id
        self.buttons["mute"].configure(state="disabled")

        def fetch():
            return self.app.obs.get_volume(selection), self.app.obs.get_mute(selection)

        self.app.submit_background(
            fetch,
            lambda result: self._apply_volume_state(selection, request_id, result),
            lambda error: self._volume_state_error(request_id, error),
            description=f"audio state for {selection}",
        )

    def update_volume_display(self, source_name):
        self.source_selected(source_name)

    def _apply_volume_state(self, source, request_id, result):
        if request_id != self._source_request_id or self.app.current_page != "online":
            return
        if self.comboboxes["source_select"].get() != source:
            return
        volume, muted = result
        if volume is None:
            self.labels["volume_value"].configure(text="--")
            return
        value = db_to_percent(volume)
        self._setting_volume_control = True
        self.sliders["volume"].set(value)
        self._setting_volume_control = False
        self.labels["volume_value"].configure(text=f"{round(value)}%")
        self.buttons["mute"].configure(
            text="Unmute" if bool(muted) else "Mute", state="normal"
        )

    def _volume_state_error(self, request_id, error):
        if request_id == self._source_request_id and self.app.current_page == "online":
            self.buttons["mute"].configure(state="disabled")
            self.show_status(f"Could not read audio state: {error}", "#e05d5d")

    def set_scene(self):
        scene = self.comboboxes["scene_select"].get()
        if scene not in self.vars["scenes"]["list"] or not self.app.obs.is_connected():
            self.show_status("Connect OBS and select a valid scene first.", "#e05d5d")
            return
        self.buttons["set_scene"].configure(state="disabled")
        self.app.submit_background(
            lambda: self.app.obs.set_current_scene(scene),
            lambda success: self._scene_action_complete(scene, success),
            lambda error: self._obs_action_error("change scene", error),
            description=f"activate scene {scene}",
        )

    def scene_selected(self, selection):
        """Scene changes remain explicit through the Activate button."""

    def _scene_action_complete(self, scene, success):
        self.buttons["set_scene"].configure(state="normal")
        if success is False:
            self.show_status("OBS rejected the scene change.", "#e05d5d")
        else:
            self.vars["status"]["current_scene"].set(scene)
            self.show_status(f"Scene changed to {scene}.", "#4caf6a")

    def volume_changed(self, value):
        if self._setting_volume_control:
            return
        self.labels["volume_value"].configure(text=f"{round(float(value))}%")
        source = self.comboboxes["source_select"].get()
        if source not in self.vars["sources"]["list"]:
            return
        self._pending_volume = (source, percent_to_db(value))
        if self._volume_timer:
            self.after_cancel(self._volume_timer)
        self._volume_timer = self.after(self.VOLUME_DEBOUNCE_MS, self._submit_volume)

    def _submit_volume(self):
        self._volume_timer = None
        pending = self._pending_volume
        self._pending_volume = None
        if not pending or not self.app.obs.is_connected():
            return
        source, db_value = pending
        self.app.submit_background(
            lambda: self.app.obs.set_volume(source, db_value),
            on_error=lambda error: self.show_status(
                f"Could not set volume: {error}", "#e05d5d"
            ),
            description=f"set volume for {source}",
        )

    def toggle_mute(self):
        source = self.comboboxes["source_select"].get()
        if (
            source not in self.vars["sources"]["list"]
            or not self.app.obs.is_connected()
        ):
            self.show_status("Connect OBS and select an audio source first.", "#e05d5d")
            return
        self.buttons["mute"].configure(state="disabled")

        def toggle():
            current = self.app.obs.get_mute(source)
            if current is None:
                raise RuntimeError("OBS did not return the mute state")
            target = not bool(current)
            result = self.app.obs.set_mute(source, target)
            return target, result

        self.app.submit_background(
            toggle,
            lambda result: self._mute_complete(source, result),
            lambda error: self._obs_action_error("change mute state", error),
            description=f"toggle mute for {source}",
        )

    def _mute_complete(self, source, result):
        target, success = result
        if success is False:
            self.show_status("OBS rejected the mute change.", "#e05d5d")
        elif self.comboboxes["source_select"].get() == source:
            self.buttons["mute"].configure(
                text="Unmute" if target else "Mute", state="normal"
            )
            self.show_status(f"{source} {'muted' if target else 'unmuted'}.", "#4caf6a")

    def start_streaming(self):
        self._run_transport_action("start_streaming", "Streaming started.")

    def stop_streaming(self):
        self._run_transport_action("stop_streaming", "Streaming stopped.")

    def start_recording(self):
        self._run_transport_action("start_recording", "Recording started.")

    def stop_recording(self):
        self._run_transport_action("stop_recording", "Recording stopped.")

    def _run_transport_action(self, method_name, success_message):
        if not self.app.obs or not self.app.obs.is_connected():
            self.show_status("OBS is not connected.", "#e05d5d")
            return
        for name in (
            "start_streaming",
            "stop_streaming",
            "start_recording",
            "stop_recording",
        ):
            self.buttons[name].configure(state="disabled")
        action = getattr(self.app.obs, method_name)
        self.app.submit_background(
            action,
            lambda success: self._transport_complete(success, success_message),
            lambda error: self._obs_action_error(method_name.replace("_", " "), error),
            description=method_name.replace("_", " "),
        )

    def _transport_complete(self, success, success_message):
        if success is False:
            self.show_status("OBS rejected the requested action.", "#e05d5d")
        else:
            self.show_status(success_message, "#4caf6a")
        self._request_snapshot()

    # Retain old private names for integrations while routing through the safe API.
    def _streaming_action(self, start):
        self._run_transport_action(
            "start_streaming" if start else "stop_streaming",
            "Streaming started." if start else "Streaming stopped.",
        )

    def _recording_action(self, start):
        self._run_transport_action(
            "start_recording" if start else "stop_recording",
            "Recording started." if start else "Recording stopped.",
        )

    def _obs_action_error(self, action, error):
        self.show_status(f"Could not {action}: {error}", "#e05d5d")
        self._request_snapshot()
        source = self.comboboxes["source_select"].get()
        if source in self.vars["sources"]["list"]:
            self.buttons["mute"].configure(state="normal")

    def navigate_to_page(self, page_name):
        self.app.show_page(page_name)
