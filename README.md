# RF Mapper

RF Mapper is an offline desktop application for terrain-aware RF propagation analysis. It combines image and DEM processing, RF loss modeling (free-space, knife-edge diffraction, two-ray ground reflection, effective-earth refraction, rain/cloud attenuation), line-of-sight checks, heatmap overlays, and export tooling for field or lab workflows.

The import package is `sim_rf_map` for compatibility. The product-facing package and command name are `rf-mapper`.

## Features

- Tkinter desktop GUI (Full and Lite editions) for loading imagery, placing transmitters, generating RF overlays, and exporting analysis products.
- CLI batch runner for headless simulations with multi-transmitter JSON configs.
- Core RF math library (`sim_rf_map.rf`): unit conversions (dBm/W/dB), canonical ITU-R P.525 free-space path loss, link budgets (EIRP, received power, kTB noise floor, SNR), grid/geodesic geometry, and pixel-to-world mapping.
- Physics stack: ITU-R P.526-style knife-edge diffraction, first Fresnel zone clearance, ITU-R P.527 ground reflection coefficients with a flat-earth two-ray model, ITU-R P.453 refractivity / effective-earth-radius (k-factor), ITU-R P.838 rain and P.840 cloud attenuation, and multi-transmitter aggregation (strongest-signal or coherent phase sum). Approximations are named in each module's docstring.
- Exports: PNG, NPY, SVG and GeoJSON contours, GeoTIFF (when `rasterio` is installed and input is georeferenced), OBJ meshes, and SHA-256 metadata sidecars.
- Optional MiDaS ONNX depth inference through `weights/model_small.onnx` (see `weights/README.md`).
- Optional WhiteboxTools and ITU-R (`itur`) integrations — detected at runtime, never required.

## Quick Start

Create an environment and install the project in editable mode:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

For a minimal (Lite-capable) install without the heavy geospatial/ML stack:

```powershell
python -m pip install -e .
```

Full-mode extras (rasterio, onnxruntime, opencv, numba, itur, whitebox):

```powershell
python -m pip install -e ".[full]"
```

Launch the GUI:

```powershell
rf-mapper
```

The legacy command remains available:

```powershell
sim-rf-map
```

Check your installation:

```powershell
rf-mapper-doctor
```

Run the test suite:

```powershell
python -m pytest -q
```

## Runtime Modes

RF Mapper supports two runtime modes:

- `full` (default): the complete desktop application — advanced propagation models, voxel/3D views, multi-transmitter analysis, DEM diagnostics, and the full export surface.
- `lite`: a genuinely reduced window (Open / Analyze / Remove TX / Export, colormap picker, zoom) that runs a fast free-space + line-of-sight analysis, downsamples large grids for speed, and needs only the core dependencies. Suitable for field laptops and demos.

Select a mode with either the application launcher or the environment variable:

```powershell
python -m sim_rf_map.main --mode=lite
$env:ONYX_MODE = "lite"; rf-mapper
```

The mode selector is deterministic; there is no startup dialog.

## CLI Batch Usage

Run batch simulations headlessly. Transmitters come from a JSON file:

```powershell
python -m sim_rf_map.cli_batch_runner --input dem.png --tx configs.json --output out_dir
```

`configs.json` is a JSON list of transmitters with pixel coordinates:

```json
[
  {"x": 5,  "y": 5,  "frequency_mhz": 900, "power_dbm": 30},
  {"x": 34, "y": 30, "frequency_mhz": 900, "power_dbm": 27}
]
```

Optional per-transmitter `z` (voxel layer) defaults to the terrain surface. A single transmitter can also be given with `--tx-x/--tx-y/--tx-power`; with no transmitter flags the DEM center is used (with a warning). Outputs are a loss-map `.npy`, a PNG overlay, and `.meta.json` sidecars. See `--help` for weather, resolution, and `--high-physics` options.

## Build

Build scripts wrap PyInstaller and set the correct runtime mode:

```powershell
python build_lite.py
python build_full.py
```

Both run the test suite first and abort on failures; coverage below 70% is a warning, not a blocker. Output lands in `dist/`. `build_full.py` bundles the ONNX model and WhiteboxTools payloads only when they exist locally — the build no longer fails when optional resources are absent. PyInstaller comes from the `build` extra: `pip install -e ".[build]"`.

## Dependencies

Core runtime dependencies (Lite): numpy, matplotlib, Pillow, scikit-image, psutil — see `requirements-runtime.txt` and `pyproject.toml`.

Optional extras:

- `.[full]`: rasterio (GeoTIFF), onnxruntime (depth inference), opencv-python, numba, itur, whitebox.
- `.[dev]`: tests, linting, coverage, packaging helpers, plus the full-mode stack.
- `.[build]`: PyInstaller build dependencies.
- `.[3d]`: pyqtgraph and PySide6 for optional 3D visualization components.

Missing optional dependencies are detected at startup (`sim_rf_map.capabilities`) and reported in the GUI status bar and by `rf-mapper-doctor`; features degrade gracefully instead of crashing.

## Configuration And Paths

- User configuration lives at `~/.sim_rf_map/config.json` (`--config` overrides; `--repair-config` fixes a broken file).
- Runtime folders (`outputs/`, `logs/`, `uploads/`, `sessions/`) are created automatically next to the project (or the executable when frozen). Set `RF_MAPPER_DATA_DIR` to relocate them.
- `ONYX_MODE` (`full`/`lite`) selects the runtime mode; `ONYX_MODEL_PATH` points at an alternative ONNX depth model.

## Math And Model Notes

Formulas and approximations are documented per module (see `docs/PHYSICS-SPEC.md` and `docs/physics_models.md`). Known-value tests in `tests/rf/` and `tests/test_physics_validation.py` pin FSPL, knife-edge J(v), Fresnel radii, dBm/W conversions, and noise-floor values against hand-computed references. Notable approximations: single-dominant-edge knife-edge diffraction (Deygout-style multi-edge is simplified), flat-earth two-ray reflection, tabulated ITU-R P.838-1 rain coefficients, and empirical (Weissberger-style) vegetation attenuation.

## Logs And Outputs

Local runtime files are intentionally ignored by git: `logs/`, `outputs/`, `uploads/`, `sessions/`, `dist/`, `build/`, `release_build/`.

## Known Limitations

- The MiDaS depth model is not bundled; depth inference stays disabled until `weights/model_small.onnx` is provided (`ONYX_MODEL_PATH` supported).
- GeoTIFF export requires `rasterio` and a georeferenced input; otherwise exports fall back to PNG with a logged warning.
- Grid analyses treat pixels as fixed-size ground cells (default 30 m in Full, configurable via `--resolution` in the CLI); no CRS reprojection is performed.
- The experimental MVC GUI under `src/sim_rf_map/gui/{controllers,models,views}` is a parallel refactor that is tested but not yet the launched window.
