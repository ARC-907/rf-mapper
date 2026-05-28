import json
import hashlib
from pathlib import Path
from datetime import datetime


def sha256_of_file(path: str) -> str:
    """Return SHA-256 hash hex digest of a file."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_meta_for(path: str, context: dict) -> None:
    """Write a .meta.json file next to ``path`` with context and file info."""
    out_path = Path(path)
    meta = {
        "file": out_path.name,
        "path": str(out_path.resolve()),
        "hash_sha256": sha256_of_file(path),
        "timestamp": datetime.utcnow().isoformat(),
    }
    meta.update(context)
    with open(out_path.with_suffix(out_path.suffix + ".meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
