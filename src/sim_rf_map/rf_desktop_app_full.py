# frozen-app entry point for PyInstaller
from sim_rf_map.gui.main_window import launch_gui


def launch_app() -> None:
    """Launch the full desktop application."""
    launch_gui()


def main() -> None:
    """Compatibility wrapper for direct module execution."""
    launch_app()

if __name__ == "__main__":
    main()
