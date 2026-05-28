from tkinter import TclError, Tk, ttk


def apply_dark_mode(root: Tk) -> None:
    """Apply a dark visual theme to ``root``."""
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except TclError:
        pass
    style.configure('.', background='#1e1e1e', foreground='#e0e0e0')
    style.configure('TButton', background='#333', foreground='#e0e0e0', bordercolor='#666')
    # Apply to classic Tk widgets as well
    try:
        root.tk_setPalette(
            background='#1e1e1e',
            foreground='#e0e0e0',
            activeBackground='#333',
            activeForeground='#e0e0e0',
        )
    except TclError:
        pass


def apply_light_mode(root: Tk) -> None:
    """Revert to the platform default light theme."""
    style = ttk.Style(root)
    try:
        style.theme_use('default')
    except TclError:
        pass
    style.configure('.', background='', foreground='')
    style.configure('TButton', background='', foreground='', bordercolor='')
    try:
        root.tk_setPalette('')
    except TclError:
        pass


# Backwards compatibility
apply_dark_theme = apply_dark_mode
apply_light_theme = apply_light_mode
