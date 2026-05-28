from __future__ import annotations

from contextlib import contextmanager
import gc
import json
import logging
import os
import platform
import sys
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path
import time
from datetime import datetime
from typing import Callable, Dict, List
import numpy as np
from PIL import Image, ImageDraw, ImageTk
from matplotlib.colors import LinearSegmentedColormap

from sim_rf_map.ui.icons import get_icon_text
from sim_rf_map.ui.shortcuts import SHORTCUTS
from sim_rf_map.ui.lang import STRINGS
from sim_rf_map.ui.split_canvas import SplitOverlayCanvas
from sim_rf_map.ui.theme import apply_dark_mode, apply_light_mode
from sim_rf_map.tooltip import Tooltip
from sim_rf_map.error_handler import catch_errors
from sim_rf_map.env_mode import IS_LITE
from sim_rf_map.utils.meta_writer import write_meta_for

try:
    import psutil
except Exception:  # pragma: no cover - optional dependency
    psutil = None

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource
except Exception:  # pragma: no cover - optional dependency
    plt = None
    LightSource = None

try:
    import rasterio
except Exception:  # pragma: no cover - optional dependency
    rasterio = None

try:
    from sim_rf_map.depth_midas import midas_depth
except Exception:  # pragma: no cover - optional dependency
    midas_depth = None

try:
    from sim_rf_map.depth_physics import physics_depth
except Exception:  # pragma: no cover - optional dependency
    physics_depth = None

try:
    from sim_rf_map.terrain_fusion import fused_dem
except Exception:  # pragma: no cover - optional dependency
    fused_dem = None

try:
    from sim_rf_map.vector_tracing import contours_from_array, save_geojson, save_svg
except Exception:  # pragma: no cover - optional dependency
    contours_from_array = None
    save_geojson = None
    save_svg = None

try:
    from sim_rf_map.voxelizer import voxelize_dem, generate_voxel_volume
    from sim_rf_map import material_inference
    classify_material = material_inference.classify_material
    from sim_rf_map.wavefront_propagator import propagate_wavefront
    from sim_rf_map.weather_model import WeatherConditions
    from sim_rf_map.weather_gui import WeatherGUI
    from sim_rf_map.debug_view import show_loss_slice, export_loss_map
except Exception:  # pragma: no cover - optional dependency
    voxelize_dem = None
    generate_voxel_volume = None
    material_inference = None
    classify_material = None
    propagate_wavefront = None
    WeatherConditions = None
    WeatherGUI = None
    show_loss_slice = None
    export_loss_map = None

try:
    from sim_rf_map.voxel_visualizer import plot_voxel_volume
except Exception:  # pragma: no cover - optional dependency
    plot_voxel_volume = None

try:
    from sim_rf_map.signal_path_tracer import trace_signal_path
    from sim_rf_map.signal_path_plot import plot_signal_profile
except Exception:  # pragma: no cover - optional dependency
    trace_signal_path = None
    plot_signal_profile = None

try:
    from sim_rf_map.gui_tx_panel import TXControlPanel
except Exception:  # pragma: no cover - optional dependency
    TXControlPanel = None

try:
    from sim_rf_map.session_export import export_session_bundle
except Exception:  # pragma: no cover - optional dependency
    export_session_bundle = None

try:
    from sim_rf_map.multi_tx_propagator import aggregate_multi_tx
except Exception:  # pragma: no cover - optional dependency
    aggregate_multi_tx = None

try:
    from sim_rf_map.propagation import simulate_basic_rf, simulate_high_physics_rf
except Exception:  # pragma: no cover - optional dependency
    simulate_basic_rf = None
    simulate_high_physics_rf = None


class _BasicPropagator:
    def compute_coverage(self, dem: np.ndarray, tx_points: list, settings: dict) -> np.ndarray:
        return np.zeros_like(dem, dtype=float)


def get_propagator(settings: dict | None = None) -> _BasicPropagator:
    return _BasicPropagator()


class Voxelizer:
    def __init__(self, settings: dict | None = None) -> None:
        self.settings = settings or {}

    def compute_voxels(self, dem: np.ndarray, tx_points: list | None = None) -> np.ndarray:
        layers = int(self.settings.get("voxel_layers", 1) or 1)
        return np.repeat(dem[None, :, :], layers, axis=0).astype(float)




class RFAnalyzerApp:
    """Main Tkinter application for RF terrain and overlay analysis."""
    _control_groups: dict = {}

    def get_str(self, key: str) -> str:
        """Return a translated string for ``key`` based on ``self.lang``."""
        if key in STRINGS:
            return STRINGS.get(key, key)
        return STRINGS.get(getattr(self, "lang", "en"), STRINGS.get("en", {})).get(key, key)
    def make_button(
        self,
        label: str,
        command: Callable,
        tooltip: str,
        icon_name: str | None = None,
        enabled: bool = True,
    ) -> ttk.Button:
        """Return a standardized toolbar button with tooltip support."""
        prefix = ""
        if icon_name:
            prefix = get_icon_text(icon_name)
            if prefix:
                prefix += " "
        btn = ttk.Button(
            self.button_frame,
            text=prefix + label,
            command=command,
        )
        btn.tooltip_text = tooltip
        if not enabled:
            btn.state(["disabled"])
        col = len(self.button_frame.grid_slaves())
        btn.grid(row=0, column=col, padx=2)
        return btn

    def install_tooltips(self) -> None:
        """Attach tooltips to all widgets that define ``tooltip_text``."""
        # Install tooltips for buttons and other widgets in the button frame
        for widget in self.button_frame.winfo_children():
            if hasattr(widget, "tooltip_text"):
                Tooltip(widget, widget.tooltip_text)

        # Install tooltips for any other frames that might contain widgets with tooltips
        for frame_name in ["entry_frame", "control_frame", "option_frame"]:
            frame = getattr(self, frame_name, None)
            if frame:
                for widget in frame.winfo_children():
                    if hasattr(widget, "tooltip_text"):
                        Tooltip(widget, widget.tooltip_text)

    def _register_control_groups(self) -> None:
        """Group buttons by dependency for quick enable/disable."""
        if hasattr(self, "_control_groups") and hasattr(self, "controls"):
            self.control_groups = {
                group: [self.controls[name] for name in names]
                for group, names in self._control_groups.items()
            }
            return
        self.btns_needing_dem = [
            self.analyze_button,
            self.export_dem_button,
            self.export_overlay_button,
            self.export_session_button,
            self.calibrate_button,
        ]
        self.btns_needing_analysis = [
            self.export_loss_button,
            self.show_slice_button,
            self.replay_button,
            self.view_3d_button,
            self.voxel_button,
            self.voxel3d_button,
            self.export_vectors_button,
            self.path_profile_button,
            self.show_path_button,
            self.export_hybrid_button,
            self.saveA_button,
            self.saveB_button,
            self.loadA_button,
            self.loadB_button,
        ]

    def _set_controls_enabled(self, group: str, value: bool) -> None:
        """Enable or disable a group of buttons."""
        if hasattr(self, "control_groups") and group in self.control_groups:
            state = tk.NORMAL if value else tk.DISABLED
            for control in self.control_groups[group]:
                control.config(state=state)
            return
        btns = {
            "dem": self.btns_needing_dem,
            "analysis": self.btns_needing_analysis,
        }[group]
        for b in btns:
            b.state(["!disabled"] if value else ["disabled"])

    def _set_status(self, message: str) -> None:
        """Update status bar message."""
        if not hasattr(self, "status") and hasattr(self, "status_label"):
            self.status_label.config(text=message)
            return
        self.status.set(message)
        self.root.update_idletasks()

    def flash_label(self, text: str, duration_ms: int = 1500) -> None:
        """Temporarily highlight window background with a status message."""
        if not hasattr(self, "status") and hasattr(self, "status_label"):
            original_text = self.status_label.cget("text")
            self.status_label.config(text=text)

            def _restore_label() -> None:
                self.status_label.config(text=original_text)

            self.root.after(duration_ms, _restore_label)
            return
        self.status.set(text)
        orig = self.root.cget("background")
        self.root.config(background="pale green")

        def _restore() -> None:
            self.root.config(background=orig)
            self.status.set("")

        self.root.after(duration_ms, _restore)

    def _update_loadbar(self, progress: float) -> None:
        """Update ASCII progress bar with ``progress`` in [0, 1]."""
        if not hasattr(self, "loadbar") and hasattr(self, "progress_bar"):
            self.progress_bar.config(value=int(progress * 100))
            return
        total = 50
        filled = int(progress * total)
        bar = "[" + ("=" * filled) + ("-" * (total - filled)) + "]"
        self.loadbar.set(bar)

    # ----- Overlay Comparison -----

    def save_overlay_snapshot(self, label: str) -> None:
        """Store a copy of the current overlay in slot ``label``."""
        if hasattr(self, "overlay_snapshots"):
            self.overlay_snapshots[label] = self.overlay_data
            return
        if self.overlay is None:
            self._set_status("No overlay to save.")
            return
        self.overlay_memory[label] = self.overlay.copy()
        self._set_status(f"Saved current overlay to slot {label}.")

    def load_overlay_snapshot(self, label: str) -> None:
        """Display the overlay stored in slot ``label`` if present."""
        if hasattr(self, "overlay_snapshots"):
            if label in self.overlay_snapshots:
                self.overlay_data = self.overlay_snapshots[label]
            return
        snap = self.overlay_memory.get(label)
        if snap is None:
            self._set_status(f"No snapshot in slot {label}.")
            return
        self.overlay = snap.copy()
        self.refresh()
        self._set_status(f"Loaded overlay from slot {label}.")

    def _init_help_panel(self) -> None:
        """Create a floating help window populated from ``docs/quick_help.md``."""
        self.help_win = tk.Toplevel(self.root)
        self.help_win.title("Quick Help")
        self.help_win.geometry("350x500")
        self.help_win.withdraw()
        text = tk.Text(self.help_win, wrap="word")
        text.pack(fill="both", expand=True)
        help_md = Path(__file__).parent / "../docs/quick_help.md"
        if help_md.exists():
            text.insert("1.0", help_md.read_text(encoding="utf-8"))
        text.config(state="disabled")
        self.help_text = text

    def _toggle_help(self, _event: tk.Event | None = None) -> None:
        """Show or hide the help window."""
        if hasattr(self, "help_panel"):
            self.help_visible = not getattr(self, "help_visible", False)
            if self.help_visible:
                self.help_panel.pack()
            else:
                self.help_panel.pack_forget()
            return
        if self.help_win.state() == "withdrawn":
            self.help_win.deiconify()
        else:
            self.help_win.withdraw()

    def _init_shortcut_hud(self) -> None:
        """Create a floating panel listing active keyboard shortcuts."""
        self.shortcut_win = tk.Toplevel(self.root)
        self.shortcut_win.title("Keyboard Shortcuts")
        self.shortcut_win.geometry("250x300")
        self.shortcut_win.withdraw()
        text = tk.Text(self.shortcut_win, wrap="word")
        text.pack(fill="both", expand=True)
        for k, v in SHORTCUTS.items():
            text.insert("end", f"{k} \u2192 {v}\n")
        text.config(state="disabled")
        self.shortcut_text = text

    def _toggle_shortcuts(self, _event: tk.Event | None = None) -> None:
        """Show or hide the shortcut reference window."""
        if self.shortcut_win.state() == "withdrawn":
            self.shortcut_win.deiconify()
        else:
            self.shortcut_win.withdraw()

    def _toggle_contrast(self) -> None:
        """Switch between normal and high-contrast themes."""
        if hasattr(self, "settings") and "high_contrast" in self.settings:
            self.settings["high_contrast"] = not self.settings["high_contrast"]
            if hasattr(self, "contrast_button"):
                self.contrast_button.config(text="Normal" if self.settings["high_contrast"] else "High Contrast")
            return
        self.use_high_contrast = not getattr(self, "use_high_contrast", False)
        style = ttk.Style(self.root)
        if self.use_high_contrast:
            style.configure(".", background="#FFFFDD", foreground="black")
            self._set_status("High Contrast Enabled")
        else:
            style.configure(".", background="", foreground="")
            self._set_status("High Contrast Disabled")

    def _init_dev_overlay(self) -> None:
        """Initialize floating developer overlay and update timer."""
        self.dev_overlay = tk.Label(
            self.root,
            bg="#000000",
            fg="lime",
            font=("Courier", 9),
            justify="left",
            anchor="ne",
            padx=5,
            pady=3,
        )
        # Position on the right side of the screen
        self.dev_overlay.place(relx=1.0, y=10, anchor="ne")
        self.dev_overlay.place_forget()
        self._dev_frame_counter = 0
        self.last_analysis_time = 0.0
        self.gpu_enabled = False
        self._dev_overlay_after_id = None

        def _update() -> None:
            if not getattr(self, "dev_overlay", None) or not self.dev_overlay.winfo_exists():
                return
            if self.dev_overlay.winfo_ismapped():
                mem = (
                    psutil.Process().memory_info().rss / (1024 ** 2)
                    if psutil is not None
                    else 0.0
                )
                info = (
                    f"Frames: {self._dev_frame_counter}\n"
                    f"Prop time: {self.last_analysis_time:.2f}s\n"
                    f"Mem: {mem:.1f}MB\n"
                    f"Mode: {self.mode_var.get()}\n"
                    f"GPU: {self.gpu_enabled}"
                )
                self.dev_overlay.config(text=info)
                self._dev_frame_counter = 0
            self._dev_overlay_after_id = self.root.after(1000, _update)

        def _cancel_dev_overlay_timer(_event: tk.Event | None = None) -> None:
            after_id = getattr(self, "_dev_overlay_after_id", None)
            if after_id:
                try:
                    self.root.after_cancel(after_id)
                except Exception:
                    pass
                self._dev_overlay_after_id = None

        self.root.bind("<Destroy>", _cancel_dev_overlay_timer, add="+")
        self._dev_overlay_after_id = self.root.after(1000, _update)

    def _init_diagnostic_overlay(self) -> None:
        """Create overlay displaying voxel resolution and inference settings."""
        self.diagnostic_overlay = tk.Label(
            self.root,
            fg="cyan",
            bg="#000000",
            font=("Courier", 9),
            anchor="ne",
            padx=5,
            pady=3,
        )
        # Position on the right side of the screen below the dev overlay
        self.diagnostic_overlay.place(relx=1.0, y=50, anchor="ne")
        self._update_diagnostic_overlay()

    def _update_diagnostic_overlay(self) -> None:
        res_percent = self.voxel_res_scale.get()
        inf = self.inference_intensity_scale.get()
        layer = self.slice_slider.get() if hasattr(self, "slice_slider") else 0
        self.diagnostic_overlay.config(
            text=f"Res: {res_percent}% | Inf: {inf}x | Layer: {layer}"
        )

    def _init_context_menu(self) -> None:
        """Enable right-click context menu on the canvas."""
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)

    def _on_canvas_right_click(self, event: tk.Event) -> None:
        if self.edit_mode:
            self.erase_mask(event)
            return
        self._show_canvas_context(event)

    def _show_canvas_context(self, event: tk.Event) -> None:
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(
            label="Remove Last TX",
            command=self.remove_last_tx,
        )
        menu.add_separator()
        menu.add_command(
            label="Help: What is this view?",
            command=lambda: self._show_help_for("canvas"),
        )
        menu.tk_popup(event.x_root, event.y_root)

    def _show_help_for(self, topic: str) -> None:
        help_texts = {
            "canvas": (
                "This is the main map view. Left-click to place transmitters. "
                "Right-click opens this menu when not editing masks."
            ),
            "overlay": (
                "The overlay shows calculated signal loss. After running "
                "analysis you can export this view or inspect slices."
            ),
        }
        messagebox.showinfo(f"Help – {topic}", help_texts.get(topic, "No help available."))

    def _init_bug_report(self) -> None:
        self.bug_button = self.make_button(
            "Report Bug",
            self._copy_diagnostics,
            "Copy system information and the most recent error traceback to the clipboard.",
        )

    def _copy_diagnostics(self) -> None:
        info = (
            f"OS: {platform.system()} {platform.release()}\n"
            f"Python: {platform.python_version()}\n"
            f"Platform: {platform.platform()}\n"
        )
        tb = getattr(sys, "last_traceback", "No traceback captured")
        text = info + "\n" + tb
        try:
            import pyperclip  # type: ignore

            pyperclip.copy(text)
            self._set_status("Bug report info copied to clipboard.")
        except Exception:
            messagebox.showinfo(
                "RF Analyzer",
                "pyperclip not installed. Diagnostic info printed to console.",
            )
            print(text)

    @contextmanager
    def busy_feedback(self, label: str = "Working..."):
        """Show wait cursor and temporary status text."""
        if not hasattr(self, "status") and hasattr(self, "status_label") and hasattr(self, "progress_bar"):
            self.status_label.config(text=label)
            self.progress_bar.grid()
            try:
                yield
            finally:
                self.progress_bar.grid_remove()
            return
        self._set_status(label)
        self.root.config(cursor="wait")
        self.root.update()
        try:
            yield
        finally:
            self.root.config(cursor="")
            self._set_status("")

    def _clear_busy(self) -> None:
        self.root.config(cursor="")
        self._set_status("")

    def _run_background(self, func: Callable, message: str = "Working...") -> None:
        from threading import Thread

        def runner() -> None:
            try:
                func()
            finally:
                self.root.after(0, self._clear_busy)

        self._set_status(message)
        self.root.config(cursor="wait")
        Thread(target=runner, daemon=True).start()

    def _resize_overlay_if_needed(self, img: Image.Image) -> Image.Image:
        """Return ``img`` scaled down to fit 800x600 if larger."""
        max_w, max_h = 800, 600
        if img.width > max_w or img.height > max_h:
            scale = min(max_w / img.width, max_h / img.height)
            new_size = (int(img.width * scale), int(img.height * scale))
            return img.resize(new_size, Image.LANCZOS)
        return img

    def _apply_theme(self, mode: str | bool) -> None:
        """Switch between dark and light UI themes."""
        if isinstance(mode, bool):
            mode = "dark" if mode else "light"
        if mode == "dark":
            apply_dark_mode(self.root)
        else:
            apply_light_mode(self.root)

    def _is_high_physics_enabled(self) -> bool:
        """Return ``True`` if advanced physics mode is active."""
        return bool(
            getattr(self, "physics_var", tk.BooleanVar(value=False)).get()
            or getattr(self, "interference_var", tk.BooleanVar(value=False)).get()
            or getattr(self, "reflection_var", tk.BooleanVar(value=False)).get()
            or getattr(self, "refraction_var", tk.BooleanVar(value=False)).get()
            or getattr(self, "deflection_var", tk.BooleanVar(value=False)).get()
            or getattr(self, "knife_edge_var", tk.BooleanVar(value=False)).get()
            or getattr(self, "fresnel_zones_var", tk.BooleanVar(value=False)).get()
        )

    def _update_voxel_params(self) -> None:
        """Update voxelization settings from UI sliders."""
        if not all(
            hasattr(self, name)
            for name in ("voxel_res_scale", "inference_intensity_scale", "depth_perception_scale", "status")
        ):
            return
        res_percent = self.voxel_res_scale.get()
        # Map percentage to scale value: 100% -> 1, 75% -> 2, 50% -> 3, 25% -> 4
        res_scale = {100: 1, 75: 2, 50: 3, 25: 4}.get(res_percent, 2)
        inf = self.inference_intensity_scale.get()
        # Get depth perception strength percentage
        depth_percent = self.depth_perception_scale.get()
        # Map percentage to strength value: 100% -> 1.0, 75% -> 0.75, 50% -> 0.5, 25% -> 0.25
        depth_strength = depth_percent / 100.0
        self.voxel_config = {"scale": res_scale, "passes": inf, "depth_strength": depth_strength}
        self._set_status(f"Voxel resolution: {res_percent}%, Inference: {inf} passes, Depth perception: {depth_percent}%")
        if self.dem is not None and generate_voxel_volume is not None:
            self.voxel_volume = generate_voxel_volume(self.dem, self.voxel_config)
            self._update_slice_slider_range()
            if self.voxel_toggle_var.get():
                self._render_hybrid_view()
        self._update_diagnostic_overlay()

    def _toggle_passive_mode(self, state: bool) -> None:
        self.passive_mode_enabled = state
        if state:
            self._start_passive_loop()
        else:
            self.passive_mode_enabled = False
        self._set_status(f"Passive mode {'enabled' if state else 'disabled'}")

    def _start_passive_loop(self) -> None:
        from threading import Thread
        import time

        def passive_worker() -> None:
            while getattr(self, "passive_mode_enabled", False):
                self.root.after(0, lambda: self._set_status("Passive: Checking telemetry overlays..."))
                time.sleep(20)

        self._passive_thread = Thread(target=passive_worker, daemon=True)
        self._passive_thread.start()

    def _stop_passive_loop(self) -> None:
        self.passive_mode_enabled = False

    def _generate_voxel_image(self) -> Image.Image:
        """Create a 2D projection of the voxel volume."""
        if self.voxel_volume is None:
            if self.dem is None or generate_voxel_volume is None:
                return self.image.convert("RGB") if self.image else Image.new("RGB", (1, 1))
            self.voxel_volume = generate_voxel_volume(self.dem, self.voxel_config)
            self._update_slice_slider_range()
        collapsed = np.max(self.voxel_volume, axis=0)
        if collapsed.max() == 0:
            scaled = collapsed.astype(np.uint8)
        else:
            scaled = np.clip((collapsed / collapsed.max()) * 255, 0, 255).astype(np.uint8)
        rgb = np.stack([scaled] * 3, axis=-1)
        img = Image.fromarray(rgb, mode="RGB").resize(self.image.size)
        return img

    def _composite_images(self, base: Image.Image, overlay: Image.Image) -> Image.Image:
        """Alpha-composite ``overlay`` over ``base`` with 50% opacity."""
        result = base.convert("RGBA")
        ov = overlay.convert("RGBA").resize(base.size)
        ov.putalpha(int(255 * 0.5))
        result.alpha_composite(ov)
        return result

    def _render_hybrid_view(self) -> None:
        """Render DEM, optional voxel base, and heatmap overlay."""
        if self.image is None:
            return
        base = self.image
        if self.voxel_toggle_var.get():
            voxel_img = self._generate_voxel_image()
            base = Image.blend(base.convert("RGBA"), voxel_img.convert("RGBA"), 0.5)
        final = base
        if self.show_overlay_var.get() and self.overlay is not None:
            final = self._composite_images(base, self.overlay)
        self.hybrid_display = final
        self.show_image(final)

    def _apply_overlay_selection(self, mode: str) -> None:
        if mode == "Heatmap":
            self._render_hybrid_view()
            return
        from sim_rf_map.overlays.overlay_registry import get_overlay
        gen = get_overlay(mode)
        if not gen:
            messagebox.showerror("RF Analyzer", f"No overlay generator found for '{mode}'")
            return
        arr = gen()
        img = self._voxel_layer_to_image(arr)
        self.hybrid_display = img
        self.show_image(img)

    @catch_errors
    def _export_hybrid(self) -> None:
        if self.hybrid_display is None:
            messagebox.showwarning("RF Analyzer", "No hybrid image to export.")
            return
        file = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not file:
            return

        def task() -> None:
            self.hybrid_display.save(file)
            write_meta_for(file, {"type": "hybrid"})
            self.root.after(0, lambda: self.flash_label(f"Hybrid view exported to {file}"))

        self._run_background(task, "Exporting hybrid view...")

    def _voxel_layer_to_image(self, layer: np.ndarray) -> Image.Image:
        data = (layer * 255).astype(np.uint8)
        rgb = np.stack([data] * 3, axis=-1)
        size = self.image.size if hasattr(self, "image") and self.image is not None else (layer.shape[1], layer.shape[0])
        return Image.fromarray(rgb, mode="RGB").resize(size)

    def _render_voxel_slice(self) -> None:
        if self.voxel_volume is None:
            return
        z = int(self.slice_slider.get())
        self.slice_label.config(text=f"Layer: {z}")
        img = self._voxel_layer_to_image(self.voxel_volume[z])
        self.hybrid_display = img
        self.show_image(img)
        self._update_diagnostic_overlay()

    def _start_slice_animation(self) -> None:
        if self._slice_timer is None:
            self._slice_timer = self.root.after(250, self._next_voxel_slice)

    def _stop_slice_animation(self) -> None:
        if self._slice_timer is not None:
            self.root.after_cancel(self._slice_timer)
            self._slice_timer = None

    def _next_voxel_slice(self) -> None:
        current = int(self.slice_slider.get())
        max_layer = int(self.slice_slider.cget("to"))
        self.slice_slider.set((current + 1) % (max_layer + 1))
        self._render_voxel_slice()
        self._slice_timer = self.root.after(250, self._next_voxel_slice)

    def _update_slice_slider_range(self) -> None:
        volume = getattr(self, "voxel_volume", None)
        if volume is None:
            volume = getattr(self, "voxel_data", None)
        if volume is not None:
            depth = volume.shape[0]
            self.slice_slider.config(from_=0, to=depth - 1)

    def _export_current_slice(self) -> None:
        if self.hybrid_display is None:
            return
        file = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not file:
            return

        def task() -> None:
            self.hybrid_display.save(file)
            write_meta_for(file, {"type": "voxel_slice", "index": int(self.slice_slider.get())})
            self.root.after(0, lambda: self.flash_label(f"Slice saved to {file}"))

        self._run_background(task, "Saving slice...")

    def _export_slice_stack(self) -> None:
        if self.voxel_volume is None:
            return
        def task() -> None:
            Path("output/slices").mkdir(parents=True, exist_ok=True)
            for z, layer in enumerate(self.voxel_volume):
                img = self._voxel_layer_to_image(layer)
                fname = f"output/slices/layer_{z:02d}.png"
                img.save(fname)
                write_meta_for(fname, {"type": "voxel_slice", "index": z})
            self.root.after(0, lambda: self.flash_label("All slices exported to output/slices/"))

        self._run_background(task, "Exporting voxel stack...")

    def _launch_export_wizard(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Export Wizard")
        tk.Label(dialog, text="Overlay Type").pack()
        option_var = tk.StringVar(value="Heatmap")
        tk.OptionMenu(dialog, option_var, "Heatmap", "LOS Zones", "Interference", "Reflections").pack()
        tk.Button(dialog, text="Export", command=lambda: self._do_export_wizard(option_var.get(), dialog)).pack(pady=5)

    def _do_export_wizard(self, overlay_name: str, dialog: tk.Toplevel) -> None:
        from sim_rf_map.overlays.overlay_registry import get_overlay
        if overlay_name == "Heatmap":
            img = self.hybrid_display
        else:
            gen = get_overlay(overlay_name)
            if not gen:
                dialog.destroy()
                messagebox.showerror("RF Analyzer", f"No overlay generator found for '{overlay_name}'")
                return
            arr = gen()
            img = self._voxel_layer_to_image(arr)
        file = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not file:
            dialog.destroy()
            return
        img.save(file)
        self.flash_label(f"Exported {overlay_name} to {file}")
        dialog.destroy()

    def _render_signal_cones(self) -> None:
        if not getattr(self, "viewer", None):
            return
        if not self.signal_cones_var.get():
            return
        try:
            from sim_rf_map.visual.signal_cones import create_cone
        except Exception:
            return
        for tx in self.txs:
            pos = (tx["x"], tx["y"], 0)
            cone = create_cone(pos, direction=[0, 0, 1])
            self.viewer.view.addItem(cone)

    def _apply_interference_map(self, dem: np.ndarray) -> None:
        if not self.interference_var.get():
            return
        try:
            from sim_rf_map.physics.interference import compute_interference
            from sim_rf_map.propagation.high_physics import simulate_one_tower
        except Exception:
            return
        volumes = [simulate_one_tower(dem, tx) for tx in self.txs]
        self.interference_map = compute_interference(volumes)
        self._render_frame_to_canvas(self.interference_map)

    def _maybe_apply_reflection(self, volume: np.ndarray) -> np.ndarray:
        if not self.reflection_var.get():
            return volume
        try:
            from sim_rf_map.physics.reflection import apply_reflection
        except Exception:
            return volume
        if self.dem is None:
            return volume
        return apply_reflection(volume, self.dem, self.txs)

    def _start_replay(self) -> None:
        if self.loss_volume is None:
            messagebox.showwarning("RF Analyzer", "Run analysis first.")
            return
        self.replay_index = 0
        if self._replay_timer is not None:
            self.root.after_cancel(self._replay_timer)
        self._replay_timer = self.root.after(42, self._next_replay_frame)

    def _next_replay_frame(self) -> None:
        if self.loss_volume is None:
            return
        if self.replay_index >= self.loss_volume.shape[0]:
            if self._replay_timer is not None:
                self.root.after_cancel(self._replay_timer)
                self._replay_timer = None
            return
        frame = self.loss_volume[self.replay_index]
        if self.fresnel_var.get():
            try:
                from sim_rf_map.propagation.fresnel import apply_fresnel_overlay

                frame = apply_fresnel_overlay(frame, self.txs)
            except Exception:
                pass
        self._render_frame_to_canvas(frame)
        self.replay_index += 1
        self._replay_timer = self.root.after(42, self._next_replay_frame)

    def _render_frame_to_canvas(self, frame: np.ndarray) -> None:
        if not hasattr(self, "image") and hasattr(self, "image_container"):
            arr = np.clip(frame, 0, 1)
            img = Image.fromarray((arr * 255).astype(np.uint8))
            resized = img.resize(frame.shape[::-1])
            photo = ImageTk.PhotoImage(resized)
            self.canvas.itemconfig(self.image_container, image=photo)
            self.current_image = photo
            return
        if np.isnan(frame).all() or frame.size == 0:
            self._set_status("Dead zone render failed: invalid data.")
            return
        if self.heatmap_centering_var.get():
            center_val = np.percentile(frame, 90)
        else:
            center_val = np.percentile(frame, 10)
        normed = np.clip((frame - center_val + 50) / 100, 0, 1)
        heatmap = generate_heatmap(normed, cmap=self.heatmap_colormap)
        heatmap = self._resize_overlay_if_needed(heatmap)
        img = Image.blend(self.image.convert("RGBA"), heatmap.convert("RGBA"), self.alpha_var.get())
        self.show_image(img)

    def _apply_view_mode(self, *_evt: tk.Event | None) -> None:
        """Switch between normal and side-by-side overlay views."""
        mode = self.view_mode.get()
        if mode == "Normal":
            self.split_canvas.pack_forget()
            self.display_frame.pack(padx=10, pady=10)
            self.refresh()
        elif mode == "Side-by-Side":
            if self.overlay_memory["A"] is not None and self.overlay_memory["B"] is not None:
                self.display_frame.pack_forget()
                self.split_canvas.pack(padx=10, pady=10)
                self.split_canvas.load_pair(self.overlay_memory["A"], self.overlay_memory["B"])
            else:
                self._set_status("Both slots A and B must be saved first.")
                self.view_mode.set("Normal")
        else:
            self._set_status("Swipe mode is under construction.")
            self.view_mode.set("Normal")

    def _toggle_legend(self) -> None:
        """Show or hide the heatmap legend frame."""
        if self.show_legend_var.get():
            self.legend_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        else:
            self.legend_frame.pack_forget()

    def _on_mode_change(self, mode_name: str) -> None:
        """Handle changes to the specialized View Mode selector."""
        self.active_mode = mode_name
        self._update_overlay_style()

    def _update_overlay_style(self) -> None:
        mode = self.active_mode
        if mode == "Void Mapping Mode":
            self.overlay_colormap = "gray_r"
            self.colorbar_config = {"shrink": 0.7, "aspect": 15, "pad": 0.02}
            self._set_status("Void Mapping: darker = stronger signal")
            self._enable_los_overlay(False)
        elif mode == "LoS Diagnostic Mode":
            self.overlay_colormap = "viridis"
            self.colorbar_config = {"shrink": 0.8, "aspect": 10, "pad": 0.05}
            self._enable_los_overlay(True)
        else:
            self.overlay_colormap = "viridis"
            self.colorbar_config = {"shrink": 0.8, "aspect": 12, "pad": 0.05}
            self._enable_los_overlay(False)
        if self.overlay_data is not None and self.overlay_visible:
            self._render_overlay()

    def _enable_los_overlay(self, enable: bool) -> None:
        if enable:
            self.los_overlay = self._compute_los_overlay()
        else:
            self.los_overlay = None

    def _compute_los_overlay(self) -> Image.Image | None:
        if self.dem is None or not self.txs:
            return None
        mask = np.zeros_like(self.dem, dtype=np.uint8)
        for tx in self.txs:
            los = compute_los(self.dem, (tx["y"], tx["x"]))
            mask = np.maximum(mask, los.astype(np.uint8))
        return make_translucent_mask(mask, (255, 0, 0, 80))

    def _toggle_before_after(self) -> None:
        if self.overlay_data is None:
            return
        if self.overlay_visible:
            self.canvas.delete("all")
            self.show_image(self.image)
            self._set_status("View: Terrain Only")
        else:
            self._render_overlay()
            self._set_status("View: Terrain + Simulation Overlay")
        self.overlay_visible = not self.overlay_visible

    def _render_overlay(self) -> None:
        if self.overlay_data is None:
            return
        heatmap = generate_heatmap(self.overlay_data, cmap=self.overlay_colormap)
        heatmap = self._resize_overlay_if_needed(heatmap)
        if self.los_overlay is not None and self.active_mode == "LoS Diagnostic Mode":
            overlay = Image.alpha_composite(heatmap.convert("RGBA"), self.los_overlay.resize(heatmap.size))
        else:
            overlay = heatmap
        self.overlay = overlay
        if plt is not None:
            legend_img = create_colorbar(
                float(self.overlay_data.min()),
                float(self.overlay_data.max()),
                cmap=self.overlay_colormap,
                **self.colorbar_config,
            )
            if legend_img is not None:
                self.legend_imgtk = ImageTk.PhotoImage(legend_img)
                self.legend_image_label.configure(image=self.legend_imgtk)
        self.refresh()

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("RF Analyzer")
        self.lang = "en"
        self.image_path: Path | None = None
        self.image: Image.Image | None = None
        self.overlay: Image.Image | None = None
        self.txs: list[dict] = []
        self.current_tx: tuple[int, int] | None = None
        self.veg_mask: np.ndarray | None = None
        self.veg_density: np.ndarray | None = None
        self.water_mask: np.ndarray | None = None
        self.water_activity: np.ndarray | None = None
        self.edit_mode: str | None = None
        self.calibration = {"scale": 1.0, "offset": 0.0}
        self.georef: dict | None = None
        self.dem: np.ndarray | None = None
        self.secondary_image: Image.Image | None = None
        self.midas_dem: np.ndarray | None = None
        self.physics_dem: np.ndarray | None = None
        self.confidence_map: np.ndarray | None = None
        self.session_file = Path("session.json")
        self.contours: list[tuple[float, list[np.ndarray]]] | None = None
        self.loss_volume: np.ndarray | None = None
        self.data: np.ndarray | None = None
        self.overlay_matrix: np.ndarray | None = None
        self.overlay_img: ImageTk.PhotoImage | None = None
        self.legend_imgtk: ImageTk.PhotoImage | None = None
        self.last_hash: str = ""
        self.last_analysis_time: float = 0.0
        self.original_shape: tuple[int, int] | None = None
        self.disp_size: tuple[int, int] = (1, 1)
        self.img_offset: tuple[int, int] = (0, 0)
        self.undo_stack: list[np.ndarray] = []
        self.redo_stack: list[np.ndarray] = []
        # ID of crosshair elements when drawing on Canvas
        self._crosshair: tuple[int, int] | None = None
        self.voxel_volume: np.ndarray | None = None
        self.hybrid_display: Image.Image | None = None
        self.voxel_config: dict = {"scale": 2, "passes": 5}
        self._slice_timer: str | None = None
        self._replay_timer: str | None = None
        self.replay_index: int = 0
        self.passive_mode_enabled = False
        self._passive_thread = None

        from sim_rf_map.overlays.overlay_registry import register_overlay
        register_overlay("voxel", self._generate_voxel_image)
        register_overlay("heatmap", lambda: self.overlay)

        # overlay rendering state
        self.active_mode = "Standard View"
        self.overlay_colormap = "viridis"
        self.heatmap_colormap = LinearSegmentedColormap.from_list(
            "spark_rgb", ["blue", "cyan", "green", "yellow", "red"]
        )
        self.colorbar_config = {"shrink": 0.8, "aspect": 12, "pad": 0.05}
        self.overlay_data: np.ndarray | None = None
        self.overlay_visible = True
        self.los_overlay: Image.Image | None = None

        # memory slots for before/after overlay comparison
        self.overlay_memory: dict[str, Image.Image | None] = {"A": None, "B": None}

        # Apply a modern scientific style to the root window
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Segoe UI", 9))
        self.style.configure("TLabel", font=("Segoe UI", 9))
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TNotebook", background="#f0f0f0")
        self.style.configure("TNotebook.Tab", padding=[10, 2], font=("Segoe UI", 9, "bold"))

        # Main container for all controls
        self.main_container = ttk.Frame(root)
        self.main_container.pack(fill="x", padx=10, pady=5)

        # Create a notebook for tabbed interface
        self.control_notebook = ttk.Notebook(self.main_container)
        self.control_notebook.pack(fill="x", padx=5, pady=5)

        # Create tabs for different control groups
        self.file_tab = ttk.Frame(self.control_notebook)
        self.analysis_tab = ttk.Frame(self.control_notebook)
        self.visualization_tab = ttk.Frame(self.control_notebook)
        self.physics_tab = ttk.Frame(self.control_notebook)
        self.editing_tab = ttk.Frame(self.control_notebook)
        self.advanced_tab = ttk.Frame(self.control_notebook)

        # Add tabs to notebook
        self.control_notebook.add(self.file_tab, text="File Operations")
        self.control_notebook.add(self.analysis_tab, text="Analysis")
        self.control_notebook.add(self.visualization_tab, text="Visualization")
        self.control_notebook.add(self.physics_tab, text="Physics")
        self.control_notebook.add(self.editing_tab, text="Editing")
        self.control_notebook.add(self.advanced_tab, text="Advanced")

        # Create frames for button groups
        self.button_frame = ttk.Frame(self.file_tab)
        self.button_frame.pack(pady=5, fill="x")

        # Create file operation buttons in the file tab
        self.file_buttons_frame = ttk.LabelFrame(self.file_tab, text="File Operations")
        self.file_buttons_frame.pack(pady=5, fill="x", padx=10)

        file_buttons_grid = ttk.Frame(self.file_buttons_frame)
        file_buttons_grid.pack(pady=5, padx=5)
        self.button_frame = file_buttons_grid

        # Row 1: Basic file operations
        self.open_button = self.make_button(
            "Open Image",
            self.open_image,
            "Load an image or GeoTIFF to begin analysis.\n\n"
            "WORKFLOW: This is the first step in any analysis - you must load an image before proceeding.\n\n"
            "TIPS:\n"
            "• Supported formats: PNG, JPEG, TIFF, GeoTIFF\n"
            "• GeoTIFF files will automatically provide geographic coordinates\n"
            "• Higher resolution images provide more detailed analysis\n\n"
            "Shortcut: Ctrl+O",
            icon_name="open",
        )
        self.open_button.grid(row=0, column=0, padx=5, pady=5, in_=file_buttons_grid)

        self.load_secondary_button = self.make_button(
            "Load Secondary",
            self.load_secondary,
            "Load an optional secondary image for DEM fusion.\n\n"
            "USAGE: This allows you to combine two images to create a more accurate terrain model.\n\n"
            "WHEN TO USE:\n"
            "• When you have multiple perspectives of the same area\n"
            "• When combining satellite imagery with elevation data\n"
            "• To improve depth estimation accuracy",
        )
        self.load_secondary_button.grid(row=0, column=1, padx=5, pady=5, in_=file_buttons_grid)

        self.save_session_button = self.make_button(
            "Save Session",
            self._save_session,
            "Save your current work to a JSON session file.\n\n"
            "WHAT'S SAVED:\n"
            "• Current image and DEM references\n"
            "• Transmitter configurations\n"
            "• Analysis settings and parameters\n"
            "• UI state and preferences\n\n"
            "TIP: Save sessions regularly to prevent data loss and to create checkpoints in your workflow.",
            icon_name="save",
        )
        self.save_session_button.grid(row=0, column=2, padx=5, pady=5, in_=file_buttons_grid)

        self.load_session_button = self.make_button(
            "Load Session",
            self._load_session,
            "Restore a previously saved session.\n\n"
            "WHAT'S RESTORED:\n"
            "• Image and DEM references (original files must still be accessible)\n"
            "• Transmitter configurations and locations\n"
            "• Analysis settings and parameters\n"
            "• UI state and preferences\n\n"
            "NOTE: This will replace your current session. Save your work first if needed.",
            icon_name="open",
        )
        self.load_session_button.grid(row=0, column=3, padx=5, pady=5, in_=file_buttons_grid)

        # Row 2: Export operations
        self.export_frame = ttk.LabelFrame(self.file_tab, text="Export Options")
        self.export_frame.pack(pady=5, fill="x", padx=10)

        export_buttons_grid = ttk.Frame(self.export_frame)
        export_buttons_grid.pack(pady=5, padx=5)
        self.button_frame = export_buttons_grid

        self.export_overlay_button = self.make_button(
            "Export Overlay",
            self.export_overlay,
            "Save the current RF overlay image with georeference data.\n\n"
            "OUTPUT FORMATS:\n"
            "• PNG: For general use and presentations\n"
            "• GeoTIFF: For use in GIS applications with geographic coordinates\n\n"
            "TIP: The exported overlay can be imported into QGIS, ArcGIS, or Google Earth.",
            icon_name="export",
        )
        self.export_overlay_button.grid(row=0, column=0, padx=5, pady=5, in_=export_buttons_grid)

        self.export_dem_button = self.make_button(
            "Export DEM",
            self.export_dem,
            "Export the Digital Elevation Model (DEM) to various formats.\n\n"
            "OUTPUT OPTIONS:\n"
            "• PNG: Grayscale height map\n"
            "• NumPy (.npy): Raw numerical data for further processing\n"
            "• GeoTIFF: For use in GIS applications\n\n"
            "USE CASES: Terrain analysis, 3D printing, integration with other RF tools.",
            icon_name="dem",
        )
        self.export_dem_button.grid(row=0, column=1, padx=5, pady=5, in_=export_buttons_grid)

        self.export_loss_button = self.make_button(
            "Export Loss",
            self.export_loss,
            "Save computed RF loss volume as a .npy file for further processing.\n\n"
            "DATA FORMAT:\n"
            "• NumPy (.npy) file containing the 3D loss volume matrix\n"
            "• Can be imported into Python, MATLAB, or other scientific tools\n\n"
            "USE CASES:\n"
            "• Advanced signal analysis in external tools\n"
            "• Custom visualization or processing\n"
            "• Integration with other RF planning software\n\n"
            "Shortcut: Ctrl+E",
            icon_name="export",
            enabled=False,
        )
        self.export_loss_button.grid(row=0, column=2, padx=5, pady=5, in_=export_buttons_grid)

        self.export_vectors_button = self.make_button(
            "Export Vectors",
            self.export_vectors,
            "Save signal contour vectors to vector file formats.\n\n"
            "OUTPUT FORMATS:\n"
            "• SVG: For use in vector graphics applications\n"
            "• GeoJSON: For GIS applications with geographic coordinates\n\n"
            "USE CASES:\n"
            "• Creating coverage maps for reports and presentations\n"
            "• Integrating RF coverage data with other map layers in GIS\n"
            "• Generating precise coverage boundary documentation",
            icon_name="export",
        )
        self.export_vectors_button.grid(row=0, column=3, padx=5, pady=5, in_=export_buttons_grid)

        self.export_session_button = self.make_button(
            "Export Session",
            self.export_session,
            "Save your entire work session for sharing or future use.\n\n"
            "WHAT'S INCLUDED:\n"
            "• Digital Elevation Model (DEM)\n"
            "• RF overlay and analysis results\n"
            "• Transmitter configurations and locations\n"
            "• Mask layers (vegetation, water)\n\n"
            "USAGE:\n"
            "• Share complete scenarios with colleagues\n"
            "• Create backups of your work\n"
            "• Document project configurations for reports",
            icon_name="export",
        )
        self.export_session_button.grid(row=1, column=0, padx=5, pady=5, in_=export_buttons_grid)

        self.export_hybrid_button = self.make_button(
            "Export Hybrid",
            self._export_hybrid,
            "Save the current composite visualization as a PNG image.\n\n"
            "WHAT'S INCLUDED:\n"
            "• Voxelized terrain representation\n"
            "• Base Digital Elevation Model (DEM)\n"
            "• RF heatmap overlay (if enabled)\n\n"
            "IDEAL FOR:\n"
            "• Presentations and reports\n"
            "• Documentation of analysis results\n"
            "• Visual comparison of different propagation scenarios",
            icon_name="export",
            enabled=False,
        )
        self.export_hybrid_button.grid(row=1, column=1, padx=5, pady=5, in_=export_buttons_grid)

        self.export_slice_button = self.make_button(
            "Export Slice",
            self._export_current_slice,
            "Save the currently displayed elevation slice as a PNG image.\n\n"
            "WHAT IT EXPORTS:\n"
            "• The specific horizontal cross-section currently shown in the slice view\n"
            "• RF propagation at the current elevation level\n\n"
            "TIP: Use the slice slider to select the specific elevation level you want to export.",
            icon_name="export",
        )
        self.export_slice_button.grid(row=1, column=2, padx=5, pady=5, in_=export_buttons_grid)

        self.export_stack_button = self.make_button(
            "Export Stack",
            self._export_slice_stack,
            "Export all elevation slices as a sequence of PNG images.\n\n"
            "OUTPUT:\n"
            "• Series of PNG files in the output/slices/ directory\n"
            "• One image per elevation level in the model\n\n"
            "USE CASES:\n"
            "• Creating animations of signal propagation through different elevations\n"
            "• Detailed analysis of RF behavior at all heights\n"
            "• Comprehensive documentation of 3D propagation patterns",
            icon_name="export",
        )
        self.export_stack_button.grid(row=1, column=3, padx=5, pady=5, in_=export_buttons_grid)

        self.export_wizard_button = self.make_button(
            "Export Wizard",
            self._launch_export_wizard,
            "Open the advanced export options dialog.\n\n"
            "FEATURES:\n"
            "• Choose from multiple overlay types (standard, voxel, hybrid)\n"
            "• Select output format (PNG, GeoTIFF, etc.)\n"
            "• Configure export resolution and quality\n\n"
            "WHEN TO USE:\n"
            "• When you need precise control over export settings\n"
            "• For creating specialized outputs for different purposes\n"
            "• When exporting for specific GIS or presentation requirements",
            icon_name="export",
        )
        self.export_wizard_button.grid(row=2, column=0, padx=5, pady=5, in_=export_buttons_grid)

        # Help and shortcuts in file tab
        self.help_frame = ttk.LabelFrame(self.file_tab, text="Help & Documentation")
        self.help_frame.pack(pady=5, fill="x", padx=10)

        help_buttons_grid = ttk.Frame(self.help_frame)
        help_buttons_grid.pack(pady=5, padx=5)
        self.button_frame = help_buttons_grid

        self.help_button = self.make_button(
            "Help",
            lambda: self._toggle_help(None),
            "Open the help documentation panel.\n\n"
            "CONTENTS:\n"
            "• Getting started guide\n"
            "• Feature explanations\n"
            "• Troubleshooting tips\n\n"
            "TIP: The help panel can remain open while you work.\n\n"
            "Shortcut: F1",
            icon_name="help",
        )
        self.help_button.grid(row=0, column=0, padx=5, pady=5, in_=help_buttons_grid)

        self.shortcut_button = self.make_button(
            "Shortcuts",
            lambda: self._toggle_shortcuts(None),
            "Display a list of keyboard shortcuts.\n\n"
            "BENEFITS:\n"
            "• Work faster with keyboard commands\n"
            "• Learn time-saving shortcuts for common operations\n"
            "• Improve your workflow efficiency\n\n"
            "TIP: Keep this panel open while learning the application.\n\n"
            "Shortcut: Ctrl+H",
        )
        self.shortcut_button.grid(row=0, column=1, padx=5, pady=5, in_=help_buttons_grid)

        # Analysis tab
        self.analysis_controls_frame = ttk.LabelFrame(self.analysis_tab, text="Analysis Controls")
        self.analysis_controls_frame.pack(pady=5, fill="x", padx=10)

        analysis_buttons_grid = ttk.Frame(self.analysis_controls_frame)
        analysis_buttons_grid.pack(pady=5, padx=5)
        self.button_frame = analysis_buttons_grid

        self.analyze_button = self.make_button(
            self.get_str("analyze_btn"),
            self.analyze,
            self.get_str("tooltip_analyze") + "\n\n"
            "WORKFLOW: After placing transmitters, run this to calculate signal propagation.\n\n"
            "WHAT IT DOES:\n"
            "• Generates a Digital Elevation Model (DEM) from the image\n"
            "• Calculates RF propagation based on terrain and transmitter properties\n"
            "• Creates a heatmap overlay showing signal strength\n\n"
            "Shortcut: Ctrl+R",
            icon_name="analyze",
            enabled=False,
        )
        self.analyze_button.grid(row=0, column=0, padx=5, pady=5, in_=analysis_buttons_grid)

        self.remove_tx_button = self.make_button(
            "Remove TX",
            self.remove_last_tx,
            "Remove the most recently placed transmitter from the map.\n\n"
            "USAGE: Use this to correct transmitter placement mistakes.\n\n"
            "NOTE: This removes transmitters in reverse order (last placed is first removed).",
        )
        self.remove_tx_button.grid(row=0, column=1, padx=5, pady=5, in_=analysis_buttons_grid)

        self.calibrate_button = self.make_button(
            "Calibrate DEM",
            self.calibrate,
            "Manually set DEM scale and offset values for accurate elevations.\n\n"
            "WHEN TO USE:\n"
            "• When you know the actual elevation range of your area\n"
            "• To match the DEM to real-world elevation data\n"
            "• When combining multiple data sources\n\n"
            "PARAMETERS:\n"
            "• Scale: Multiplier for elevation values (default: 1.0)\n"
            "• Offset: Value added to all elevations in meters (default: 0.0)",
        )
        self.calibrate_button.grid(row=0, column=2, padx=5, pady=5, in_=analysis_buttons_grid)

        # Transmitter panel in analysis tab
        self.tx_panel_frame = ttk.LabelFrame(self.analysis_tab, text="Transmitter Configuration")
        self.tx_panel_frame.pack(pady=5, fill="x", padx=10)
        self.tx_panel = TXControlPanel(self.tx_panel_frame)
        self.freq_var = self.tx_panel.tx_freq_var
        self.power_var = self.tx_panel.tx_power_var
        self.height_var = self.tx_panel.tx_height_var

        # Model selection in analysis tab
        self.model_frame = ttk.LabelFrame(self.analysis_tab, text="Propagation Model")
        self.model_frame.pack(pady=5, fill="x", padx=10)

        model_grid = ttk.Frame(self.model_frame)
        model_grid.pack(pady=5, padx=5)

        ttk.Label(model_grid, text="Model").grid(row=0, column=0, sticky="w", padx=5)
        self.model_var = tk.StringVar(value="FSPL")
        model_menu = ttk.OptionMenu(
            model_grid, self.model_var, "FSPL", "Longwave", "Shortwave", "Cellular", "Satcom"
        )
        model_menu.grid(row=0, column=1, padx=5)
        Tooltip(
            model_menu,
            "Select the RF propagation model for analysis.\n\n"
            "MODEL OPTIONS:\n"
            "• FSPL (Free Space Path Loss): Basic line-of-sight model, ideal for open areas\n"
            "• Longwave: Best for low frequencies (<30 MHz), accounts for ground wave propagation\n"
            "• Shortwave: Optimized for 3-30 MHz, includes ionospheric reflection\n"
            "• Cellular: Designed for mobile communications (700-2600 MHz), includes urban effects\n"
            "• Satcom: For satellite communications, accounts for atmospheric effects\n\n"
            "TIP: Choose the model that best matches your frequency band and environment."
        )

        ttk.Label(model_grid, text="Parameter").grid(row=0, column=2, sticky="w", padx=5)
        self.param_var = tk.StringVar()
        param_entry = ttk.Entry(model_grid, width=6, textvariable=self.param_var)
        param_entry.grid(row=0, column=3, padx=5)
        Tooltip(
            param_entry,
            "Enter an optional model parameter for advanced configuration.\n\n"
            "PARAMETER USAGE BY MODEL:\n"
            "• FSPL: Atmospheric attenuation factor (default: 0)\n"
            "• Longwave: Ground conductivity (0.001-0.03, default: 0.005)\n"
            "• Shortwave: Ionospheric reflection efficiency (0-1, default: 0.7)\n"
            "• Cellular: Urban density factor (1-5, default: 3)\n"
            "• Satcom: Atmospheric moisture (0-100%, default: 50)\n\n"
            "Leave blank to use default values."
        )

        ttk.Label(model_grid, text="DEM Source").grid(row=0, column=4, sticky="w", padx=5)
        self.dem_source_var = tk.StringVar(value="Fused")
        dem_menu = ttk.OptionMenu(model_grid, self.dem_source_var, "Fused", "MiDaS", "Physics")
        dem_menu.grid(row=0, column=5, padx=5)
        Tooltip(
            dem_menu,
            "Choose which Digital Elevation Model source to use for analysis. "
            "Options depend on what data you have loaded."
        )

        # Visualization tab
        self.visualization_controls_frame = ttk.LabelFrame(self.visualization_tab, text="Visualization Controls")
        self.visualization_controls_frame.pack(pady=5, fill="x", padx=10)

        viz_buttons_grid = ttk.Frame(self.visualization_controls_frame)
        viz_buttons_grid.pack(pady=5, padx=5)
        self.button_frame = viz_buttons_grid

        self.view_3d_button = self.make_button(
            "3D View",
            self.show_3d,
            "Open a 3D visualization of the current terrain model.\n\n"
            "WHAT IT SHOWS:\n"
            "• 3D rendering of the Digital Elevation Model (DEM)\n"
            "• Terrain features like hills, valleys, and mountains\n\n"
            "INTERACTION:\n"
            "• Click and drag to rotate the 3D view\n"
            "• Right-click and drag to pan\n"
            "• Scroll to zoom in/out\n\n"
            "TIP: Use this to verify that the terrain model looks correct before running analysis.",
            icon_name="view3d",
            enabled=False,
        )
        self.view_3d_button.grid(row=0, column=0, padx=5, pady=5, in_=viz_buttons_grid)

        self.voxel_button = self.make_button(
            "Voxel Volume",
            self.show_voxels,
            "Visualize the 3D voxelized terrain model.\n\n"
            "WHAT IT SHOWS:\n"
            "• 3D representation of terrain as discrete volume elements (voxels)\n"
            "• How the terrain is modeled internally for RF calculations\n\n"
            "WHEN TO USE:\n"
            "• To verify terrain modeling accuracy\n"
            "• When troubleshooting unexpected RF propagation results\n"
            "• For understanding how terrain features affect signal paths",
        )
        self.voxel_button.grid(row=0, column=1, padx=5, pady=5, in_=viz_buttons_grid)

        self.voxel3d_button = self.make_button(
            "3D Voxel",
            self._open_voxel_3d,
            "Open an interactive 3D view of the voxel volume.\n\n"
            "FEATURES:\n"
            "• Real-time 3D rendering with rotation and zoom\n"
            "• Visualization of signal cones from transmitters\n"
            "• Color-coded representation of terrain and signal paths\n\n"
            "REQUIREMENTS:\n"
            "• Requires PyQtGraph library\n"
            "• More resource-intensive than the standard 3D view",
            enabled=False,
        )
        self.voxel3d_button.grid(row=0, column=2, padx=5, pady=5, in_=viz_buttons_grid)

        self.path_profile_button = self.make_button(
            "Path Profile",
            self.show_path_profile,
            "Plot the signal path profile between transmitters.\n\n"
            "WHAT IT SHOWS:\n"
            "• Elevation profile between the first and last transmitter\n"
            "• Line-of-sight analysis\n"
            "• Terrain obstructions affecting signal propagation\n\n"
            "INTERPRETATION:\n"
            "• Peaks represent hills or mountains that may block signals\n"
            "• Valleys show areas where signals might propagate more freely\n"
            "• Use to identify optimal transmitter placement",
        )
        self.path_profile_button.grid(row=0, column=3, padx=5, pady=5, in_=viz_buttons_grid)

        self.show_path_button = self.make_button(
            "Show Path",
            self._start_path_selection,
            "Analyze signal path between two points.\n\n"
            "HOW TO USE:\n"
            "1. Click this button to enter path selection mode\n"
            "2. Select a transmitter as the starting point\n"
            "3. Click anywhere on the map as the endpoint\n\n"
            "WHAT IT SHOWS:\n"
            "• Terrain profile along the selected path\n"
            "• Signal loss at each point along the path\n"
            "• Fresnel zone and line-of-sight analysis",
        )
        self.show_path_button.grid(row=1, column=0, padx=5, pady=5, in_=viz_buttons_grid)

        self.show_slice_button = self.make_button(
            "Show Slice",
            self.show_slice,
            "Display an interactive slice through the RF loss volume.\n\n"
            "WHAT IT SHOWS:\n"
            "• Horizontal cross-sections of the RF propagation at different heights\n"
            "• Signal strength variations across the terrain at a specific elevation\n\n"
            "USAGE: Use the slider to move through different elevation levels.\n\n"
            "Shortcut: Ctrl+L",
            enabled=False,
        )
        self.show_slice_button.grid(row=1, column=1, padx=5, pady=5, in_=viz_buttons_grid)

        self.replay_button = self.make_button(
            "Replay Prop",
            self._start_replay,
            "Replay the propagation volume as an animation.\n\n"
            "WHAT IT SHOWS:\n"
            "• Animated view of signal propagation through different elevation levels\n"
            "• Helps visualize how signals interact with 3D terrain\n\n"
            "CONTROLS: Use the slider that appears to control animation speed.",
            enabled=False,
        )
        self.replay_button.grid(row=1, column=2, padx=5, pady=5, in_=viz_buttons_grid)

        # Overlay comparison in visualization tab
        self.overlay_comparison_frame = ttk.LabelFrame(self.visualization_tab, text="Overlay Comparison")
        self.overlay_comparison_frame.pack(pady=5, fill="x", padx=10)

        comparison_grid = ttk.Frame(self.overlay_comparison_frame)
        comparison_grid.pack(pady=5, padx=5)
        self.button_frame = comparison_grid

        self.saveA_button = self.make_button(
            "Save A",
            lambda: self.save_overlay_snapshot("A"),
            "Save the current overlay to memory slot A.\n\n"
            "USAGE SCENARIO:\n"
            "• Save your baseline or reference overlay configuration\n"
            "• Store a 'before' state when testing different parameters\n\n"
            "WORKFLOW TIP:\n"
            "1. Save current overlay to slot A\n"
            "2. Make changes to parameters or transmitters\n"
            "3. Run new analysis\n"
            "4. Save new overlay to slot B\n"
            "5. Compare results using View A and View B buttons",
            enabled=False,
        )
        self.saveA_button.grid(row=0, column=0, padx=5, pady=5, in_=comparison_grid)

        self.saveB_button = self.make_button(
            "Save B",
            lambda: self.save_overlay_snapshot("B"),
            "Save the current overlay to memory slot B.\n\n"
            "USAGE SCENARIO:\n"
            "• Save your modified or alternative overlay configuration\n"
            "• Store an 'after' state when testing different parameters\n\n"
            "WORKFLOW TIP:\n"
            "Use in conjunction with Save A, View A, and View B for quick A/B testing of different configurations.",
            enabled=False,
        )
        self.saveB_button.grid(row=0, column=1, padx=5, pady=5, in_=comparison_grid)

        self.loadA_button = self.make_button(
            "View A",
            lambda: self.load_overlay_snapshot("A"),
            "Display the overlay stored in memory slot A.\n\n"
            "WHEN TO USE:\n"
            "• To recall a previously saved overlay configuration\n"
            "• When comparing different analysis results\n"
            "• To return to a baseline configuration after testing alternatives\n\n"
            "NOTE: This will replace the current overlay display but won't affect your current settings.",
            enabled=False,
        )
        self.loadA_button.grid(row=0, column=2, padx=5, pady=5, in_=comparison_grid)

        self.loadB_button = self.make_button(
            "View B",
            lambda: self.load_overlay_snapshot("B"),
            "Display the overlay stored in memory slot B.\n\n"
            "WHEN TO USE:\n"
            "• To recall a previously saved alternative overlay configuration\n"
            "• When comparing different analysis results\n"
            "• To view the 'after' state in an A/B comparison\n\n"
            "TIP: Quickly toggle between View A and View B to see differences between configurations.",
            enabled=False,
        )
        self.loadB_button.grid(row=0, column=3, padx=5, pady=5, in_=comparison_grid)

        # Editing tab
        self.editing_controls_frame = ttk.LabelFrame(self.editing_tab, text="Editing Controls")
        self.editing_controls_frame.pack(pady=5, fill="x", padx=10)

        editing_buttons_grid = ttk.Frame(self.editing_controls_frame)
        editing_buttons_grid.pack(pady=5, padx=5)
        self.button_frame = editing_buttons_grid

        self.edit_veg_button = self.make_button(
            "Edit Veg",
            lambda: self.start_edit("veg"),
            "Paint vegetation mask regions on the image to control foliage attenuation.\n\n"
            "HOW TO USE:\n"
            "• Left-click and drag to paint vegetation areas\n"
            "• Right-click and drag to erase vegetation areas\n\n"
            "EFFECT ON SIMULATION:\n"
            "• Vegetation increases signal attenuation\n"
            "• Denser vegetation (darker green) causes more signal loss\n"
            "• Useful for modeling forests, parks, and other foliage-heavy areas",
        )
        self.edit_veg_button.grid(row=0, column=0, padx=5, pady=5, in_=editing_buttons_grid)

        self.edit_water_button = self.make_button(
            "Edit Water",
            lambda: self.start_edit("water"),
            "Paint water mask regions on the image to model water bodies.\n\n"
            "HOW TO USE:\n"
            "• Left-click and drag to paint water areas\n"
            "• Right-click and drag to erase water areas\n\n"
            "EFFECT ON SIMULATION:\n"
            "• Water reflects and attenuates RF signals differently than land\n"
            "• Important for accurate modeling near lakes, rivers, and oceans\n"
            "• Can significantly affect propagation patterns in coastal areas",
        )
        self.edit_water_button.grid(row=0, column=1, padx=5, pady=5, in_=editing_buttons_grid)

        self.done_edit_button = self.make_button(
            "Done Edit",
            self.end_edit,
            "Exit editing mode and apply mask changes.\n\n"
            "WHEN TO USE:\n"
            "• After completing vegetation or water mask edits\n"
            "• To return to normal interaction mode\n\n"
            "NOTE: Your edits will be applied to the simulation when you run the next analysis.",
        )
        self.done_edit_button.grid(row=0, column=2, padx=5, pady=5, in_=editing_buttons_grid)

        self.undo_button = self.make_button(
            "Undo",
            self.undo_edit,
            "Undo the last mask editing action.\n\n"
            "LIMITATIONS:\n"
            "• Only available during editing mode\n"
            "• Only works for the most recent edit\n"
            "• Cannot undo after making new edits\n\n"
            "TIP: For complex edits, use undo frequently to correct mistakes as you go.",
        )
        self.undo_button.grid(row=0, column=3, padx=5, pady=5, in_=editing_buttons_grid)

        self.redo_button = self.make_button(
            "Redo",
            self.redo_edit,
            "Redo the last undone mask edit.\n\n"
            "WHEN TO USE:\n"
            "• After using the Undo button\n"
            "• When you want to restore an edit you previously undid\n\n"
            "NOTE: Redo history is cleared when you make a new edit.",
        )
        self.redo_button.grid(row=0, column=4, padx=5, pady=5, in_=editing_buttons_grid)

        # Create a frame for brush size in editing tab
        brush_frame = ttk.Frame(self.editing_controls_frame)
        brush_frame.pack(side=tk.TOP, pady=5, padx=5, fill="x")

        ttk.Label(brush_frame, text="Brush Size").pack(side=tk.LEFT, padx=5)
        self.brush_var = tk.IntVar(value=1)
        brush_scale = ttk.Scale(brush_frame, variable=self.brush_var, from_=1, to=20, orient=tk.HORIZONTAL, length=200)
        brush_scale.pack(side=tk.LEFT, padx=5)
        Tooltip(
            brush_scale,
            "Set the brush size used when painting vegetation or water masks. A "
            "larger brush speeds up broad edits while a small brush allows detail work."
        )

        # Physics tab
        self.physics_controls_frame = ttk.LabelFrame(self.physics_tab, text="Physics Simulation Options")
        self.physics_controls_frame.pack(pady=5, fill="x", padx=10)

        physics_grid = ttk.Frame(self.physics_controls_frame)
        physics_grid.pack(pady=5, padx=5)

        # Row 1: Basic physics options
        self.physics_var = tk.BooleanVar(value=False)
        physics_cb = ttk.Checkbutton(
            physics_grid,
            text="High Physics Simulation",
            variable=self.physics_var,
        )
        physics_cb.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        Tooltip(
            physics_cb,
            "Enable advanced propagation with refraction, interference, fresnel zones, and knife edge diffraction."
        )

        self.fresnel_var = tk.BooleanVar(value=True)
        fresnel_cb = ttk.Checkbutton(
            physics_grid,
            text="Fresnel Pulse",
            variable=self.fresnel_var,
        )
        fresnel_cb.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        Tooltip(
            fresnel_cb,
            "Animate a Fresnel zone pulse overlay during propagation replay."
        )

        self.signal_cones_var = tk.BooleanVar(value=False)
        cones_cb = ttk.Checkbutton(
            physics_grid,
            text="Show Signal Cones",
            variable=self.signal_cones_var,
            command=self._render_signal_cones,
        )
        cones_cb.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        Tooltip(cones_cb, "Render 3D directional cones for each transmitter.")

        # Row 2: Advanced physics options
        self.interference_var = tk.BooleanVar(value=False)
        inter_cb = ttk.Checkbutton(
            physics_grid,
            text="Multi-Tower Interference",
            variable=self.interference_var,
        )
        inter_cb.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        Tooltip(inter_cb, "Highlight constructive and destructive interference zones.")

        self.reflection_var = tk.BooleanVar(value=False)
        refl_cb = ttk.Checkbutton(
            physics_grid,
            text="Terrain Reflection",
            variable=self.reflection_var,
        )
        refl_cb.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        Tooltip(refl_cb, "Simulate simple signal reflections off terrain.")

        self.refraction_var = tk.BooleanVar(value=False)
        refr_cb = ttk.Checkbutton(
            physics_grid,
            text="Refraction",
            variable=self.refraction_var,
        )
        refr_cb.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        Tooltip(refr_cb, "Simulate signal bending through atmosphere.")

        # Row 3: More physics options
        self.deflection_var = tk.BooleanVar(value=False)
        defl_cb = ttk.Checkbutton(
            physics_grid,
            text="Deflection",
            variable=self.deflection_var,
        )
        defl_cb.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        Tooltip(defl_cb, "Simulate signal deflection around obstacles.")

        self.knife_edge_var = tk.BooleanVar(value=False)
        knife_cb = ttk.Checkbutton(
            physics_grid,
            text="Knife Edge",
            variable=self.knife_edge_var,
        )
        knife_cb.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        Tooltip(knife_cb, "Simulate knife edge diffraction over terrain.")

        self.fresnel_zones_var = tk.BooleanVar(value=False)
        fresnel_zones_cb = ttk.Checkbutton(
            physics_grid,
            text="Fresnel Zones",
            variable=self.fresnel_zones_var,
        )
        fresnel_zones_cb.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        Tooltip(fresnel_zones_cb, "Consider Fresnel zones in propagation calculations.")

        # Weather frame in physics tab
        if WeatherGUI is not None:
            self.weather_frame = ttk.LabelFrame(self.physics_tab, text="Weather Effects")
            self.weather_frame.pack(pady=5, fill="x", padx=10)
            self.weather_gui = WeatherGUI(self.weather_frame)
        else:
            self.weather_gui = None

        # Advanced tab
        self.advanced_controls_frame = ttk.LabelFrame(self.advanced_tab, text="Advanced Visualization")
        self.advanced_controls_frame.pack(pady=5, fill="x", padx=10)

        advanced_grid = ttk.Frame(self.advanced_controls_frame)
        advanced_grid.pack(pady=5, padx=5)

        # Row 1: View modes
        ttk.Label(advanced_grid, text="View Mode:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.view_mode_selector = ttk.Combobox(
            advanced_grid,
            values=[
                "Standard View",
                "Void Mapping Mode",
                "LoS Diagnostic Mode",
            ],
            state="readonly",
            width=18,
        )
        self.view_mode_selector.set("Standard View")
        self.view_mode_selector.bind(
            "<<ComboboxSelected>>", lambda _e: self._on_mode_change(self.view_mode_selector.get())
        )
        self.view_mode_selector.grid(row=0, column=1, padx=5, pady=5)
        Tooltip(
            self.view_mode_selector,
            "Select display mode: Standard shows the normal overlay, Void Mapping"
            " focuses on weak zones, and LoS Diagnostics highlights lines of sight",
        )

        ttk.Label(advanced_grid, text="Display Mode:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.view_mode = ttk.Combobox(
            advanced_grid,
            values=["Normal", "Side-by-Side", "Swipe"],
            state="readonly",
            width=12,
        )
        self.view_mode.set("Normal")
        self.view_mode.bind("<<ComboboxSelected>>", self._apply_view_mode)
        self.view_mode.grid(row=0, column=3, padx=5, pady=5)
        Tooltip(
            self.view_mode,
            "Choose how overlays are displayed: a single normal view, a side-by-side comparison, or a future swipe mode."
        )

        # Row 2: Overlay options
        ttk.Label(advanced_grid, text="Overlay Type:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.overlay_type_var = tk.StringVar(value="danger")
        overlay_menu = ttk.OptionMenu(
            advanced_grid,
            self.overlay_type_var,
            "danger",
            "propagation",
            "wavefront",
            "sphere",
            "flood",
            "global",
        )
        overlay_menu.grid(row=1, column=1, padx=5, pady=5)
        Tooltip(
            overlay_menu,
            "Select the type of overlay displayed on the image such as danger "
            "zones or propagation intensity."
        )

        ttk.Label(advanced_grid, text="Overlay Selection:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.overlay_select_var = tk.StringVar(value="Heatmap")
        overlay_menu = ttk.OptionMenu(
            advanced_grid,
            self.overlay_select_var,
            "Heatmap",
            "LOS Zones",
            "Interference",
            "Reflections",
            command=self._apply_overlay_selection,
        )
        overlay_menu.grid(row=1, column=3, padx=5, pady=5)

        # Row 3: Display options
        self.show_overlay_var = tk.BooleanVar(value=True)
        overlay_cb = ttk.Checkbutton(
            advanced_grid,
            text="Show Heatmap Overlay",
            variable=self.show_overlay_var,
            command=self._render_hybrid_view,
        )
        overlay_cb.grid(row=2, column=0, padx=5, pady=5, sticky="w", columnspan=2)
        Tooltip(
            overlay_cb,
            "Toggle the RF heatmap layer when viewing the voxel-based terrain rendering so you can focus on geometry alone if needed.",
        )
        self.heatmap_toggle = overlay_cb

        self.voxel_toggle_var = tk.BooleanVar(value=True)
        self.voxel_toggle = ttk.Checkbutton(
            advanced_grid,
            text="Voxel Base",
            variable=self.voxel_toggle_var,
            command=self._render_hybrid_view,
        )
        self.voxel_toggle.grid(row=2, column=2, padx=5, pady=5, sticky="w", columnspan=2)
        Tooltip(
            self.voxel_toggle,
            "Display the voxelized terrain collapsed into a 2D image beneath the DEM. Disable if you only want the raw terrain view.",
        )

        # Row 4: More display options
        self.show_legend_var = tk.BooleanVar(value=True)
        legend_cb = ttk.Checkbutton(
            advanced_grid,
            text="Show Legend",
            variable=self.show_legend_var,
            command=self._toggle_legend,
        )
        legend_cb.grid(row=3, column=0, padx=5, pady=5, sticky="w", columnspan=2)
        Tooltip(legend_cb, "Toggle display of the color scale legend beside the overlay.")

        self.vector_var = tk.IntVar(value=0)
        vector_cb = ttk.Checkbutton(
            advanced_grid,
            text="Show Vectors",
            variable=self.vector_var,
            command=self.refresh,
        )
        vector_cb.grid(row=3, column=2, padx=5, pady=5, sticky="w", columnspan=2)
        Tooltip(
            vector_cb,
            "Toggle display of signal contour vectors on the overlay.\n\n"
            "WHAT IT SHOWS:\n"
            "• Signal strength boundary lines at different thresholds\n"
            "• Coverage area outlines for each signal strength level\n\n"
            "WHEN TO ENABLE:\n"
            "• When you need to see precise coverage boundaries\n"
            "• For identifying signal strength transition areas\n"
            "• When preparing data for export to vector formats"
        )

        # Row 5: Theme options
        self.theme_var = tk.BooleanVar(value=True)
        self.theme_toggle = ttk.Checkbutton(
            advanced_grid,
            text="Dark Mode",
            variable=self.theme_var,
            command=lambda: self._apply_theme(self.theme_var.get()),
        )
        self.theme_toggle.grid(row=4, column=0, padx=5, pady=5, sticky="w", columnspan=2)
        Tooltip(
            self.theme_toggle,
            "Toggle between light and dark application themes. Dark mode can reduce eye strain and helps when working in dim environments.",
        )

        contrast_cb = ttk.Checkbutton(
            advanced_grid,
            text="High Contrast",
            command=self._toggle_contrast,
        )
        contrast_cb.grid(row=4, column=2, padx=5, pady=5, sticky="w", columnspan=2)
        Tooltip(
            contrast_cb,
            "Switch to a high contrast theme to improve visibility for low-vision users."
        )

        # Row 6: Passive mode and debug
        self.passive_var = tk.BooleanVar(value=False)
        self.passive_toggle = ttk.Checkbutton(
            advanced_grid,
            text="Passive Mode",
            variable=self.passive_var,
            command=lambda: self._toggle_passive_mode(self.passive_var.get()),
        )
        self.passive_toggle.grid(row=5, column=0, padx=5, pady=5, sticky="w", columnspan=2)
        Tooltip(
            self.passive_toggle,
            "When idle, the system performs background analysis and monitoring.",
        )

        self.debug_var = tk.BooleanVar(value=False)
        debug_cb = ttk.Checkbutton(
            advanced_grid,
            text="Dev Overlay",
            variable=self.debug_var,
            command=lambda: self.dev_overlay.place(x=10, y=10)
            if self.debug_var.get()
            else self.dev_overlay.place_forget(),
        )
        debug_cb.grid(row=5, column=2, padx=5, pady=5, sticky="w", columnspan=2)
        Tooltip(
            debug_cb,
            "Toggle live developer overlay showing frame count, memory use, layer info.\n"
            "Useful for performance debugging and visual inspection.\nCan be enabled at runtime."
        )

        # Voxel parameters in advanced tab
        self.voxel_params_frame = ttk.LabelFrame(self.advanced_tab, text="Voxel Parameters")
        self.voxel_params_frame.pack(pady=5, fill="x", padx=10)

        voxel_params_grid = ttk.Frame(self.voxel_params_frame)
        voxel_params_grid.pack(pady=5, padx=5)

        # Row 1: Voxel resolution
        ttk.Label(voxel_params_grid, text="Voxel Resolution").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.voxel_res_scale = ttk.Scale(
            voxel_params_grid,
            from_=25,
            to=100,
            orient=tk.HORIZONTAL,
            length=200,
            command=lambda _v: self._update_voxel_params(),
        )
        self.voxel_res_scale.set(75)  # Default to 75% (equivalent to old default of 2)
        self.voxel_res_scale.grid(row=0, column=1, padx=5, pady=5)
        Tooltip(
            self.voxel_res_scale, 
            "Controls the resolution of the 3D voxel terrain model.\n"
            "Higher values (100%) provide more detail but require more processing power.\n"
            "Lower values (25%) are faster but less detailed."
        )

        # Row 2: Depth perception
        ttk.Label(voxel_params_grid, text="Depth Perception").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.depth_perception_scale = ttk.Scale(
            voxel_params_grid,
            from_=25,
            to=100,
            orient=tk.HORIZONTAL,
            length=200,
            command=lambda _v: self._update_voxel_params(),
        )
        self.depth_perception_scale.set(100)  # Default to 100%
        self.depth_perception_scale.grid(row=1, column=1, padx=5, pady=5)
        Tooltip(
            self.depth_perception_scale, 
            "Controls the strength of the physics-based depth perception mechanics.\n"
            "Higher values (100%) provide more pronounced depth effects.\n"
            "Lower values (25%) create more subtle depth perception."
        )

        # Row 3: Inference intensity
        ttk.Label(voxel_params_grid, text="Inference Intensity").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.inference_intensity_scale = ttk.Scale(
            voxel_params_grid,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            length=200,
            command=lambda _v: self._update_voxel_params(),
        )
        self.inference_intensity_scale.set(5)
        self.inference_intensity_scale.grid(row=2, column=1, padx=5, pady=5)

        # Row 4: Alpha slider
        ttk.Label(voxel_params_grid, text="Overlay Alpha").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.alpha_var = tk.DoubleVar(value=0.5)
        alpha_scale = ttk.Scale(
            voxel_params_grid,
            variable=self.alpha_var,
            from_=0,
            to=1,
            orient=tk.HORIZONTAL,
            length=200,
        )
        alpha_scale.grid(row=3, column=1, padx=5, pady=5)
        Tooltip(
            alpha_scale,
            "Adjust how transparent the overlay image appears so base imagery "
            "remains visible underneath."
        )

        # Slice controls in advanced tab
        self.slice_controls_frame = ttk.LabelFrame(self.advanced_tab, text="Slice Controls")
        self.slice_controls_frame.pack(pady=5, fill="x", padx=10)

        slice_controls_grid = ttk.Frame(self.slice_controls_frame)
        slice_controls_grid.pack(pady=5, padx=5)

        self.slice_label = ttk.Label(slice_controls_grid, text="Layer: 0")
        self.slice_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.slice_slider = ttk.Scale(
            slice_controls_grid,
            from_=0,
            to=15,
            orient=tk.HORIZONTAL,
            length=200,
            command=lambda _v: self._render_voxel_slice(),
        )
        self.slice_slider.grid(row=0, column=1, padx=5, pady=5)

        self.play_button = ttk.Button(
            slice_controls_grid,
            text="▶️ Play",
            command=self._start_slice_animation,
        )
        self.play_button.grid(row=0, column=2, padx=5, pady=5)

        self.stop_button = ttk.Button(
            slice_controls_grid,
            text="⏹️ Stop",
            command=self._stop_slice_animation,
        )
        self.stop_button.grid(row=0, column=3, padx=5, pady=5)

        # Display mode radio buttons in advanced tab
        self.display_mode_frame = ttk.LabelFrame(self.advanced_tab, text="Display Mode")
        self.display_mode_frame.pack(pady=5, fill="x", padx=10)

        display_mode_grid = ttk.Frame(self.display_mode_frame)
        display_mode_grid.pack(pady=5, padx=5)

        self.mode_var = tk.StringVar(value="overlay")
        row, col = 0, 0
        for m in ("base", "overlay", "composite", "veg", "water", "confidence", "diff", "dead"):
            rb = ttk.Radiobutton(
                display_mode_grid, text=m.title(), variable=self.mode_var, value=m, command=self.refresh
            )
            rb.grid(row=row, column=col, padx=5, pady=5, sticky="w")
            Tooltip(rb, f"Display mode: {m}")
            col += 1
            if col > 3:  # 4 columns per row
                col = 0
                row += 1

        self.vector_var = tk.IntVar(value=0)
        cb = ttk.Checkbutton(
            self.button_frame,
            text="Show Vectors",
            variable=self.vector_var,
            command=self.refresh,
        )
        cb.tooltip_text = (
            "Toggle display of signal contour vectors on the overlay.\n\n"
            "WHAT IT SHOWS:\n"
            "• Signal strength boundary lines at different thresholds\n"
            "• Coverage area outlines for each signal strength level\n\n"
            "WHEN TO ENABLE:\n"
            "• When you need to see precise coverage boundaries\n"
            "• For identifying signal strength transition areas\n"
            "• When preparing data for export to vector formats"
        )
        col = len(self.button_frame.grid_slaves())
        cb.grid(row=0, column=col, padx=2)

        entry_frame = tk.Frame(root)
        entry_frame.pack(pady=5)
        self.tx_panel = TXControlPanel(entry_frame)
        self.freq_var = self.tx_panel.tx_freq_var
        self.power_var = self.tx_panel.tx_power_var
        self.height_var = self.tx_panel.tx_height_var
        tk.Label(entry_frame, text="Model").pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value="FSPL")
        model_menu = tk.OptionMenu(
            entry_frame, self.model_var, "FSPL", "Longwave", "Shortwave", "Cellular", "Satcom"
        )
        model_menu.pack(side=tk.LEFT, padx=5)
        Tooltip(
            model_menu,
            "Select the RF propagation model for analysis.\n\n"
            "MODEL OPTIONS:\n"
            "• FSPL (Free Space Path Loss): Basic line-of-sight model, ideal for open areas\n"
            "• Longwave: Best for low frequencies (<30 MHz), accounts for ground wave propagation\n"
            "• Shortwave: Optimized for 3-30 MHz, includes ionospheric reflection\n"
            "• Cellular: Designed for mobile communications (700-2600 MHz), includes urban effects\n"
            "• Satcom: For satellite communications, accounts for atmospheric effects\n\n"
            "TIP: Choose the model that best matches your frequency band and environment."
        )
        tk.Label(entry_frame, text="Param").pack(side=tk.LEFT)
        self.param_var = tk.StringVar()
        param_entry = tk.Entry(entry_frame, width=6, textvariable=self.param_var)
        param_entry.pack(side=tk.LEFT, padx=5)
        Tooltip(
            param_entry,
            "Enter an optional model parameter for advanced configuration.\n\n"
            "PARAMETER USAGE BY MODEL:\n"
            "• FSPL: Atmospheric attenuation factor (default: 0)\n"
            "• Longwave: Ground conductivity (0.001-0.03, default: 0.005)\n"
            "• Shortwave: Ionospheric reflection efficiency (0-1, default: 0.7)\n"
            "• Cellular: Urban density factor (1-5, default: 3)\n"
            "• Satcom: Atmospheric moisture (0-100%, default: 50)\n\n"
            "Leave blank to use default values."
        )

        if WeatherGUI is not None:
            self.weather_gui = WeatherGUI(entry_frame)
        else:
            self.weather_gui = None

        tk.Label(entry_frame, text="DEM Source").pack(side=tk.LEFT)
        self.dem_source_var = tk.StringVar(value="Fused")
        dem_menu = tk.OptionMenu(entry_frame, self.dem_source_var, "Fused", "MiDaS", "Physics")
        dem_menu.pack(side=tk.LEFT, padx=5)
        Tooltip(
            dem_menu,
            "Choose which Digital Elevation Model source to use for analysis. "
            "Options depend on what data you have loaded."
        )

        self.overlay_type_var = tk.StringVar(value="danger")
        overlay_menu = tk.OptionMenu(
            entry_frame,
            self.overlay_type_var,
            "danger",
            "propagation",
            "wavefront",
            "sphere",
            "flood",
            "global",
        )
        overlay_menu.pack(side=tk.LEFT, padx=5)
        Tooltip(
            overlay_menu,
            "Select the type of overlay displayed on the image such as danger "
            "zones or propagation intensity."
        )

        self.alpha_var = tk.DoubleVar(value=0.5)
        tk.Label(entry_frame, text="Overlay Alpha").pack(side=tk.LEFT)
        alpha_scale = tk.Scale(
            entry_frame,
            variable=self.alpha_var,
            from_=0,
            to=1,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            length=100,
        )
        alpha_scale.pack(side=tk.LEFT)
        Tooltip(
            alpha_scale,
            "Adjust how transparent the overlay image appears so base imagery "
            "remains visible underneath."
        )

        tk.Label(entry_frame, text="Brush Size").pack(side=tk.LEFT)
        self.brush_var = tk.IntVar(value=1)
        brush_scale = tk.Scale(entry_frame, variable=self.brush_var, from_=1, to=20, orient=tk.HORIZONTAL, length=80)
        brush_scale.pack(side=tk.LEFT)
        Tooltip(
            brush_scale,
            "Set the brush size used when painting vegetation or water masks. A "
            "larger brush speeds up broad edits while a small brush allows detail work."
        )

        self.mode_var = tk.StringVar(value="overlay")
        for m in ("base", "overlay", "composite", "veg", "water", "confidence", "diff", "dead"):
            rb = tk.Radiobutton(
                entry_frame, text=m.title(), variable=self.mode_var, value=m, command=self.refresh
            )
            rb.pack(side=tk.LEFT, padx=2)
            Tooltip(rb, f"Display mode: {m}")

        self.debug_var = tk.BooleanVar(value=False)
        debug_cb = tk.Checkbutton(
            entry_frame,
            text="Dev Overlay",
            variable=self.debug_var,
            command=lambda: self.dev_overlay.place(x=10, y=10)
            if self.debug_var.get()
            else self.dev_overlay.place_forget(),
        )
        debug_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(
            debug_cb,
            "Toggle live developer overlay showing frame count, memory use, layer info.\n"
            "Useful for performance debugging and visual inspection.\nCan be enabled at runtime."
        )

        self.view_mode_selector = ttk.Combobox(
            entry_frame,
            values=[
                "Standard View",
                "Void Mapping Mode",
                "LoS Diagnostic Mode",
            ],
            state="readonly",
            width=18,
        )
        self.view_mode_selector.set("Standard View")
        self.view_mode_selector.bind(
            "<<ComboboxSelected>>", lambda _e: self._on_mode_change(self.view_mode_selector.get())
        )
        self.view_mode_selector.pack(side=tk.LEFT, padx=5)
        Tooltip(
            self.view_mode_selector,
            "Select display mode: Standard shows the normal overlay, Void Mapping"
            " focuses on weak zones, and LoS Diagnostics highlights lines of sight",
        )

        self.use_high_contrast = False
        contrast_cb = tk.Checkbutton(
            entry_frame,
            text="High Contrast",
            command=self._toggle_contrast,
        )
        contrast_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(
            contrast_cb,
            "Switch to a high contrast theme to improve visibility for low-vision users."
        )

        self.theme_var = tk.BooleanVar(value=True)
        self.theme_toggle = tk.Checkbutton(
            entry_frame,
            text="Dark Mode",
            variable=self.theme_var,
            command=lambda: self._apply_theme(self.theme_var.get()),
        )
        self.theme_toggle.pack(side=tk.LEFT, padx=5)
        Tooltip(
            self.theme_toggle,
            "Toggle between light and dark application themes. Dark mode can reduce eye strain and helps when working in dim environments.",
        )
        self._apply_theme(self.theme_var.get())

        self.view_mode = ttk.Combobox(
            entry_frame,
            values=["Normal", "Side-by-Side", "Swipe"],
            state="readonly",
            width=12,
        )
        self.view_mode.set("Normal")
        self.view_mode.bind("<<ComboboxSelected>>", self._apply_view_mode)
        self.view_mode.pack(side=tk.LEFT, padx=5)
        Tooltip(
            self.view_mode,
            "Choose how overlays are displayed: a single normal view, a side-by-side comparison, or a future swipe mode."
        )

        self.show_legend_var = tk.BooleanVar(value=True)
        legend_cb = tk.Checkbutton(
            entry_frame,
            text="Show Legend",
            variable=self.show_legend_var,
            command=self._toggle_legend,
        )
        legend_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(legend_cb, "Toggle display of the color scale legend beside the overlay.")

        self.voxel_toggle_var = tk.BooleanVar(value=True)
        self.voxel_toggle = tk.Checkbutton(
            entry_frame,
            text="Voxel Base",
            variable=self.voxel_toggle_var,
            command=self._render_hybrid_view,
        )
        self.voxel_toggle.pack(side=tk.LEFT, padx=5)
        Tooltip(
            self.voxel_toggle,
            "Display the voxelized terrain collapsed into a 2D image beneath the DEM. Disable if you only want the raw terrain view.",
        )

        self.show_overlay_var = tk.BooleanVar(value=True)
        overlay_cb = tk.Checkbutton(
            entry_frame,
            text="Show Heatmap Overlay",
            variable=self.show_overlay_var,
            command=self._render_hybrid_view,
        )
        overlay_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(
            overlay_cb,
            "Toggle the RF heatmap layer when viewing the voxel-based terrain rendering so you can focus on geometry alone if needed.",
        )
        self.heatmap_toggle = overlay_cb
        if IS_LITE:
            self.heatmap_toggle.config(state=tk.DISABLED)
            self._set_status("Running in Lite Mode – Advanced overlays disabled.")

        tk.Label(entry_frame, text="Overlay").pack(side=tk.LEFT)
        self.overlay_select_var = tk.StringVar(value="Heatmap")
        overlay_menu = tk.OptionMenu(
            entry_frame,
            self.overlay_select_var,
            "Heatmap",
            "LOS Zones",
            "Interference",
            "Reflections",
            command=self._apply_overlay_selection,
        )
        overlay_menu.pack(side=tk.LEFT, padx=5)

        self.passive_var = tk.BooleanVar(value=False)
        self.passive_toggle = tk.Checkbutton(
            entry_frame,
            text="Passive Mode",
            variable=self.passive_var,
            command=lambda: self._toggle_passive_mode(self.passive_var.get()),
        )
        self.passive_toggle.pack(side=tk.LEFT, padx=5)
        Tooltip(
            self.passive_toggle,
            "When idle, the system performs background analysis and monitoring.",
        )

        self.fresnel_var = tk.BooleanVar(value=True)
        fresnel_cb = tk.Checkbutton(
            entry_frame,
            text="Fresnel Pulse",
            variable=self.fresnel_var,
        )
        fresnel_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(
            fresnel_cb,
            "Animate a Fresnel zone pulse overlay during propagation replay.",
        )

        self.physics_var = tk.BooleanVar(value=False)
        physics_cb = tk.Checkbutton(
            entry_frame,
            text="High Physics Simulation",
            variable=self.physics_var,
        )
        physics_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(
            physics_cb,
            "Enable advanced propagation with refraction, interference, fresnel zones, and knife edge diffraction.",
        )

        self.signal_cones_var = tk.BooleanVar(value=False)
        cones_cb = tk.Checkbutton(
            entry_frame,
            text="Show Signal Cones",
            variable=self.signal_cones_var,
            command=self._render_signal_cones,
        )
        cones_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(cones_cb, "Render 3D directional cones for each transmitter.")

        self.interference_var = tk.BooleanVar(value=False)
        inter_cb = tk.Checkbutton(
            entry_frame,
            text="Multi-Tower Interference",
            variable=self.interference_var,
        )
        inter_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(inter_cb, "Highlight constructive and destructive interference zones.")

        self.reflection_var = tk.BooleanVar(value=False)
        refl_cb = tk.Checkbutton(
            entry_frame,
            text="Terrain Reflection",
            variable=self.reflection_var,
        )
        refl_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(refl_cb, "Simulate simple signal reflections off terrain.")

        self.refraction_var = tk.BooleanVar(value=False)
        refr_cb = tk.Checkbutton(
            entry_frame,
            text="Refraction",
            variable=self.refraction_var,
        )
        refr_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(refr_cb, "Simulate signal bending through atmosphere.")

        self.deflection_var = tk.BooleanVar(value=False)
        defl_cb = tk.Checkbutton(
            entry_frame,
            text="Deflection",
            variable=self.deflection_var,
        )
        defl_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(defl_cb, "Simulate signal deflection around obstacles.")

        self.knife_edge_var = tk.BooleanVar(value=False)
        knife_cb = tk.Checkbutton(
            entry_frame,
            text="Knife Edge",
            variable=self.knife_edge_var,
        )
        knife_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(knife_cb, "Simulate knife edge diffraction over terrain.")

        self.fresnel_zones_var = tk.BooleanVar(value=False)
        fresnel_zones_cb = tk.Checkbutton(
            entry_frame,
            text="Fresnel Zones",
            variable=self.fresnel_zones_var,
        )
        fresnel_zones_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(fresnel_zones_cb, "Consider Fresnel zones in propagation calculations.")

        # Add interference pattern toggle
        self.interference_pattern_var = tk.BooleanVar(value=False)
        interference_pattern_cb = tk.Checkbutton(
            entry_frame,
            text="Show Interference Pattern",
            variable=self.interference_pattern_var,
        )
        interference_pattern_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(interference_pattern_cb, "Show constructive/destructive interference patterns between multiple transmitters.")

        self.heatmap_centering_var = tk.BooleanVar(value=False)
        center_cb = tk.Checkbutton(
            entry_frame,
            text="Center on Dead Zones",
            variable=self.heatmap_centering_var,
        )
        center_cb.pack(side=tk.LEFT, padx=5)
        Tooltip(center_cb, "Adjust heatmap contrast based on dead zones.")

        # Create a frame for the voxel resolution scale with percentage values
        voxel_res_frame = tk.Frame(entry_frame)
        voxel_res_frame.pack(side=tk.LEFT, padx=5)

        tk.Label(voxel_res_frame, text="Voxel Resolution").pack(anchor=tk.W)

        # Use a scale with percentage values (25%, 50%, 75%, 100%)
        self.voxel_res_scale = tk.Scale(
            voxel_res_frame,
            from_=25,
            to=100,
            orient=tk.HORIZONTAL,
            resolution=25,
            command=lambda _v: self._update_voxel_params(),
        )
        self.voxel_res_scale.set(75)  # Default to 75% (equivalent to old default of 2)
        self.voxel_res_scale.pack(side=tk.TOP)

        # Add a tooltip explaining what the voxel resolution does
        Tooltip(
            voxel_res_frame, 
            "Controls the resolution of the 3D voxel terrain model.\n"
            "Higher values (100%) provide more detail but require more processing power.\n"
            "Lower values (25%) are faster but less detailed."
        )

        # Create a frame for the depth perception strength scale with percentage values
        depth_perception_frame = tk.Frame(entry_frame)
        depth_perception_frame.pack(side=tk.LEFT, padx=5)

        tk.Label(depth_perception_frame, text="Depth Perception").pack(anchor=tk.W)

        # Use a scale with percentage values (25%, 50%, 75%, 100%)
        self.depth_perception_scale = tk.Scale(
            depth_perception_frame,
            from_=25,
            to=100,
            orient=tk.HORIZONTAL,
            resolution=25,
            command=lambda _v: self._update_voxel_params(),
        )
        self.depth_perception_scale.set(100)  # Default to 100%
        self.depth_perception_scale.pack(side=tk.TOP)

        # Add a tooltip explaining what the depth perception strength does
        Tooltip(
            depth_perception_frame, 
            "Controls the strength of the physics-based depth perception mechanics.\n"
            "Higher values (100%) provide more pronounced depth effects.\n"
            "Lower values (25%) create more subtle depth perception."
        )

        self.inference_intensity_scale = tk.Scale(
            entry_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            label="Inference Intensity",
            command=lambda _v: self._update_voxel_params(),
        )
        self.inference_intensity_scale.set(5)
        self.inference_intensity_scale.pack(side=tk.LEFT, padx=5)

        self.slice_label = tk.Label(entry_frame, text="Layer: 0")
        self.slice_label.pack(side=tk.LEFT, padx=5)

        self.slice_slider = tk.Scale(
            entry_frame,
            from_=0,
            to=15,
            orient=tk.HORIZONTAL,
            command=lambda _v: self._render_voxel_slice(),
        )
        self.slice_slider.pack(side=tk.LEFT, padx=5)

        # These buttons are now created in the slice_controls_frame in the advanced tab

        # Create a main display area with a modern, scientific look
        self.use_canvas = True
        self.display_frame = ttk.Frame(root)
        self.display_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Create a frame for the canvas with a border to make it look more professional
        self.canvas_container = ttk.Frame(self.display_frame, relief=tk.GROOVE, borderwidth=2)
        self.canvas_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if self.use_canvas:
            self.canvas = tk.Canvas(self.canvas_container, highlightthickness=0, bg="#f8f8f8")
        else:
            self.canvas = tk.Label(self.canvas_container)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Create a more scientific-looking legend with a title and border
        self.legend_frame = ttk.LabelFrame(self.display_frame, text="Signal Analysis")
        self.legend_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        ttk.Label(self.legend_frame, text="Signal Loss (dB)", font=("Segoe UI", 9, "bold")).pack(pady=(5,0))
        self.legend_image_label = ttk.Label(self.legend_frame)
        self.legend_image_label.pack(pady=5, padx=5)

        # Add a small info panel below the legend
        self.info_frame = ttk.LabelFrame(self.legend_frame, text="Analysis Info")
        self.info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.info_text = tk.Text(self.info_frame, height=6, width=20, font=("Consolas", 8), 
                                wrap=tk.WORD, bg="#f0f0f0", relief=tk.FLAT)
        self.info_text.pack(padx=5, pady=5)
        self.info_text.insert(tk.END, "Click on the map to place transmitters.\n\n"
                             "Use the Analysis tab to run propagation simulations.\n\n"
                             "View results in different visualization modes.")
        self.info_text.config(state=tk.DISABLED)

        # Bind canvas events
        self.canvas.bind("<Button-1>", self.set_tx)
        self.canvas.bind("<B1-Motion>", self.paint_mask)
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Leave>", lambda _e: self._remove_crosshair())
        self._toggle_legend()

        # Split canvas for comparison views
        self.split_canvas = SplitOverlayCanvas(root)
        self.split_canvas.pack_forget()

        # Status bar with a more modern look
        self.status_frame = ttk.Frame(root, relief=tk.GROOVE, borderwidth=1)
        self.status_frame.pack(fill="x", side=tk.BOTTOM, padx=5, pady=2)

        self.status = tk.StringVar(value="")
        self.loadbar = tk.StringVar(value="[--------------------------------------------------]")

        ttk.Label(self.status_frame, textvariable=self.loadbar, anchor="w").pack(fill="x", side=tk.BOTTOM, padx=5)
        ttk.Label(self.status_frame, textvariable=self.status, anchor="w").pack(fill="x", side=tk.BOTTOM, padx=5)

        self._init_help_panel()
        self._init_shortcut_hud()
        self._init_dev_overlay()
        self._init_diagnostic_overlay()
        self._init_context_menu()
        self._init_bug_report()
        self.install_tooltips()
        self._register_control_groups()
        self._set_controls_enabled("dem", False)
        self._set_controls_enabled("analysis", False)
        self._update_overlay_style()

        # keyboard shortcuts
        root.bind("<Control-o>", lambda e: self.open_image())
        root.bind("<Control-r>", lambda e: self.analyze())
        root.bind("<Control-e>", lambda e: self.export_loss())
        root.bind("<Control-l>", lambda e: self.show_slice())
        root.bind("<F1>", self._toggle_help)
        root.bind("<Control-h>", self._toggle_shortcuts)
        root.bind("<Control-1>", lambda e: (self.view_mode_selector.set("Standard View"), self._on_mode_change("Standard View")))
        root.bind("<Control-2>", lambda e: (self.view_mode_selector.set("Void Mapping Mode"), self._on_mode_change("Void Mapping Mode")))
        root.bind("<Control-3>", lambda e: (self.view_mode_selector.set("LoS Diagnostic Mode"), self._on_mode_change("LoS Diagnostic Mode")))
        root.bind("<Right>", lambda e: self.pan_canvas(10, 0))
        root.bind("<Left>", lambda e: self.pan_canvas(-10, 0))
        root.bind("<Up>", lambda e: self.pan_canvas(0, -10))
        root.bind("<Down>", lambda e: self.pan_canvas(0, 10))
        root.bind("<Tab>", lambda e: self._toggle_before_after())

    def hash_settings(self) -> str:
        if hasattr(self, "settings") and not hasattr(self, "model_var"):
            return hashlib.md5(str(sorted(self.settings.items())).encode()).hexdigest()
        weather_info = self.weather_gui.get_weather().__dict__ if self.weather_gui else {}
        return hashlib.md5(
            str(
                (
                    self.txs,
                    self.model_var.get(),
                    self.overlay_type_var.get(),
                    self.param_var.get(),
                    weather_info,
                )
            ).encode()
        ).hexdigest()

    @catch_errors
    def load_secondary(self) -> None:
        """Load a secondary image for DEM fusion."""
        file = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.tif;*.tiff")])
        if not file:
            return
        try:
            self.secondary_image = Image.open(file).convert("RGB")
            messagebox.showinfo("RF Analyzer", f"Loaded secondary image {file}")
        except Exception as exc:
            messagebox.showerror("RF Analyzer", f"Failed to load secondary: {exc}")

    @catch_errors
    def open_image(self) -> None:
        import logging  # Ensure logging is available in this method's scope
        file = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.tif;*.tiff")])
        if not file:
            return
        if not hasattr(self, "txs") and hasattr(self, "current_image"):
            from PIL import Image as pil_image

            img = pil_image.open(file)
            img = img.convert("RGB")
            self.image = img
            self.show_image(img)
            return
        logging.debug("Loading image %s", file)
        self.image_path = Path(file)
        rgb, dem, self.georef = load_input(self.image_path)
        self.image = Image.fromarray(rgb.astype("uint8"))
        self.original_shape = self.image.size
        self.disp_size = self.image.size
        if self.georef and hasattr(self.georef.get("transform"), "a"):
            self.calibration["scale"] = abs(self.georef["transform"].a)
        (
            self.water_mask,
            self.water_activity,
            self.veg_mask,
            self.veg_density,
            dem_corr,
            self.confidence_map,
        ) = discriminate_water_veg(rgb)
        self.midas_dem = None
        self.physics_dem = None
        if dem is not None:
            base_dem = dem.astype("float32")
        else:
            try:
                from sim_rf_map.terrain_fusion import fused_dem

                base_dem = fused_dem(self.image, self.secondary_image)
                if midas_depth is not None:
                    self.midas_dem = midas_depth(self.image)
                if self.secondary_image is not None and physics_depth is not None:
                    self.physics_dem = physics_depth(self.secondary_image)
            except Exception:
                sun = analyze_sun_shadow(rgb)[0]
                base_dem = build_dem_iterative(rgb, sun)
        base_dem = np.where(self.veg_mask > 0, dem_corr, base_dem)
        self.dem = np.where(self.veg_mask > 0, _smooth(base_dem), base_dem)
        if generate_voxel_volume is not None:
            self.voxel_volume = generate_voxel_volume(self.dem, self.voxel_config)
            self._update_slice_slider_range()
        logging.debug("DEM loaded with shape %s", self.dem.shape)
        self.txs.clear()
        self.current_tx = None
        cache_file(self.image_path, "uploads")
        self.overlay = None
        self._set_controls_enabled("dem", True)
        self._set_controls_enabled("analysis", False)
        self._set_status("DEM loaded. Ready for analysis.")
        if self.session_file.exists():
            try:
                data = json.load(open(self.session_file, "r", encoding="utf-8"))
                self.calibration.update(data.get("calibration", {}))
                self.txs = list(data.get("txs", []))
            except Exception:
                pass
        self.refresh()
        if self.voxel_toggle_var.get():
            self._render_hybrid_view()
        if self.txs:
            self._set_status("Image and TX loaded. Click Analyze to proceed.")

    def set_tx(self, event: tk.Event) -> None:
        if not hasattr(self, "image") and hasattr(self, "tx_points"):
            x = int(self.canvas.canvasx(event.x))
            y = int(self.canvas.canvasy(event.y))
            self.tx_points.append((x, y))
            marker = self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="red")
            if not hasattr(self, "tx_markers"):
                self.tx_markers = []
            self.tx_markers.append(marker)
            return
        if self.image is None:
            return
        coords = map_display_to_image(
            event.x,
            event.y,
            self.img_offset,
            getattr(self, "disp_size", self.image.size),
            self.image.size,
        )
        if coords is None:
            messagebox.showerror("RF Analyzer", "Click inside the image area")
            return
        x, y = coords
        if self.edit_mode:
            mask = self.veg_mask if self.edit_mode == "veg" else self.water_mask
            self.undo_stack.append(mask.copy())
            self.redo_stack.clear()
            r = self.brush_var.get() // 2
            y0 = max(y - r, 0)
            y1 = min(y + r + 1, img_h)
            x0 = max(x - r, 0)
            x1 = min(x + r + 1, img_w)
            mask[y0:y1, x0:x1] = 255
            self.refresh()
            return
        if self.overlay is not None and hasattr(event, "state") and event.state & 0x0001:
            val = float(self.data[y, x]) if hasattr(self, "data") else 0.0
            messagebox.showinfo("RF Analyzer", f"Danger at ({x}, {y}) = {val:.2f}")
            return
        self.current_tx = (y, x)
        try:
            tx_config = self.tx_panel.get_tx_config()
        except Exception:
            messagebox.showerror("RF Analyzer", "Invalid transmitter settings")
            return
        if self.dem is None:
            messagebox.showerror("RF Analyzer", "DEM not loaded")
            return
        z_voxel, y_vox, x_vox = self.tx_panel.get_full_tx_origin(self.dem, x, y)
        tx_entry = {
            "x": x_vox,
            "y": y_vox,
            "z": z_voxel,
            "frequency_mhz": tx_config["frequency_mhz"],
            "power_dbm": tx_config["power_dbm"],
        }
        self.txs.append(tx_entry)
        import logging  # Ensure logging is available in this method's scope
        logging.debug("Placed TX at %s", tx_entry)
        messagebox.showinfo(
            "RF Analyzer",
            f"Added TX ({x_vox}, {y_vox}, {z_voxel}) {tx_config['frequency_mhz']} MHz {tx_config['power_dbm']} dBm",
        )
        self.refresh()
        self.analyze()

    def remove_last_tx(self) -> None:
        """Remove the most recently placed transmitter."""
        if not hasattr(self, "txs") and hasattr(self, "tx_points"):
            if self.tx_points:
                self.tx_points.pop()
            if hasattr(self, "tx_markers") and self.tx_markers:
                self.canvas.delete(self.tx_markers.pop())
            return
        if not self.txs:
            return
        self.txs.pop()
        if self.txs:
            self.analyze()
        else:
            self.overlay = None
            self.data = None
        self.refresh()

    def paint_mask(self, event: tk.Event) -> None:
        if self.image is None or not self.edit_mode:
            return
        coords = map_display_to_image(
            event.x,
            event.y,
            self.img_offset,
            getattr(self, "disp_size", self.image.size),
            self.image.size,
        )
        if coords is None:
            return
        x, y = coords
        mask = self.veg_mask if self.edit_mode == "veg" else self.water_mask
        self.undo_stack.append(mask.copy())
        self.redo_stack.clear()
        r = self.brush_var.get() // 2
        y0 = max(y - r, 0)
        y1 = min(y + r + 1, img_h)
        x0 = max(x - r, 0)
        x1 = min(x + r + 1, img_w)
        mask[y0:y1, x0:x1] = 255
        self.refresh()

    def erase_mask(self, event: tk.Event) -> None:
        if self.image is None or not self.edit_mode:
            return
        coords = map_display_to_image(
            event.x,
            event.y,
            self.img_offset,
            getattr(self, "disp_size", self.image.size),
            self.image.size,
        )
        if coords is None:
            return
        x, y = coords
        mask = self.veg_mask if self.edit_mode == "veg" else self.water_mask
        self.undo_stack.append(mask.copy())
        self.redo_stack.clear()
        r = self.brush_var.get() // 2
        y0 = max(y - r, 0)
        y1 = min(y + r + 1, img_h)
        x0 = max(x - r, 0)
        x1 = min(x + r + 1, img_w)
        mask[y0:y1, x0:x1] = 0
        self.refresh()

    def on_hover(self, event: tk.Event) -> None:
        if self.data is None or self.image is None:
            return
        coords = map_display_to_image(
            event.x,
            event.y,
            self.img_offset,
            getattr(self, "disp_size", self.image.size),
            self.image.size,
        )
        if coords is None:
            self._remove_crosshair()
            return
        x, y = coords
        val = float(self.data[y, x])
        self.root.title(f"RF Analyzer – Danger at ({x},{y}) = {val:.2f} dB")
        self._draw_crosshair(event.x, event.y)

    def start_edit(self, mode: str) -> None:
        if self.image is None:
            return
        self.edit_mode = mode
        mask = self.veg_mask if mode == "veg" else self.water_mask
        if mask is not None:
            self.undo_stack.append(mask.copy())
            self.redo_stack.clear()
        messagebox.showinfo("RF Analyzer", f"Editing {mode} mask: left draw, right erase")

    def end_edit(self) -> None:
        self.edit_mode = None

    def undo_edit(self) -> None:
        if hasattr(self, "edit_history") and not hasattr(self, "edit_mode"):
            if self.edit_position > 0:
                self.edit_position -= 1
                self.load_secondary(self.edit_history[self.edit_position])
            return
        if not self.edit_mode or not self.undo_stack:
            return
        target = self.veg_mask if self.edit_mode == "veg" else self.water_mask
        self.redo_stack.append(target.copy())
        mask = self.undo_stack.pop()
        if self.edit_mode == "veg":
            self.veg_mask = mask
        else:
            self.water_mask = mask
        self.refresh()

    def redo_edit(self) -> None:
        if hasattr(self, "edit_history") and not hasattr(self, "edit_mode"):
            if self.edit_position < len(self.edit_history) - 1:
                self.edit_position += 1
                self.load_secondary(self.edit_history[self.edit_position])
            return
        if not self.edit_mode or not self.redo_stack:
            return
        target = self.veg_mask if self.edit_mode == "veg" else self.water_mask
        self.undo_stack.append(target.copy())
        mask = self.redo_stack.pop()
        if self.edit_mode == "veg":
            self.veg_mask = mask
        else:
            self.water_mask = mask
        self.refresh()

    def calibrate(self) -> None:
        scale = simpledialog.askfloat("DEM Scale", "Scale", initialvalue=self.calibration["scale"])
        offset = simpledialog.askfloat(
            "DEM Offset", "Offset", initialvalue=self.calibration["offset"]
        )
        if scale is not None and offset is not None:
            self.calibration = {"scale": scale, "offset": offset}

    @catch_errors
    def show_3d(self) -> None:
        if plt is None or self.image is None:
            messagebox.showwarning("RF Analyzer", "matplotlib required for 3D view")
            return
        dem = (
            self.dem
            if self.dem is not None
            else infer_dem_from_shading(np.array(self.image), self.calibration)
        )
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        X, Y = np.meshgrid(range(dem.shape[1]), range(dem.shape[0]))
        ax.plot_surface(X, Y, dem, cmap="terrain", linewidth=0, antialiased=False)
        plt.show()

    @catch_errors
    def show_voxels(self) -> None:
        if not hasattr(self, "image") and getattr(self, "dem", None) is not None:
            voxelizer = Voxelizer(getattr(self, "settings", {}))
            self.voxel_data = voxelizer.compute_voxels(self.dem, getattr(self, "tx_points", []))
            self.voxel_volume = self.voxel_data
            if hasattr(self, "slice_slider"):
                self.slice_slider.config(to=self.voxel_data.shape[0] - 1)
            return
        if plot_voxel_volume is None or self.image is None:
            messagebox.showwarning("RF Analyzer", "matplotlib required for voxel view")
            return
        dem = (
            self.dem
            if self.dem is not None
            else infer_dem_from_shading(np.array(self.image), self.calibration)
        )
        voxels = voxelize_dem(dem) if voxelize_dem is not None else None
        if voxels is None:
            messagebox.showwarning("RF Analyzer", "Voxelizer unavailable")
            return
        self.voxel_volume = voxels
        plot_voxel_volume(voxels)

    @catch_errors
    def _open_voxel_3d(self) -> None:
        if self.voxel_volume is None:
            messagebox.showwarning("RF Analyzer", "Run analysis first to generate voxels")
            return
        try:
            from sim_rf_map.ui.voxel_3d import Voxel3DViewer

            self.viewer = Voxel3DViewer(self.voxel_volume)
            self.gl_scene = self.viewer.view
            self._render_signal_cones()
            self.viewer.show()
        except Exception as exc:  # pragma: no cover - optional dependency
            messagebox.showerror("RF Analyzer", f"3D view failed: {exc}")

    @catch_errors
    def show_path_profile(self) -> None:
        if (
            plot_signal_profile is None
            or trace_signal_path is None
            or self.image is None
            or len(self.txs) < 2
        ):
            messagebox.showwarning("RF Analyzer", "Need matplotlib and at least two transmitters")
            return
        dem = (
            self.dem
            if self.dem is not None
            else infer_dem_from_shading(np.array(self.image), self.calibration)
        )
        origin = (self.txs[0]["y"], self.txs[0]["x"])
        target = (self.txs[-1]["y"], self.txs[-1]["x"])
        path = trace_signal_path(dem, origin, target)
        plot_signal_profile(path)

    # ----- Interactive Path Profiling -----
    def _start_path_selection(self) -> None:
        """Begin interactive path definition from TX to target."""
        if self.image is None or self.data is None:
            messagebox.showwarning("RF Analyzer", "Run analysis first")
            return
        self._set_status("Click a transmitter then a target point")
        self.canvas.bind("<Button-1>", self._capture_tx_point)

    def _capture_tx_point(self, event: tk.Event) -> None:
        coords = map_display_to_image(
            event.x,
            event.y,
            self.img_offset,
            self.disp_size,
            self.image.size,
        )
        if coords is None:
            return
        self.tx_point = coords
        self._set_status("TX selected. Click target point")
        self.canvas.bind("<Button-1>", self._capture_target_point)

    def _capture_target_point(self, event: tk.Event) -> None:
        coords = map_display_to_image(
            event.x,
            event.y,
            self.img_offset,
            self.disp_size,
            self.image.size,
        )
        if coords is None:
            self.canvas.bind("<Button-1>", self.set_tx)
            return
        self.canvas.bind("<Button-1>", self.set_tx)
        self._compute_path_profile(self.tx_point, coords)

    def _compute_path_profile(self, tx_xy: tuple[int, int], target_xy: tuple[int, int]) -> None:
        """Plot terrain elevation and signal loss along straight path."""
        if callable(trace_signal_path) and callable(plot_signal_profile):
            path = trace_signal_path(self.dem, tx_xy, target_xy)
            plot_signal_profile(path, tx_height=getattr(self, "settings", {}).get("tx_height", 0))
            return
        if plt is None:
            messagebox.showwarning("RF Analyzer", "matplotlib required")
            return
        from scipy.interpolate import interpn

        steps = 200
        x = np.linspace(tx_xy[0], target_xy[0], steps)
        y = np.linspace(tx_xy[1], target_xy[1], steps)

        dem = self.dem if self.dem is not None else infer_dem_from_shading(np.array(self.image), self.calibration)
        loss = self.data if self.data is not None else np.zeros_like(dem)

        points = (np.arange(dem.shape[0]), np.arange(dem.shape[1]))
        sample_coords = np.vstack((y, x)).T
        elev = interpn(points, dem, sample_coords, method="linear", bounds_error=False, fill_value=np.nan)
        sig_loss = interpn(points, loss, sample_coords, method="linear", bounds_error=False, fill_value=np.nan)

        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax1.plot(elev, color="saddlebrown", label="Elevation")
        ax2.plot(sig_loss, color="red", label="Loss")
        ax1.set_xlabel("Distance along path")
        ax1.set_ylabel("Elevation (m)", color="saddlebrown")
        ax2.set_ylabel("Loss (dB)", color="red")
        ax1.set_title("Path Profile")
        plt.tight_layout()
        plt.show()

    @catch_errors
    def analyze(self) -> None:
        import logging  # Ensure logging is available in this method's scope
        if not hasattr(self, "image") and getattr(self, "dem", None) is not None:
            propagator = get_propagator(getattr(self, "settings", {}))
            self.overlay_data = propagator.compute_coverage(
                self.dem,
                getattr(self, "tx_points", []),
                getattr(self, "settings", {}),
            )
            if hasattr(self, "status_label"):
                self.status_label.config(text="Analysis complete")
            self.refresh()
            return
        if self.image is None:
            messagebox.showwarning("RF Analyzer", "Please open an image first.")
            return
        if not self.txs and self.overlay_type_var.get() not in {"flood", "global"}:
            messagebox.showwarning(
                "RF Analyzer",
                "Add at least one transmitter by clicking on the image, or switch to Flood/Global mode.",
            )
            return
        new_hash = self.hash_settings()
        if new_hash == self.last_hash and self.overlay is not None:
            self.refresh()
            return
        self.last_hash = new_hash
        logging.debug("Starting analysis with %d TX", len(self.txs))
        self._update_loadbar(0.0)
        start_time = time.time()
        with self.busy_feedback("Analyzing RF volume..."):
            rgb = np.array(self.image).astype("float32")
            dem_choice = self.dem_source_var.get()
            if dem_choice == "MiDaS" and self.midas_dem is not None:
                dem = self.midas_dem
            elif dem_choice == "Physics" and self.physics_dem is not None:
                dem = self.physics_dem
            else:
                dem = (
                    self.dem if self.dem is not None else infer_dem_from_shading(rgb, self.calibration)
                )
            dem = apply_refraction(dem)
            veg = (
                self.veg_density
                if self.veg_density is not None
                else self.veg_mask if self.veg_mask is not None else rgb[:, :, 1]
            )
            water = self.water_mask if self.water_mask is not None else rgb[:, :, 2]
            if dem.shape[0] > 800:
                dem = dem[::2, ::2]
                veg = veg[::2, ::2]
                water = water[::2, ::2]
            hazard = compute_hazard(dem)
            veg_loss = vegetation_loss(dem, veg)
            water_l = water_loss(water, self.water_activity)
            total_loss = np.zeros_like(dem, dtype="float32")
            if self._is_high_physics_enabled() and simulate_high_physics_rf is not None:
                # Create RF behavior options with physics effect flags set based on toggle states
                from sim_rf_map.physics.rf_behavior import RFBehaviorOptions
                options = RFBehaviorOptions()
                options.physics_effects["enable_refraction"] = getattr(self, "refraction_var", tk.BooleanVar(value=False)).get()
                options.physics_effects["enable_deflection"] = getattr(self, "deflection_var", tk.BooleanVar(value=False)).get()
                options.physics_effects["enable_reflection"] = getattr(self, "reflection_var", tk.BooleanVar(value=False)).get()
                options.physics_effects["enable_knife_edge"] = getattr(self, "knife_edge_var", tk.BooleanVar(value=False)).get()
                options.physics_effects["enable_fresnel_zones"] = getattr(self, "fresnel_zones_var", tk.BooleanVar(value=False)).get()
                options.physics_effects["enable_interference"] = getattr(self, "interference_var", tk.BooleanVar(value=False)).get()
                options.physics_effects["show_interference_pattern"] = getattr(self, "interference_pattern_var", tk.BooleanVar(value=False)).get()

                self.data = simulate_high_physics_rf(dem, self.txs, options)
            elif simulate_basic_rf is not None:
                self.data = simulate_basic_rf(dem, self.txs)
                self.data = self._maybe_apply_reflection(self.data)
            else:
                self.data = total_loss

            if self.interference_var.get():
                self._apply_interference_map(dem)
                self.loss_volume = self.interference_map[None, :, :]
                overlay = self.interference_map
            else:
                self.loss_volume = self.data[None, :, :]
                overlay = self.data

            self.overlay_matrix = overlay
            self.overlay_data = overlay
            self._update_overlay_style()
            self.overlay_visible = True
            self._update_loadbar(1.0)
            self.refresh()
            self.last_analysis_time = time.time() - start_time
            gc.collect()
            self.root.update_idletasks()
            self._set_controls_enabled("analysis", True)
            self._set_status("Analysis complete. Export options unlocked.")
            return
        if self.weather_gui is not None and WeatherConditions is not None:
            weather = self.weather_gui.get_weather()
            cloud = weather.cloud_cover_level
            precip = weather.precipitation_level
            temp = weather.temperature_c
            hum = weather.humidity_percent
        else:
            cloud = "None"
            precip = "None"
            temp = 20.0
            hum = 50.0
            weather = WeatherConditions() if WeatherConditions is not None else None
        ot = self.overlay_type_var.get()
        if ot == "wavefront" and propagate_wavefront and voxelize_dem and classify_material:
            materials = classify_material(rgb)
            voxels = voxelize_dem(dem)
            self.voxel_volume = voxels
            if hasattr(material_inference, "get_voxel_permeability"):
                perm2d = material_inference.get_voxel_permeability(materials)
                permeability = np.repeat(perm2d[None, :, :], voxels.shape[0], axis=0)
            else:
                permeability = None
            self.loss_volume = np.full_like(voxels, np.inf, dtype="float32")
            if aggregate_multi_tx is not None:
                tx_list = []
                for tx in self.txs:
                    tx_list.append(
                        {
                            "y": tx["y"],
                            "x": tx["x"],
                            "z": tx["z"],
                            "frequency_mhz": tx["frequency_mhz"],
                            "power_dbm": tx["power_dbm"],
                        }
                    )
                for _t in tx_list:
                    _t.setdefault("height_m", _t["z"])
                self.loss_volume = aggregate_multi_tx(
                    voxels,
                    materials,
                    permeability,
                    tx_list,
                    weather,
                )
                self._update_loadbar(1.0)
            else:
                for i, tx in enumerate(self.txs):
                    origin_z = tx["z"]
                    vol = propagate_wavefront(
                        voxels,
                        materials,
                        permeability,
                        (origin_z, tx["y"], tx["x"]),
                        tx["frequency_mhz"],
                        weather,
                    )
                    self.loss_volume = np.minimum(self.loss_volume, vol - tx["power_dbm"])
                    self._update_loadbar((i + 1) / len(self.txs))
            total_loss = self.loss_volume.min(axis=0)
        elif ot == "sphere":
            for i, tx in enumerate(self.txs):
                dist = np.hypot(
                    np.arange(dem.shape[0])[:, None] - tx["y"],
                    np.arange(dem.shape[1])[None, :] - tx["x"],
                )
                strength = tx["power_dbm"] - fspl(tx["frequency_mhz"], dist)
                total_loss = np.maximum(total_loss, strength)
                self._update_loadbar((i + 1) / len(self.txs))
        else:
            if not self._is_high_physics_enabled() and simulate_basic_rf is not None:
                total_loss = simulate_basic_rf(dem, self.txs)
                self._update_loadbar(1.0)
            else:
                for i, tx in enumerate(self.txs):
                    dist = np.hypot(
                        np.arange(dem.shape[0])[:, None] - tx["y"],
                        np.arange(dem.shape[1])[None, :] - tx["x"],
                    )
                    path = fspl(tx["frequency_mhz"], dist) + advanced_constant(
                        self.model_var.get(), self.param_var.get()
                    )
                    path += weather_loss(cloud, precip, temp, hum, tx["frequency_mhz"])
                    los, diff = compute_los_diffraction(
                        dem,
                        (tx["y"], tx["x"]),
                        tx["frequency_mhz"],
                        self.calibration.get("scale", 1.0),
                    )
                    dz = compute_dead_zone({"veg": veg_loss, "water": water_l}, los)
                    path += diff
                    multi = np.zeros_like(path)
                    for y in range(dem.shape[0]):
                        for x in range(dem.shape[1]):
                            multi[y, x] = multipath_loss(
                                dem,
                                (tx["y"], tx["x"]),
                                (y, x),
                                tx["frequency_mhz"],
                                self.calibration.get("scale", 1.0),
                            )
                    path += multi
                    if self.overlay_type_var.get() == "propagation":
                        total_loss += path + veg_loss + water_l - tx["power_dbm"]
                    else:
                        total_loss += (
                            path
                            + veg_loss
                            + water_l
                            + hazard * 0.5
                            + dz * 50
                            - tx["power_dbm"]
                        )
                    self._update_loadbar((i + 1) / len(self.txs))
        self.data = total_loss
        self.overlay_matrix = total_loss
        self.overlay_data = total_loss if ot != "sphere" else -total_loss
        self._update_overlay_style()
        self.overlay_visible = True
        print("[INFO] Overlay image assigned.")
        if contours_from_array is not None:
            try:
                from sim_rf_map.vector_tracing import contours_from_array_auto

                self.contours = contours_from_array_auto(total_loss)
            except Exception:
                self.contours = contours_from_array(total_loss)
        else:
            self.contours = None
        self.refresh()
        if self.voxel_toggle_var.get() or self.show_overlay_var.get():
            self._render_hybrid_view()
        try:
            from sim_rf_map.overlays.overlay_registry import register_all
            loss_vols = self.loss_volume if self.loss_volume is not None else [self.data]
            register_all(self.dem, self.txs, loss_vols)
        except Exception:
            pass
        self.last_analysis_time = time.time() - start_time
        logging.debug("Analysis finished in %.2fs", self.last_analysis_time)
        gc.collect()
        self.root.update_idletasks()
        self._set_controls_enabled("analysis", True)
        self._update_loadbar(1.0)
        self._set_status("Analysis complete. Export options unlocked.")

    @catch_errors
    def export_overlay(self) -> None:
        import logging  # Ensure logging is available in this method's scope
        if not hasattr(self, "overlay") and getattr(self, "overlay_data", None) is not None:
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
            if not file_path:
                return
            arr = np.asarray(self.overlay_data, dtype=float)
            arr = arr - np.nanmin(arr)
            max_value = np.nanmax(arr)
            if max_value > 0:
                arr = arr / max_value
            from PIL import Image as pil_image

            img = pil_image.fromarray((arr * 255).astype(np.uint8))
            img.save(file_path)
            if hasattr(self, "status_label"):
                self.status_label.config(text="Overlay exported successfully")
            return
        # Ensure overlay attribute exists and is not None
        if not hasattr(self, 'overlay') or self.overlay is None:
            # Initialize overlay if it doesn't exist
            if not hasattr(self, 'overlay'):
                self.overlay = None
                logging.warning("Overlay attribute was missing and has been initialized")
            messagebox.showwarning("RF Analyzer", "Nothing to export. Run analysis first.")
            return
        def task() -> None:
            logging.debug("Exporting overlay image")
            img = self.overlay
            if self.mode_var.get() == "composite" and self.image is not None:
                base = self.image.convert("RGBA")
                over = self.overlay.convert("RGBA")
                img = Image.blend(base, over, self.alpha_var.get())
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = save_overlay_georef(img, self.georef)
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump({"calibration": self.calibration, "txs": self.txs}, f)
            if self.data is not None:
                stats = {
                    "tx_count": len(self.txs),
                    "freqs": list({tx["frequency_mhz"] for tx in self.txs}),
                    "powers": list({tx["power_dbm"] for tx in self.txs}),
                    "loss_min": float(self.data.min()),
                    "loss_max": float(self.data.max()),
                    "mean_loss": float(self.data.mean()),
                    "dead_pixels": int(np.sum(self.data > 100.0)),
                    "coverage_percent": float(np.sum(self.data <= 100.0) / self.data.size * 100),
                }
                with open(Path("outputs") / f"session_{ts}.json", "w", encoding="utf-8") as f2:
                    json.dump(stats, f2, indent=2)
            self.root.after(0, lambda: messagebox.showinfo("RF Analyzer", f"Overlay saved to {out}"))
            self.root.after(0, lambda: self.flash_label(f"Exported overlay to {out}"))

        self._run_background(task, "Exporting overlay...")
        logging.debug("Overlay export initiated")

    @catch_errors
    def export_dem(self) -> None:
        if self.dem is None:
            messagebox.showwarning("RF Analyzer", "No DEM available")
            return
        with self.busy_feedback("Exporting DEM..."):
            img = Image.fromarray(self.dem.astype("float32"))
            Path("outputs").mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_png = Path("outputs") / f"dem_{ts}.png"
            from PIL import Image
            import numpy as np

            img_array = np.array(img)
            if img_array.dtype == np.float32 or img_array.dtype == np.float64:
                scaled = np.clip((img_array / img_array.max()) * 255, 0, 255).astype(np.uint8)
                img = Image.fromarray(scaled, mode="L")
            else:
                img = Image.fromarray(img_array.astype(np.uint8), mode="L")
            img.save(out_png)
            np.save(Path("outputs") / f"dem_{ts}.npy", self.dem)
            if rasterio and self.georef:
                meta = {
                    "driver": "GTiff",
                    "height": self.dem.shape[0],
                    "width": self.dem.shape[1],
                    "count": 1,
                    "dtype": "float32",
                    "transform": self.georef.get("transform"),
                    "crs": self.georef.get("crs"),
                }
                tif_out = Path("outputs") / f"dem_{ts}.tif"
                with rasterio.open(tif_out, "w", **meta) as dst:
                    dst.write(self.dem.astype("float32"), 1)
            # export simple OBJ mesh
            obj_path = Path("outputs") / f"dem_{ts}.obj"
            with open(obj_path, "w", encoding="utf-8") as f:
                rows, cols = self.dem.shape
                for y in range(rows):
                    for x in range(cols):
                        z = self.dem[y, x]
                        f.write(f"v {x} {y} {z}\n")
                for y in range(rows - 1):
                    for x in range(cols - 1):
                        i = y * cols + x + 1
                        f.write(f"f {i} {i+1} {i+cols}\n")
                        f.write(f"f {i+1} {i+cols+1} {i+cols}\n")
        messagebox.showinfo("RF Analyzer", f"DEM saved to {out_png}")
        self.flash_label(f"DEM exported to {out_png}")

    @catch_errors
    def export_vectors(self) -> None:
        import logging  # Ensure logging is available in this method's scope
        if self.contours is None:
            messagebox.showwarning("RF Analyzer", "No vectors to export")
            return
        with self.busy_feedback("Exporting vectors..."):
            logging.debug("Exporting %d vector groups", len(self.contours))
            Path("outputs").mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            svg_path = Path("outputs") / f"vectors_{ts}.svg"
            geo_path = Path("outputs") / f"vectors_{ts}.geojson"
            if save_svg is not None:
                save_svg(self.contours, svg_path, self.image.size if self.image else (0, 0))
            if save_geojson is not None:
                save_geojson(self.contours, geo_path)
        messagebox.showinfo("RF Analyzer", f"Vectors saved to {svg_path}")
        logging.debug("Vector export complete")
        self.flash_label(f"Vectors exported to {svg_path}")

    @catch_errors
    def show_slice(self) -> None:
        if show_loss_slice is None or self.loss_volume is None:
            messagebox.showwarning("RF Analyzer", "No loss volume to display")
            return
        show_loss_slice(self.loss_volume)

    @catch_errors
    def export_loss(self) -> None:
        import logging  # Ensure logging is available in this method's scope
        if export_loss_map is None or self.loss_volume is None:
            messagebox.showwarning("RF Analyzer", "No loss volume to export")
            return
        with self.busy_feedback("Exporting loss map..."):
            logging.debug("Saving loss volume")
            Path("outputs").mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = Path("outputs") / f"loss_{ts}.npy"
            export_loss_map(self.loss_volume, filename)
        self.flash_label(f"Loss map saved to {filename}")
        logging.debug("Loss map exported")

    @catch_errors
    def export_session(self) -> None:
        import logging  # Ensure logging is available in this method's scope
        if export_session_bundle is None or self.data is None:
            messagebox.showwarning("RF Analyzer", "Nothing to export")
            return
        with self.busy_feedback("Exporting session..."):
            logging.debug("Creating session bundle")
            dem = (
                self.dem
                if self.dem is not None
                else infer_dem_from_shading(np.array(self.image), self.calibration)
            )
            tx_list = []
            for tx in self.txs:
                tx_list.append(
                    {
                        "y": tx["y"],
                        "x": tx["x"],
                        "z": tx["z"],
                        "frequency_mhz": tx["frequency_mhz"],
                        "power_dbm": tx["power_dbm"],
                    }
                )
            for _t in tx_list:
                _t.setdefault("height_m", _t["z"])
            label = datetime.now().strftime("session_%Y%m%d_%H%M%S")
            export_session_bundle(dem, self.data, tx_list, label=label)
        messagebox.showinfo("RF Analyzer", "Session exported")
        logging.debug("Session bundle exported")
        self.flash_label("Session bundle exported")

    def _save_session(self) -> None:
        """Save current configuration to a JSON session file."""
        config = {
            "tx_list": self.txs,
            "overlay": self.mode_var.get() if hasattr(self, "mode_var") else None,
            "voxel_enabled": bool(getattr(self, "voxel_toggle_var", tk.IntVar(value=1)).get()),
            "heatmap_enabled": bool(getattr(self, "overlay_visible", True)),
            "passive_enabled": self.passive_mode_enabled,
        }
        file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not file:
            return
        from sim_rf_map.session.session_io import save_session
        save_session(file, config)
        self.flash_label(f"Session saved to {file}")

    def _load_session(self) -> None:
        """Load configuration from a JSON session file."""
        file = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not file:
            return
        from sim_rf_map.session.session_io import load_session
        sess = load_session(file)
        self.txs = sess.get("tx_list", [])
        if hasattr(self, "mode_var") and sess.get("overlay"):
            self.mode_var.set(sess["overlay"])
        if hasattr(self, "voxel_toggle_var"):
            self.voxel_toggle_var.set(1 if sess.get("voxel_enabled", True) else 0)
        self.overlay_visible = sess.get("heatmap_enabled", True)
        self.passive_mode_enabled = sess.get("passive_enabled", False)
        self.refresh()
        self.flash_label(f"Session loaded from {file}")

    def reset_all(self) -> None:
        """Clear all loaded data and disable controls."""
        self.image_path = None
        self.image = None
        if not hasattr(self, "txs") and hasattr(self, "tx_points"):
            for marker in getattr(self, "tx_markers", []):
                self.canvas.delete(marker)
            self.tx_points = []
            self.tx_markers = []
            self.dem = None
            self.overlay_data = None
            return
        self.overlay = None
        self.txs.clear()
        self.current_tx = None
        self.dem = None
        self.midas_dem = None
        self.physics_dem = None
        self.loss_volume = None
        self.voxel_volume = None
        self.hybrid_display = None
        self.overlay_img = None
        self.data = None
        self.canvas.delete("all")
        self._set_controls_enabled("dem", False)
        self._set_controls_enabled("analysis", False)
        self._set_status("Reset complete. Load a new DEM to begin.")

    def refresh(self) -> None:
        if not hasattr(self, "image") and getattr(self, "overlay_data", None) is not None:
            arr = np.asarray(self.overlay_data, dtype=float)
            arr = arr - np.nanmin(arr)
            max_value = np.nanmax(arr)
            if max_value > 0:
                arr = arr / max_value
            from PIL import Image as pil_image

            img = pil_image.fromarray((arr * 255).astype(np.uint8))
            if hasattr(self, "canvas"):
                self.canvas.itemconfig("image", image=img)
            if hasattr(self, "status_label"):
                self.status_label.config(text="Display refreshed")
            return
        if self.image is None:
            return
        mode = self.mode_var.get()
        if mode == "base" or self.overlay is None or not self.overlay_visible:
            img = self.image
        elif mode == "overlay":
            img = self.overlay
        elif mode == "veg" and self.veg_density is not None:
            img = generate_heatmap(self.veg_density.astype(float), cmap="Greens")
        elif mode == "water" and self.water_mask is not None:
            water_display = (
                self.water_activity if self.water_activity is not None else self.water_mask
            ).astype(float)
            img = generate_heatmap(water_display, cmap="Blues")
        elif mode == "composite":
            base = self.image.convert("RGBA")
            over = self.overlay.convert("RGBA")
            alpha = self.alpha_var.get()
            img = Image.blend(base, over, alpha)
        elif mode == "confidence" and self.confidence_map is not None:
            img = generate_heatmap(self.confidence_map.astype(float), cmap="viridis")
        elif mode == "diff" and self.midas_dem is not None and self.physics_dem is not None:
            diff_map = np.abs(self.midas_dem - self.physics_dem)
            img = generate_heatmap(diff_map, cmap="coolwarm")
        elif mode == "dead" and self.data is not None:
            img = generate_deadzone_map(self.data)
        else:
            base = self.image.convert("RGBA")
            over = self.overlay.convert("RGBA")
            alpha = self.alpha_var.get()
            img = Image.blend(base, over, alpha)
        if self.active_mode == "LoS Diagnostic Mode" and self.los_overlay is not None and self.overlay_visible:
            overlay = self.los_overlay.resize(img.size)
            img = Image.alpha_composite(img.convert("RGBA"), overlay)
        self.show_image(img)

    def show_image(self, img: Image.Image) -> None:
        if not hasattr(self, "_dev_frame_counter") and hasattr(self, "image_container"):
            from PIL import Image as pil_image

            converted = img.convert("RGB")
            photo = pil_image.PhotoImage(converted)
            self.canvas.itemconfig(self.image_container, image=photo)
            self.current_image = photo
            return
        self._dev_frame_counter += 1
        disp = img.copy()
        disp_w, disp_h = disp.size
        self.disp_size = (disp_w, disp_h)
        draw = ImageDraw.Draw(disp)
        base_w, base_h = self.image.size if self.image else disp.size
        for tx in self.txs:
            cx = int(tx["x"] / base_w * disp_w)
            cy = int(tx["y"] / base_h * disp_h)
            draw.line((cx - 5, cy, cx + 5, cy), fill="red")
            draw.line((cx, cy - 5, cx, cy + 5), fill="red")
        if self.vector_var.get() and self.contours is not None:
            scale_x = disp_w / base_w
            scale_y = disp_h / base_h
            for _, segs in self.contours:
                for seg in segs:
                    pts = [(p[0] * scale_x, p[1] * scale_y) for p in seg]
                    draw.line(pts, fill="yellow", width=1)
        if self.edit_mode == "veg" and self.veg_mask is not None:
            mask = Image.fromarray(self.veg_mask).resize(disp.size)
            disp.paste((0, 255, 0), mask=mask)
        if self.edit_mode == "water" and self.water_mask is not None:
            mask = Image.fromarray(self.water_mask).resize(disp.size)
            disp.paste((0, 0, 255), mask=mask)
        photo = ImageTk.PhotoImage(disp)
        self.overlay_img = photo
        if self.use_canvas:
            self.canvas.delete("all")
            self.canvas.update_idletasks()
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            img_x0 = max((canvas_w - disp_w) // 2, 0)
            img_y0 = max((canvas_h - disp_h) // 2, 0)
            self.img_offset = (img_x0, img_y0)
            self.canvas.create_image(img_x0, img_y0, anchor="nw", image=photo)
            self.canvas.configure(scrollregion=(0, 0, disp_w, disp_h))
        else:
            self.canvas.configure(image=photo)
            self.canvas.image = photo
            self.canvas.update_idletasks()
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            img_x0 = max((canvas_w - disp_w) // 2, 0)
            img_y0 = max((canvas_h - disp_h) // 2, 0)
            self.img_offset = (img_x0, img_y0)

    def _remove_crosshair(self) -> None:
        """Clear any crosshair currently drawn on the canvas."""
        if hasattr(self, "crosshair_ids"):
            for item in self.crosshair_ids:
                self.canvas.delete(item)
            self.crosshair_ids = []
            return
        if getattr(self, "_crosshair", None) and getattr(self, "use_canvas", True):
            for item in self._crosshair:
                self.canvas.delete(item)
            self._crosshair = None

    def _draw_crosshair(self, disp_x: int, disp_y: int) -> None:
        """Draw a small crosshair, highlighting if near a transmitter."""
        if not getattr(self, "use_canvas", True):
            return
        self._remove_crosshair()
        color = "yellow"
        if hasattr(self, "image") and getattr(self, "image", None) is not None:
            for tx in getattr(self, "txs", []):
                cx = int(tx["x"] / self.image.size[0] * self.disp_size[0]) + self.img_offset[0]
                cy = int(tx["y"] / self.image.size[1] * self.disp_size[1]) + self.img_offset[1]
                if abs(cx - disp_x) <= 5 and abs(cy - disp_y) <= 5:
                    color = "orange"
                    break
        h = self.canvas.create_line(disp_x - 5, disp_y, disp_x + 5, disp_y, fill=color)
        v = self.canvas.create_line(disp_x, disp_y - 5, disp_x, disp_y + 5, fill=color)
        self.crosshair_ids = [h, v]
        self._crosshair = (h, v)

    def pan_canvas(self, dx: int = 0, dy: int = 0) -> None:
        """Move the canvas view by ``dx`` and ``dy`` units."""
        if not getattr(self, "use_canvas", True):
            return
        self.canvas.xview_scroll(dx, "units")
        self.canvas.yview_scroll(dy, "units")


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--batch":
        batch_dir = Path(sys.argv[2])
        for img_path in batch_dir.glob("*.*"):
            rgb, dem, georef = load_input(img_path)
            wm, wa, vm, vd, dem_corr, conf = discriminate_water_veg(rgb)
            dem = dem.astype("float32") if dem is not None else dem_corr
            veg = vd
            water = wm
            hazard = compute_hazard(dem)
            veg_loss = vegetation_loss(dem, veg)
            water_l = water_loss(water, wa)
            dist = np.hypot(
                np.arange(dem.shape[0])[:, None] - dem.shape[0] // 2,
                np.arange(dem.shape[1])[None, :] - dem.shape[1] // 2,
            )
            loss = fspl(900, dist) + veg_loss + water_l + hazard * 0.5
            overlay = generate_heatmap(loss)
            save_overlay_georef(overlay, georef)
            diag = {
                "image": img_path.name,
                "min": float(loss.min()),
                "max": float(loss.max()),
                "veg_pct": float(veg.mean() / 255.0),
                "water_pct": float(water.mean() / 255.0),
            }
            json.dump(
                diag,
                open(Path("outputs") / f"diag_{img_path.stem}.json", "w", encoding="utf-8"),
                indent=2,
            )
        print("Batch processing complete")
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--diagnostics":
        arr = np.zeros((2, 2, 3), dtype=float)
        dem = infer_dem_from_shading(arr)
        print("Diag DEM range", dem.min(), dem.max())
        return

    if "--debug" in sys.argv:
        from sim_rf_map.logging_config import enable_dev_logging

        enable_dev_logging()

    root = tk.Tk()
    if "--dark" in sys.argv:
        apply_dark_mode(root)
    app = RFAnalyzerApp(root)
    app.refresh()
    root.mainloop()


def launch_gui() -> None:
    """Convenience wrapper to start the Tk GUI."""
    main()


if __name__ == "__main__":
    main()
