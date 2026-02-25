"""NASTRAN-95 Fortran extension module.

This module provides direct access to the NASTRAN-95 solver via f2py.
The extension must be built first using:

    python -m pynastran95._fortran.build_ext

Once built, the _nastran_core module provides:
    - nastran_solve(input_file, output_file) -> return_code
    - Access to COMMON blocks (system, dbm, etc.)
"""

from __future__ import annotations

import importlib
from pathlib import Path


def is_built() -> bool:
    """Check if the f2py extension has been built."""
    fortran_dir = Path(__file__).parent
    so_files = list(fortran_dir.glob("_nastran_core*.so"))
    return len(so_files) > 0


def get_core():
    """Import and return the _nastran_core extension module.

    Raises ImportError if not built.
    """
    import sys

    fortran_dir = str(Path(__file__).parent)
    if fortran_dir not in sys.path:
        sys.path.insert(0, fortran_dir)
    return importlib.import_module("_nastran_core")
