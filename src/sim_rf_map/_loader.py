"""Compatibility helpers for dynamic loading."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import types
import __future__


def load_with_future_annotations(path: Path, module_name: str):
    """Load module from ``path`` using future ``annotations`` flag."""
    source = path.read_text()
    flags = __future__.annotations.compiler_flag
    code = compile(source, str(path), "exec", flags=flags)
    module = types.ModuleType(module_name)
    sys.modules[module_name] = module
    exec(code, module.__dict__)
    return module
