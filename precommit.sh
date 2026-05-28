
#!/bin/sh
set -e
python check_markers.py
python run_tests.py
python src/sim_rf_map/run_tests.py
ruff .
pip-compile --generate-hashes -o requirements_lock.txt requirements.txt
git diff --quiet requirements_lock.txt || {
  echo "Lock file is out of date. Run pip-compile." >&2
  exit 1
}
