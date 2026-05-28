# Developer Setup

This guide helps contributors work on RF Mapper locally.

## Environment

Create a virtual environment from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

For optional setup helper scripts, install the setup extra:

```powershell
python -m pip install -e ".[setup]"
```

For optional 3D visualization work, install the 3D extra:

```powershell
python -m pip install -e ".[3d]"
```

## Run The App

Launch the default desktop GUI:

```powershell
rf-mapper
```

The legacy command remains available for compatibility:

```powershell
sim-rf-map
```

Run the explicit mode-aware launcher:

```powershell
python -m sim_rf_map.main --mode=full
python -m sim_rf_map.main --mode=lite
```

## Runtime Modes

`full` is the default mode. `lite` can be selected through `--mode=lite` or `ONYX_MODE=lite`.

```powershell
$env:ONYX_MODE = "lite"
rf-mapper
```

The startup mode selector is deterministic and does not open an interactive prompt.

## Tests

Run the focused productization smoke suite:

```powershell
python -m pytest tests/test_entrypoint.py tests/core/test_main.py tests/test_build_scripts.py tests/test_build.py -q
```

Run the full suite when changing RF, export, or GUI behavior:

```powershell
python -m pytest
```

## Build

Build wrappers use PyInstaller through the maintained Python scripts:

```powershell
python build_lite.py
python build_full.py
```

Batch wrappers are available on Windows:

```powershell
.\build_light.bat
.\build_full.bat
```

The build scripts fail on test failures. Coverage below 70% is logged as a portfolio target warning rather than a hard blocker.

## Dependency Files

- `pyproject.toml` is the source of package metadata and extras.
- `requirements-runtime.txt` lists runtime dependencies only.
- `requirements.txt` is the development lock used by existing automation.

Runtime files under `logs/`, `outputs/`, `uploads/`, `build/`, `dist/`, and `release_build/` are ignored by git.
