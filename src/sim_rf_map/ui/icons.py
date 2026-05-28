"""Provide simple text-based icons for toolbar buttons."""

ICONS: dict[str, str] = {
    "open": "[]",
    "analyze": ">>",
    "export": "^",
    "dem": "##",
    "view3d": "<>",
    "help": "?",
}


def get_icon_text(name: str) -> str:
    """Return a short ASCII sequence for ``name``."""
    return ICONS.get(name, "")

