import os


def choose_mode(gui_supported: bool = True) -> str:
    """Return the runtime mode without opening an interactive prompt.

    Parameters
    ----------
    gui_supported:
        If ``False`` the function returns ``"lite"`` so callers can avoid
        launching GUI-only features in headless environments.
    """

    if not gui_supported:
        return "lite"

    mode = os.getenv("ONYX_MODE", "full").strip().lower()
    return mode if mode in {"full", "lite"} else "full"
