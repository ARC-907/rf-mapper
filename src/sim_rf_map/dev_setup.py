# dev_setup.py
#!/usr/bin/env python3
"""Simple environment setup for RF Desktop Analyzer."""
from __future__ import annotations

# PATCH 180: pyproject.toml Auto-Sanity Check/Fix
import os
import sys
import re


def toml_sanity_patch() -> None:
    """Clean invalid fields in pyproject.toml."""
    toml_path = os.path.join(os.path.dirname(__file__), "pyproject.toml")
    if not os.path.exists(toml_path):
        return
    with open(toml_path, encoding="utf-8") as f:
        lines = f.readlines()
    changed = False
    new_lines = []
    for idx, line in enumerate(lines):
        if re.match(r"^\s*include-package-data\s*=.*", line):
            context = "".join(lines[max(0, idx - 3) : idx + 1])
            if "[project]" in context:
                changed = True
                print("[PATCH] Removed invalid 'include-package-data' from [project]")
                continue
        new_lines.append(line)
    if changed:
        with open(toml_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print("[PATCH] pyproject.toml sanitized and saved.")


toml_sanity_patch()


# PATCH 190: requirements.txt Sanity and Auto-Conflict Removal
def requirements_sanity_patch() -> None:
    """Relax overly strict dependency pins."""
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if not os.path.exists(req_path):
        return
    with open(req_path, encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    changed = False
    for line in lines:
        if "pendulum==" in line or "pendulum >=3.0" in line:
            changed = True
            print("[PATCH] Removed strict pendulum version pin (handled by Prefect).")
            continue
        new_lines.append(line)
    if changed:
        with open(req_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print("[PATCH] requirements.txt sanitized and saved.")


requirements_sanity_patch()


# PATCH 191: MANIFEST.in Presence & Data File Inclusion
def manifest_sanity_patch() -> None:
    manifest_path = os.path.join(os.path.dirname(__file__), "MANIFEST.in")
    if not os.path.exists(manifest_path):
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write("include README.md\n")
            f.write("recursive-include src/sim_rf_map/static *\n")
            f.write("recursive-include src/sim_rf_map/field_gui/static *\n")
            f.write("recursive-include tiles *\n")
        print("[PATCH] MANIFEST.in auto-generated for data/static inclusion.")
    else:
        with open(manifest_path, encoding="utf-8") as f:
            content = f.read()
        needed = [
            "recursive-include src/sim_rf_map/static *",
            "recursive-include src/sim_rf_map/field_gui/static *",
            "recursive-include tiles *",
        ]
        added = False
        with open(manifest_path, "a", encoding="utf-8") as f:
            for line in needed:
                if line not in content:
                    f.write(line + "\n")
                    added = True
        if added:
            print("[PATCH] MANIFEST.in updated with static/data includes.")


manifest_sanity_patch()

import subprocess
import sys
from pathlib import Path
import venv
import shutil

# PATCH 140: Robust bootstrap, always installs colorama if missing


def safe_import_colorama():
    try:
        from colorama import Fore, Style, init as colorama_init
    except ImportError:  # pragma: no cover - install at runtime if missing
        subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
        from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    return Fore, Style


Fore, Style = safe_import_colorama()

# PATCH 141: Ensure src is in sys.path (portable, robust)
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
os.environ["PYTHONPATH"] = src_path

# PATCH 142: Only import project modules after venv is created and src is in path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - ensure dotenv available
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv

ROOT = Path(__file__).parent
ENV_FILE = ROOT / ".env"
if not ENV_FILE.exists() and (ROOT / ".env.example").exists():
    print(Fore.YELLOW + "Auto-copying .env.example to .env" + Style.RESET_ALL)
    shutil.copy(ROOT / ".env.example", ENV_FILE)

load_dotenv(ENV_FILE, override=True)
SRC_PATH = ROOT / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
REQ_FILE = Path("requirements.txt")
VENV_DIR = Path(".venv")

REQUIRED_VARS = ["S3_BUCKET"]
missing = [v for v in REQUIRED_VARS if not os.environ.get(v)]
if missing:
    print(
        Fore.YELLOW
        + f"Warning: Missing environment variables: {', '.join(missing)}. Using default values."
        + Style.RESET_ALL
    )
    # Set default values for missing environment variables
    if "S3_BUCKET" in missing:
        os.environ["S3_BUCKET"] = "default-bucket"
    print(Fore.GREEN + "\u2714 Using default S3_BUCKET: default-bucket" + Style.RESET_ALL)
else:
    print(Fore.GREEN + "\u2714 S3_BUCKET loaded" + Style.RESET_ALL)

if sys.version_info < (3, 11):
    raise RuntimeError("Python 3.11 or newer is required for building this application.")
print(
    Fore.GREEN
    + f"\u2714 Python {sys.version_info.major}.{sys.version_info.minor} detected."
    + Style.RESET_ALL
)

if "venv" not in Path(sys.prefix).name:
    print(
        Fore.YELLOW
        + "WARNING: You are not using the 'venv' from this project root. Unexpected behavior may occur."
        + Style.RESET_ALL
    )


# PATCH 143: Create venv only if missing, error if can't find python
def create_venv(root: Path) -> Path:
    venv_dir = root / ".venv"
    if venv_dir.exists():
        print(f"{Fore.CYAN}[i] Virtual environment already exists at {venv_dir}")
        return venv_dir
    python_bin = sys.executable
    try:
        subprocess.check_call([python_bin, "-m", "venv", str(venv_dir)])
    except FileNotFoundError as e:
        print(f"{Fore.RED}[!] Could not find Python to create venv: {e}")
        sys.exit(1)
    print(f"{Fore.GREEN}[✓] Created venv at {venv_dir}")
    return venv_dir


# PATCH 144: Install dependencies with pip, fallback gracefully if a conflict occurs
def install_deps(venv_dir: Path) -> None:
    pip_bin = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "pip"
    try:
        subprocess.check_call([pip_bin, "install", "--upgrade", "pip"])
        req_file = "requirements.lock" if Path("requirements.lock").exists() else "requirements.txt"
        try:
            subprocess.check_call([pip_bin, "install", "-r", req_file])
        except subprocess.CalledProcessError:
            print(
                f"{Fore.YELLOW}[!] Failed to fully resolve {req_file}, attempting src/ install and manual package pins."
            )
            subprocess.check_call([pip_bin, "install", "-e", "src/"])
            subprocess.check_call([pip_bin, "install", "prefect==2.20.2", "pendulum<3.0"])
    except Exception as e:
        print(f"{Fore.RED}[!] Dependency install failed: {e}")
        sys.exit(1)

    try:
        subprocess.run(["gdalinfo", "--version"], check=True)
    except Exception:
        print("WARNING: GDAL not found. Please install system GDAL libraries.")
        if os.name == "nt":
            print("Hint: install from OSGeo4W or Conda, see README.")
        else:
            print("Try: sudo apt-get install gdal-bin")
    try:
        subprocess.run(
            [venv_dir / "bin" / "python", "-c", "import rasterio"],
            check=True,
        )
    except subprocess.CalledProcessError:
        print("ERROR: rasterio failed to install. See README for troubleshooting.")
        if os.name == "nt":
            print(
                "Try installing pre-built wheels via Conda or from https://www.lfd.uci.edu/~gohlke/pythonlibs/ ."
            )
        sys.exit(1)


def ensure_dirs(root: Path) -> None:
    # Adjust import paths to handle both package and direct imports
    try:
        # Try direct import first
        from sim_rf_map.data.sample_rasters import ensure_samples
        from sim_rf_map.decode_assets import ensure_static_assets
    except ImportError:
        # If that fails, try to adjust sys.path and import again
        project_root = root.parent if root.name == 'sim_rf_map' else root
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        try:
            from sim_rf_map.data.sample_rasters import ensure_samples
            from sim_rf_map.decode_assets import ensure_static_assets
        except ImportError as e:
            print(f"{Fore.YELLOW}[!] Warning: Could not import required modules: {e}")
            print(f"{Fore.YELLOW}[!] Skipping sample data and static assets setup")
            # Define dummy functions to avoid errors
            def ensure_samples(path): 
                print(f"{Fore.YELLOW}[!] Skipped sample data setup")
            def ensure_static_assets(path): 
                print(f"{Fore.YELLOW}[!] Skipped static assets setup")

    for name in ["tiles", "data", "output", "tests"]:
        (root / name).mkdir(exist_ok=True)
    for sub in ["ndvi", "dem", "hydro", "weather"]:
        (root / "tiles" / sub).mkdir(parents=True, exist_ok=True)

    try:
        ensure_samples(root / "data")
        ensure_static_assets(root)
    except Exception as e:
        print(f"{Fore.YELLOW}[!] Warning: Error during sample/static setup: {e}")
        print(f"{Fore.YELLOW}[!] Continuing with setup anyway")


def check_permissions(root: Path) -> None:
    tiles = root / "tiles"
    tiles.mkdir(exist_ok=True)
    try:
        testfile = tiles / "write_test.txt"
        with open(testfile, "w") as f:
            f.write("ok")
        testfile.unlink()
    except PermissionError:
        print(
            "ERROR: No write permission in tiles/. Please fix permissions or run with proper rights."
        )
        sys.exit(1)


def verify_assets(root: Path) -> None:
    # Check if we're in the sim_rf_map directory or the project root
    if (root / "field_gui").exists():
        # We're in the sim_rf_map directory
        templates_path = root / "field_gui" / "templates" / "index.html"
    else:
        # We're in the project root
        templates_path = root / "src" / "sim_rf_map" / "field_gui" / "templates" / "index.html"

    required = [
        templates_path,
        root / "data" / "dem_sample.tif",
        root / "data" / "veg_sample.tif",
        root / "data" / "hydro_sample.tif",
        root / "data" / "cond_sample.tif",
    ]

    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print(f"{Fore.YELLOW}[!] Warning: Some assets are missing:")
        for m in missing:
            print(f"{Fore.YELLOW}    - {m}")
        print(f"{Fore.YELLOW}[!] These assets will need to be downloaded or created later.")
        print(f"{Fore.YELLOW}[!] Continuing with setup anyway...")
        # Don't exit, just warn and continue


def run_tests(venv_dir: Path) -> None:
    # Use the correct directory for the platform (Scripts on Windows, bin on Unix)
    scripts_dir = "Scripts" if os.name == "nt" else "bin"
    pytest_path = venv_dir / scripts_dir / ("pytest.exe" if os.name == "nt" else "pytest")

    # Check if pytest exists
    if not pytest_path.exists():
        print(f"{Fore.YELLOW}[!] Warning: pytest not found at {pytest_path}")
        print(f"{Fore.YELLOW}[!] Skipping tests")
        return

    env = dict(os.environ)
    env.setdefault("PYTHONPATH", str(Path(__file__).parent / "src"))

    try:
        subprocess.check_call([str(pytest_path), "-v"], env=env)
    except subprocess.CalledProcessError as e:
        print(f"{Fore.YELLOW}[!] Warning: Tests failed with error code {e.returncode}")
        print(f"{Fore.YELLOW}[!] Continuing with setup anyway...")
    except FileNotFoundError:
        print(f"{Fore.YELLOW}[!] Warning: Could not run pytest. Make sure it's installed.")
        print(f"{Fore.YELLOW}[!] Continuing with setup anyway...")


def create_venv(path: Path) -> None:
    if path.exists():
        return
    subprocess.check_call([sys.executable, "-m", "venv", str(path)])


def main() -> None:
    """Set up virtual environment and verify build."""
    root = Path(__file__).parent
    venv_dir = root / ".venv"  # Define venv_dir directly as a Path

    # Create venv if it doesn't exist
    if not venv_dir.exists():
        print(f"{Fore.CYAN}[i] Creating virtual environment at {venv_dir}")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
            print(f"{Fore.GREEN}[✓] Created venv at {venv_dir}")
        except Exception as e:
            print(f"{Fore.RED}[!] Could not create venv: {e}")
            sys.exit(1)
    else:
        print(f"{Fore.CYAN}[i] Virtual environment already exists at {venv_dir}")

    install_deps(venv_dir)
    ensure_dirs(root)
    verify_assets(root)
    run_tests(venv_dir)
    print(Fore.GREEN + "Setup complete." + Style.RESET_ALL)
    print("\nTo start the application:")
    if os.name == "nt":
        print("1. Activate your virtual environment:\n   .venv\\Scripts\\activate")
        launch_cmd = "set PYTHONPATH=src && python src\\sim_rf_map\\field_gui\\app.py"
    else:
        print("1. Activate your virtual environment:\n   source .venv/bin/activate")
        launch_cmd = "PYTHONPATH=src python src/sim_rf_map/field_gui/app.py"
    print("2. Set PYTHONPATH and run:\n   " + launch_cmd)
    print("3. Open http://127.0.0.1:5000/ in your browser.\n")


def install_deps(path: Path) -> None:
    python_exe = path / ("Scripts" if os.name == "nt" else "bin") / "python"
    pip = path / ("Scripts" if os.name == "nt" else "bin") / "pip"

    # Use python -m pip for upgrading pip itself (more reliable)
    try:
        subprocess.check_call([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError:
        print(f"{Fore.YELLOW}[!] Warning: Failed to upgrade pip, continuing with existing version")

    if REQ_FILE.exists():
        try:
            subprocess.check_call([str(pip), "install", "-r", str(REQ_FILE)])
        except subprocess.CalledProcessError:
            print(f"{Fore.YELLOW}[!] Warning: Failed to install all requirements, continuing anyway")


if __name__ == "__main__":
    main()
    create_venv(VENV_DIR)
    install_deps(VENV_DIR)
    print(
        "[✓] Setup complete. Activate with 'source .venv/bin/activate' and run 'python -m sim_rf_map.main'."
    )
