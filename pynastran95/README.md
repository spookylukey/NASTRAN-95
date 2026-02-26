# pynastran95

Python wrapper for **NASTRAN-95**, the NASA Structural Analysis System.

Run finite element analyses from Python, with results returned as NumPy arrays.

## Features

- **Two execution modes**: subprocess (robust) or f2py (in-process via fork)
- **Automatic output parsing**: displacements, stresses, eigenvalues → NumPy arrays
- **Full NASTRAN-95 capability**: all 13 rigid format solution types
- **Simple API**: `pynastran95.run(input_deck)` → structured results
- **f2py extension**: direct Fortran binding with COMMON block access
- **Compatible with pyNastran** for BDF model generation

## Quick Start

```python
import pynastran95

# Run a static analysis
result = pynastran95.run("inp_clean/d01011a.inp")

if result.completed:
    disp = result.displacements[0]
    print(f"Max displacement: {disp.translations.max():.6e}")
```

See [docs/getting-started.md](docs/getting-started.md) for full documentation.

## Installation

First, build the NASTRAN-95 Fortran binary (requires gfortran):

```bash
cd build
make          # compiles ~1850 Fortran sources (~60 seconds)
cd ..
```

Then install the Python package:

```bash
cd pynastran95
uv venv
uv pip install -e ".[dev]"
```

Optionally, build the f2py extension for in-process execution:

```bash
.venv/bin/python -m pynastran95._fortran.build_ext
```

## Testing

```bash
.venv/bin/python -m pytest tests/ -v
```

## Architecture

```
pynastran95/
├── src/pynastran95/
│   ├── __init__.py          # Public API
│   ├── runner.py            # Subprocess & f2py runners
│   ├── parser.py            # F06 output parser
│   ├── models.py            # Result dataclasses
│   └── _fortran/            # f2py extension
│       ├── build_ext.py     # Build script
│       ├── nastran_entry.f   # Fortran wrapper subroutine
│       ├── exit_override.c   # EXIT/STOP interception via fork()
│       └── _nastran_core*.so # Built extension (after build_ext)
├── tests/
│   ├── test_parser.py       # Output parser tests
│   ├── test_runner.py       # Subprocess runner tests
│   ├── test_f2py.py         # f2py extension tests
│   └── test_pynastran_integration.py  # End-to-end with analytical verification
└── docs/
    ├── getting-started.md   # User guide
    └── api-reference.md     # API documentation
```
