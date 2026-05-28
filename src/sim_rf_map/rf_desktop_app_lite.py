import json
import logging
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from .tooltip import Tooltip
from .logging_config import configure_logging

# Configure logging system
configure_logging(level=logging.INFO)

import numpy as np
from PIL import Image, ImageTk, ImageDraw

from sim_rf_map.gui_tx_panel import TXControlPanel
from sim_rf_map.weather_gui import WeatherGUI
from sim_rf_map.weather_model import WeatherConditions
from sim_rf_map.rf_desktop_app import (
    load_input,
    infer_dem_from_shading,
    compute_hazard,
    vegetation_loss,
    water_loss,
    fspl,
    generate_heatmap,
    create_colorbar,
    cache_file,
    save_overlay_georef,
    compute_los,
    compute_dead_zone,
    map_display_to_image,
)
from sim_rf_map.voxelizer import generate_voxel_volume
from sim_rf_map.propagation.high_physics import simulate_high_physics_rf


class RFAnalyzerLite:
    def __init__(self, root: tk.Tk) -> None:
        logging.info("Initializing RFAnalyzerLite application")
        self.root = root
        self.root.title("SparkMind RF – Field Edition (ONIX Enabled)")

        # Set a better default window size (1024x768)
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = min(1024, screen_width - 100)
        window_height = min(768, screen_height - 100)

        # Center the window on the screen
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2

        # Set window size and position
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        # Allow window resizing
        self.root.minsize(800, 600)

        self.image = None
        self.dem = None
        self.txs = []
        self.georef = None
        self.overlay = None
        self.original_shape = None
        self.disp_size = (1, 1)
        self.img_offset = (0, 0)

        self.physics_simulation_mode = "high"
        self.heatmap_colormap = "turbo"  # Default colormap
        self.overlay_visible = True
        self.heatmap_centering = True
        self.darkmode = True
        self.voxel_visible = False

        self.use_canvas = True
        if self.use_canvas:
            self.canvas = tk.Canvas(root, highlightthickness=0, bg="black")
        else:
            self.canvas = tk.Label(root)
        self.canvas.pack(fill=tk.BOTH, expand=True)  # Fill available space

        self.root.configure(background="black")
        self.status = tk.StringVar(value="")
        self.loadbar = tk.StringVar(value="[--------------------------------------------------]")
        tk.Label(root, textvariable=self.loadbar, anchor="w", fg="cyan", bg="black").pack(fill="x", side=tk.BOTTOM)
        tk.Label(root, textvariable=self.status, anchor="w", fg="cyan", bg="black").pack(fill="x", side=tk.BOTTOM)

        btn_frame = tk.Frame(root, bg="black")
        btn_frame.pack(fill="x")

        # Left side buttons
        left_frame = tk.Frame(btn_frame, bg="black")
        left_frame.pack(side="left", fill="x")

        tk.Button(left_frame, text="Open", command=self.open_image).pack(side="left", padx=2)
        tk.Button(left_frame, text="Analyze", command=self.analyze).pack(side="left", padx=2)
        rm_btn = tk.Button(left_frame, text="Remove TX", command=self.remove_last_tx)
        rm_btn.pack(side="left", padx=2)
        Tooltip(
            rm_btn,
            "Remove the most recently placed transmitter in case you misclicked "
            "or want to reposition it elsewhere."
        )
        tk.Button(left_frame, text="Export", command=self.export_overlay).pack(side="left", padx=2)

        # Right side controls
        right_frame = tk.Frame(btn_frame, bg="black")
        right_frame.pack(side="right", fill="x")

        # Colormap selector
        tk.Label(right_frame, text="Colormap:", fg="white", bg="black").pack(side="left", padx=2)
        self.colormap_var = tk.StringVar(value=self.heatmap_colormap)
        colormap_options = ["turbo", "viridis", "plasma", "inferno", "magma", "jet", "rainbow", "terrain"]
        colormap_menu = tk.OptionMenu(right_frame, self.colormap_var, *colormap_options, command=self.set_colormap)
        colormap_menu.pack(side="left", padx=2)
        Tooltip(
            colormap_menu,
            "Select a colormap for the heatmap visualization. Different colormaps can help highlight different aspects of the data."
        )

        self.tx_panel = TXControlPanel(btn_frame)
        self.weather_gui = WeatherGUI(btn_frame)

        # Bind mouse and keyboard events
        self.canvas.bind("<Button-1>", self.set_tx)
        self.root.bind("<plus>", self.zoom_in)
        self.root.bind("<minus>", self.zoom_out)
        self.root.bind("<equal>", self.zoom_in)  # For keyboards where + is on the same key as =
        self.root.bind("<Control-plus>", self.zoom_in)
        self.root.bind("<Control-minus>", self.zoom_out)
        self.root.bind("<Control-equal>", self.zoom_in)
        self.root.bind("<Control-0>", self.reset_zoom)

        # Store zoom level
        self.zoom_level = 1.0

        default_dem = Path("field/dem.tif")
        default_tx = Path("field/tx.json")
        if default_dem.exists() and default_tx.exists():
            self._field_auto_run(str(default_dem), str(default_tx))

    def _is_high_physics_enabled(self) -> bool:
        return True

    def open_image(self) -> None:
        logging.info("Opening image file dialog")
        file = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.tif;*.tiff")])
        if not file:
            logging.info("Image file selection cancelled")
            return
        path = Path(file)
        logging.info(f"Loading image from: {path}")
        rgb, dem, self.georef = load_input(path)
        self.image = Image.fromarray(rgb.astype("uint8"))
        self.original_shape = self.image.size
        self.disp_size = self.image.size
        logging.info(f"Image loaded with dimensions: {self.image.size}")
        self.dem = dem if dem is not None else infer_dem_from_shading(rgb)
        logging.info("DEM data processed")
        cache_file(path, "uploads")
        self.txs.clear()
        self.refresh()

    def _load_dem(self, path: str) -> None:
        p = Path(path)
        rgb, dem, self.georef = load_input(p)
        self.image = Image.fromarray(rgb.astype("uint8"))
        self.dem = dem if dem is not None else infer_dem_from_shading(rgb)
        self.original_shape = self.image.size
        self.disp_size = self.image.size

    def _load_tx_from_file(self, path: str) -> None:
        data = json.loads(Path(path).read_text())
        if isinstance(data, list):
            self.txs = data
        else:
            self.txs = data.get("txs", [])

    def _field_auto_run(self, dem_path: str, tx_path: str) -> None:
        try:
            self._load_dem(dem_path)
            self._load_tx_from_file(tx_path)
            self._run_analysis()
        except Exception as exc:
            self._set_status(f"[FieldMode] Startup failed: {exc}")

    def set_tx(self, event: tk.Event) -> None:
        if self.image is None:
            return
        coords = map_display_to_image(
            event.x,
            event.y,
            self.img_offset,
            self.disp_size,
            self.image.size,
        )
        if coords is None:
            messagebox.showerror("RF Analyzer", "Click inside the image area")
            return
        x, y = coords
        cfg = self.tx_panel.get_tx_config()
        self.txs.append(
            {"x": x, "y": y, "frequency_mhz": cfg["frequency_mhz"], "power_dbm": cfg["power_dbm"]}
        )
        self.refresh()

    def remove_last_tx(self) -> None:
        """Remove the most recently placed transmitter."""
        if not self.txs:
            return
        self.txs.pop()
        self.refresh()

    def set_colormap(self, colormap: str) -> None:
        """Change the heatmap colormap and update the display if needed."""
        logging.info(f"Changing colormap to: {colormap}")
        self.heatmap_colormap = colormap

        # If we have an overlay, regenerate it with the new colormap
        if self.overlay and hasattr(self, 'loss'):
            self._set_status(f"Updating visualization with {colormap} colormap...")

            # Regenerate the heatmap with the new colormap
            heatmap = generate_heatmap(self.loss, cmap=self.heatmap_colormap)

            # Ensure heatmap matches original image dimensions
            if heatmap.size != self.image.size:
                heatmap = heatmap.resize(self.image.size, Image.LANCZOS)

            # Get original image dimensions
            orig_width, orig_height = self.image.size

            # Create a new colorbar with the updated colormap
            min_loss = float(np.nanmin(self.loss))
            max_loss = float(np.nanmax(self.loss))
            cb = create_colorbar(min_loss, max_loss, cmap=self.heatmap_colormap, shrink=0.9, aspect=15)

            if cb:
                # Calculate appropriate colorbar size
                cb_width = int(orig_width * 0.15)
                cb_height = int(orig_height * 0.8)
                cb_resized = cb.resize((cb_width, cb_height), Image.LANCZOS)

                # Position colorbar
                paste_x = orig_width - cb_width - 20
                paste_y = (orig_height - cb_height) // 2

                # Create a copy of the heatmap and add the colorbar
                heatmap_with_cb = heatmap.copy()
                heatmap_with_cb.paste(cb_resized, (paste_x, paste_y))
                self.overlay = heatmap_with_cb
            else:
                self.overlay = heatmap

            # Refresh the display
            self.refresh()
            self._set_status(f"Visualization updated with {colormap} colormap")

    def _set_status(self, message: str) -> None:
        self.status.set(message)
        self.root.update_idletasks()

    def _update_loadbar(self, progress: float) -> None:
        total = 50
        filled = int(progress * total)
        bar = "[" + ("=" * filled) + ("-" * (total - filled)) + "]"
        self.loadbar.set(bar)

    def analyze(self) -> None:
        self._run_analysis()

    def _run_analysis(self) -> None:
        logging.info("Starting RF analysis")
        if self.image is None:
            logging.warning("Analysis failed: No image loaded")
            messagebox.showerror("Error", "No image loaded.")
            return
        if not self.txs:
            logging.warning("Analysis failed: No transmitters placed")
            messagebox.showerror("Error", "Place at least one transmitter.")
            return

        self._set_status("Running field-grade analysis...")
        logging.info(f"Analysis parameters: {len(self.txs)} transmitters, image size: {self.image.size}")

        self._update_loadbar(0.1)
        logging.info("Generating voxel volume")
        self.voxel_volume = generate_voxel_volume(self.dem, {"scale": 2, "passes": 6})

        self._update_loadbar(0.3)
        logging.info("Simulating high physics RF propagation")
        loss = simulate_high_physics_rf(self.dem, self.txs)

        # Store the loss data for later use (e.g., when changing colormap)
        self.loss = loss

        self._update_loadbar(0.6)
        logging.info("Generating heatmap visualization")
        heatmap = generate_heatmap(loss, cmap=self.heatmap_colormap)

        # Store original image dimensions for reference
        orig_width, orig_height = self.image.size

        # Ensure heatmap matches original image dimensions for proper overlay
        if heatmap.size != self.image.size:
            logging.info(f"Resizing heatmap from {heatmap.size} to {self.image.size}")
            heatmap = heatmap.resize(self.image.size, Image.LANCZOS)

        min_loss = float(np.nanmin(loss))
        max_loss = float(np.nanmax(loss))
        logging.info(f"Signal loss range: min={min_loss:.2f}dB, max={max_loss:.2f}dB")

        # Create a more detailed colorbar
        cb = create_colorbar(min_loss, max_loss, cmap=self.heatmap_colormap, shrink=0.9, aspect=15)
        if cb:
            # Calculate appropriate colorbar size based on image dimensions
            cb_width = int(orig_width * 0.15)  # 15% of image width
            cb_height = int(orig_height * 0.8)  # 80% of image height
            cb_resized = cb.resize((cb_width, cb_height), Image.LANCZOS)

            # Position colorbar in the bottom-right corner with some padding
            paste_x = orig_width - cb_width - 20
            paste_y = (orig_height - cb_height) // 2

            # Create a copy of the heatmap to avoid modifying the original
            heatmap_with_cb = heatmap.copy()
            heatmap_with_cb.paste(cb_resized, (paste_x, paste_y))
            self.overlay = heatmap_with_cb
        else:
            self.overlay = heatmap

        self._update_loadbar(0.9)
        self.refresh()
        self._set_status("Analysis complete.")
        self._update_loadbar(1.0)
        logging.info("RF analysis completed successfully")

    def refresh(self) -> None:
        if self.image is None:
            return
        img = self.overlay if self.overlay else self.image

        # Get the canvas size for optimal display
        self.canvas.update_idletasks()
        canvas_w = max(self.canvas.winfo_width(), 800)  # Minimum width of 800px
        canvas_h = max(self.canvas.winfo_height(), 600)  # Minimum height of 600px

        # Calculate the optimal display size while maintaining aspect ratio
        img_w, img_h = img.size
        aspect_ratio = img_w / img_h

        # For post-analysis display (when overlay exists), use a larger size
        if self.overlay:
            # Use 90% of canvas size for display to leave some margin
            disp_w = int(canvas_w * 0.9)
            disp_h = int(disp_w / aspect_ratio)

            # If height exceeds canvas, adjust accordingly
            if disp_h > canvas_h * 0.9:
                disp_h = int(canvas_h * 0.9)
                disp_w = int(disp_h * aspect_ratio)
        else:
            # For original image, use 80% of canvas size
            disp_w = int(canvas_w * 0.8)
            disp_h = int(disp_w / aspect_ratio)

            # If height exceeds canvas, adjust accordingly
            if disp_h > canvas_h * 0.8:
                disp_h = int(canvas_h * 0.8)
                disp_w = int(disp_h * aspect_ratio)

        # Apply zoom factor to display size
        disp_w = int(disp_w * self.zoom_level)
        disp_h = int(disp_h * self.zoom_level)

        # Ensure minimum display size
        disp_w = max(disp_w, 200)
        disp_h = max(disp_h, 150)

        # Add zoom level indicator to status if zoomed
        if self.zoom_level != 1.0:
            self._set_status(f"Zoom: {self.zoom_level:.2f}x")

        # Resize the image for display while preserving quality
        disp = img.resize((disp_w, disp_h), Image.LANCZOS)
        self.disp_size = (disp_w, disp_h)

        # Draw transmitter markers
        draw = ImageDraw.Draw(disp)
        for tx in self.txs:
            cx = int(tx["x"] / img.width * disp_w)
            cy = int(tx["y"] / img.height * disp_h)
            # Make markers more visible
            marker_size = 7  # Increased from 5
            draw.line((cx - marker_size, cy, cx + marker_size, cy), fill="red", width=2)
            draw.line((cx, cy - marker_size, cx, cy + marker_size), fill="red", width=2)

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
        else:
            self.canvas.configure(image=photo)
            self.canvas.image = photo
            self.canvas.update_idletasks()
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            img_x0 = max((canvas_w - disp_w) // 2, 0)
            img_y0 = max((canvas_h - disp_h) // 2, 0)
            self.img_offset = (img_x0, img_y0)

    def zoom_in(self, event=None) -> None:
        """Increase zoom level and refresh display."""
        if self.image is None:
            return
        self.zoom_level *= 1.2  # Increase zoom by 20%
        self.zoom_level = min(self.zoom_level, 5.0)  # Cap at 5x zoom
        logging.info(f"Zooming in to {self.zoom_level:.2f}x")
        self._set_status(f"Zoom: {self.zoom_level:.2f}x")
        self.refresh()

    def zoom_out(self, event=None) -> None:
        """Decrease zoom level and refresh display."""
        if self.image is None:
            return
        self.zoom_level /= 1.2  # Decrease zoom by 20%
        self.zoom_level = max(self.zoom_level, 0.5)  # Minimum 0.5x zoom
        logging.info(f"Zooming out to {self.zoom_level:.2f}x")
        self._set_status(f"Zoom: {self.zoom_level:.2f}x")
        self.refresh()

    def reset_zoom(self, event=None) -> None:
        """Reset zoom to original level."""
        if self.image is None:
            return
        self.zoom_level = 1.0
        logging.info("Resetting zoom to 1.0x")
        self._set_status("Zoom reset to 1.0x")
        self.refresh()

    def export_overlay(self) -> None:
        logging.info("Attempting to export overlay")
        if self.overlay is None:
            logging.warning("Export failed: No overlay available")
            messagebox.showwarning("Field Mode", "Run analysis first")
            return

        # Ask user for export quality
        logging.info("Prompting user for export quality")
        quality_options = {
            "Standard (Original Size)": "original",
            "High Resolution (2x)": "2x",
            "Ultra HD (4x)": "4x"
        }

        quality = simpledialog.askstring(
            "Export Quality",
            "Select export quality:",
            initialvalue="Standard (Original Size)",
        )

        if not quality or quality not in quality_options:
            quality = "Standard (Original Size)"
            logging.info(f"Using default quality: {quality}")
        else:
            logging.info(f"Selected quality: {quality}")

        logging.info("Opening save file dialog")
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile="field_result.png",
            filetypes=[("PNG", "*.png")],
        )

        if not path:
            logging.info("Export cancelled by user")
            return

        # Export at selected quality
        quality_mode = quality_options[quality]

        if quality_mode == "original":
            # Save at original resolution
            logging.info(f"Exporting overlay to: {path} at original resolution")
            self.overlay.save(path)
            logging.info(f"Overlay successfully exported to: {path}")
            self._set_status(f"Overlay exported to {path} at original resolution")
        else:
            # Get scale factor
            scale = 2 if quality_mode == "2x" else 4

            # Get original image size
            orig_w, orig_h = self.overlay.size

            # Calculate new size
            new_w = orig_w * scale
            new_h = orig_h * scale

            logging.info(f"Resizing overlay from {orig_w}x{orig_h} to {new_w}x{new_h}")

            # Resize using high-quality LANCZOS resampling
            high_res = self.overlay.resize((new_w, new_h), Image.LANCZOS)

            # Save high-resolution image
            logging.info(f"Exporting high-resolution overlay to: {path}")
            high_res.save(path)
            logging.info(f"High-resolution overlay successfully exported to: {path}")
            self._set_status(f"Overlay exported to {path} at {quality} ({new_w}x{new_h})")


def launch_app() -> None:
    """Launch Lite mode through the shared desktop application surface."""
    logging.info("Launching RF Mapper Lite through the shared desktop application")
    from sim_rf_map.gui.main_window import launch_gui

    launch_gui()


if __name__ == "__main__":
    launch_app()
