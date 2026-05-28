import json


def save_session(path: str, session_data: dict) -> None:
    """Save session data dictionary to ``path`` as JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)


def load_session(path: str) -> dict:
    """Load session data dictionary from ``path``."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
