# RF Mapper

RF Mapper is an offline desktop application for terrain-aware RF propagation analysis. It combines image and DEM processing, MiDaS-based depth inference, RF loss modeling, line-of-sight checks, heatmap overlays, and export tooling for field or lab workflows.

The import package is still `sim_rf_map` for compatibility. The product-facing package and command name are `rf-mapper`.

## Features

- Tkinter desktop GUI for loading imagery, generating RF overlays, and exporting analysis products.
- CLI batch runner for headless simulations and automated export workflows.
- RF propagation helpers for free-space path loss, vegetation and water attenuation, Fresnel zones, knife-edge diffraction, weather loss, and multi-transmitter aggregation.
- Geospatial export support for PNG, GeoTIFF-style overlays, SVG, GeoJSON, and metadata sidecars.
- Optional MiDaS ONNX depth model support through `weights/model_small.onnx`.
- Optional WhiteboxTools and ITU-R model integrations for terrain and propagation analysis.
- Optional 3D visualization support through the `3d` extra.

## Quick Start

Create an environment and install the project in editable mode:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Launch the GUI:

```powershell
rf-mapper
```

The legacy command remains available:

```powershell
sim-rf-map
```

Run the focused smoke tests:

```powershell
python -m pytest tests/test_entrypoint.py tests/core/test_main.py tests/test_build_scripts.py tests/test_build.py -q
```

## Runtime Modes

RF Mapper supports two runtime modes:

- `full`: default desktop mode.
- `lite`: reduced mode for constrained or headless environments.

You can select a mode with either the application launcher or the environment variable:

```powershell
python -m sim_rf_map.main --mode=lite
$env:ONYX_MODE = "lite"; rf-mapper
```

The mode selector is deterministic. It no longer opens a startup dialog.

## CLI Batch Usage

Run batch simulations headlessly:

```powershell
python -m sim_rf_map.cli_batch_runner --input dem.tif --tx configs.json --output out_dir
```

## Build

Build scripts wrap PyInstaller and set the correct runtime mode:

```powershell
python build_lite.py
python build_full.py
```

The build scripts still fail on test failures. Coverage below 70% is reported as a portfolio target warning, not a hard build blocker.

## Dependencies

Runtime dependencies are listed in `requirements-runtime.txt` and `pyproject.toml`. Development and build dependencies are in `requirements.txt` and optional extras.

Notable optional extras:

- `.[dev]`: tests, linting, coverage, and packaging helpers.
- `.[build]`: PyInstaller build dependencies.
- `.[setup]`: development setup helper dependencies.
- `.[3d]`: pyqtgraph and PySide6 for optional 3D visualization components.

## Logs And Outputs

Local runtime files are intentionally ignored by git:

- `logs/`
- `outputs/`
- `uploads/`
- `dist/`
- `build/`
- `release_build/`

Implementation notes for the current productization pass are in `reports/2026-05-26_implementation-notes.md`.
