# Usage Guide

1. Install dependencies via `python dev_setup.py`.
   Requires Python 3.11 or newer.
2. Activate the environment: `source .venv/bin/activate`.
3. Run `python -m sim_rf_map.main --mode=lite` for the lightweight workflow.
4. Use `--mode=full` for the full 3D engine if a GUI is available.

If the application fails to launch in full mode on a headless server, retry with `--mode=lite`.
