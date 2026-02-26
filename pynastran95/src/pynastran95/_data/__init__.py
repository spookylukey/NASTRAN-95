"""Bundled NASTRAN-95 data files.

Provides paths to the bundled nastrn executable and rigid format files
when installed from a wheel.
"""

from __future__ import annotations

import platform
from pathlib import Path

_DATA_DIR = Path(__file__).parent


def get_executable() -> Path | None:
    """Return path to the bundled nastrn executable, or None if not found."""
    name = "nastrn.exe" if platform.system() == "Windows" else "nastrn"
    exe = _DATA_DIR / "bin" / name
    return exe if exe.exists() else None


def get_rfdir() -> Path | None:
    """Return path to the bundled rigid format directory, or None if not found."""
    rf = _DATA_DIR / "rf"
    return rf if rf.is_dir() and any(rf.iterdir()) else None
