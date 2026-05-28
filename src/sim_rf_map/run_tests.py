# run_tests.py
#!/usr/bin/env python3
"""Simple wrapper to run the test suite with the correct PYTHONPATH."""
import os
import subprocess
from pathlib import Path

if __name__ == "__main__":
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", "src")
    src_path = Path(__file__).resolve().parents[1] / "src"
    env.setdefault("PYTHONPATH", str(src_path))
    raise SystemExit(subprocess.call(["pytest", "-q"], env=env))
