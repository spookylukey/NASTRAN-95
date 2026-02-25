# Getting Started with pynastran95

pynastran95 is a Python wrapper for **NASTRAN-95**, the original NASA Structural
Analysis System. It lets you run finite element analyses directly from Python
and access results as NumPy arrays.

## Prerequisites

- Python 3.11+
- gfortran (for building the Fortran extension)
- A built NASTRAN-95 binary (see the main repo README)

## Installation

```bash
cd pynastran95
uv venv
uv pip install -e ".[dev]"
```

Optionally, install pyNastran for BDF model building:

```bash
uv pip install pyNastran
```

## Quick Start

### Running an Existing Input Deck

The simplest way to use pynastran95 is to run an existing NASTRAN input file:

```python
import pynastran95

# Run a demo problem
result = pynastran95.run("inp_clean/d01011a.inp")

# Check if it completed successfully
print(f"Completed: {result.completed}")
print(f"Wall time: {result.wall_time:.1f} seconds")

# Access displacements
for disp in result.displacements:
    print(f"Subcase {disp.subcase}: {len(disp.node_ids)} nodes")
    print(f"  Max displacement: {disp.translations.max():.6e}")

# Access eigenvalues (for modal analysis)
if result.eigenvalues is not None:
    for i, freq in enumerate(result.eigenvalues.frequencies):
        print(f"  Mode {i+1}: {freq:.3f} Hz")
```

### Building a Model from Scratch

You can pass a NASTRAN input deck as a string:

```python
import pynastran95
import numpy as np

# A simple cantilever beam
deck = """
ID    CANTILEVER,EXAMPLE
APP   DISPLACEMENT
SOL   1,1
TIME  10
CEND
TITLE    = CANTILEVER BEAM
   SPC = 1
  LOAD = 1
  DISPLACEMENT = ALL
  SPCFORCES = ALL
  ELSTRESS = ALL
BEGIN BULK
GRID    1               0.0     0.0     0.0
GRID    2              10.0     0.0     0.0
GRID    3              20.0     0.0     0.0
GRID    4              30.0     0.0     0.0
GRID    5              40.0     0.0     0.0
GRID    6              50.0     0.0     0.0
CBAR    1       1       1       2       0.0     0.0     1.0
CBAR    2       1       2       3       0.0     0.0     1.0
CBAR    3       1       3       4       0.0     0.0     1.0
CBAR    4       1       4       5       0.0     0.0     1.0
CBAR    5       1       5       6       0.0     0.0     1.0
PBAR    1       1       1.0     1.0     1.0     2.0
MAT1    1       30.0+6          .3      .283
SPC1    1       123456  1
FORCE   1       6       0       1000.0  0.0     0.0     1.0
ENDDATA
"""

result = pynastran95.run(deck)

if result.completed:
    disp = result.displacements[0]
    # Get tip deflection (node 6)
    idx = np.where(disp.node_ids == 6)[0][0]
    print(f"Tip deflection: {disp.translations[idx, 2]:.6e} in")
```

### Using pyNastran for Model Building

pyNastran provides a Python API for building BDF models. Here's an example:

```python
from io import StringIO
from pyNastran.bdf.bdf import BDF
import pynastran95
import numpy as np

# Build model
model = BDF()

# Material: steel
model.add_mat1(mid=1, E=30.0e6, G=None, nu=0.3, rho=0.283)

# Property: beam
model.add_pbar(pid=1, mid=1, A=1.0, i1=1.0, i2=1.0, j=2.0)

# Nodes
for i in range(11):
    model.add_grid(i + 1, [i * 10.0, 0.0, 0.0])

# Elements
for i in range(10):
    model.add_cbar(i + 1, 1, [i + 1, i + 2], [0.0, 0.0, 1.0])

# Boundary conditions
model.add_spc1(1, '123456', [1])

# Load
model.add_force(1, 11, 1.0, [0.0, 0.0, 1000.0])

# Executive control (NASTRAN-95 format)
model.executive_control_lines = [
    'SOL 1,1',
    'APP DISPLACEMENT',
    'TIME 10',
    'CEND',
]

# Case control
case = model.create_subcases(0)
case.add_integer_type('SPC', 1)
case.add_integer_type('LOAD', 1)
case.add_result_type('DISPLACEMENT', 'ALL')

# Write to string and run
buf = StringIO()
model.write_bdf(buf)
result = pynastran95.run(buf.getvalue())

if result.completed:
    disp = result.displacements[0]
    idx = np.where(disp.node_ids == 11)[0][0]
    print(f"Tip Z-deflection: {disp.translations[idx, 2]:.6e} in")
```

## Execution Modes

pynastran95 supports two execution modes:

### Subprocess Mode (default)

Runs the compiled `nastrn` binary as a subprocess. This is the most robust
mode and requires no additional build steps beyond compiling the Fortran
binary.

```python
result = pynastran95.run(deck, mode="subprocess")
```

### f2py Mode

Calls the Fortran solver directly via a Python C extension built with f2py.
Requires building the extension first:

```bash
python -m pynastran95._fortran.build_ext
```

Then:

```python
result = pynastran95.run(deck, mode="f2py")
```

The f2py mode also exposes NASTRAN's internal COMMON blocks:

```python
from pynastran95._fortran import get_core
core = get_core()

# Access the SYSTEM common block
print(core.system.isystm[:10])

# Access the DBM common block  
print(core.dbm.lenopc)
```

## Result Objects

### NastranResult

The main result object returned by `run()`:

| Attribute | Type | Description |
|-----------|------|-------------|
| `completed` | `bool` | Whether NASTRAN finished successfully |
| `returncode` | `int` | Process return code |
| `output` | `str` | Full printed output (F06-style) |
| `log` | `str` | Log file contents |
| `displacements` | `list[DisplacementResult]` | Parsed displacement results |
| `stresses` | `list[StressResult]` | Parsed stress results |
| `eigenvalues` | `EigenvalueResult \| None` | Eigenvalue results (modal analysis) |
| `wall_time` | `float` | Wall clock time in seconds |

### DisplacementResult

| Attribute | Type | Description |
|-----------|------|-------------|
| `node_ids` | `NDArray[int32]` | Grid point IDs |
| `translations` | `NDArray[float64]` | (N, 3) array of T1, T2, T3 |
| `rotations` | `NDArray[float64]` | (N, 3) array of R1, R2, R3 |
| `subcase` | `int` | Subcase ID |

### EigenvalueResult

| Attribute | Type | Description |
|-----------|------|-------------|
| `mode_numbers` | `NDArray[int32]` | Mode numbers |
| `eigenvalues` | `NDArray[float64]` | Eigenvalues (rad/s)² |
| `frequencies` | `NDArray[float64]` | Natural frequencies (Hz) |
| `generalized_mass` | `NDArray[float64]` | Generalized masses |
| `generalized_stiffness` | `NDArray[float64]` | Generalized stiffnesses |

### StressResult

| Attribute | Type | Description |
|-----------|------|-------------|
| `element_ids` | `NDArray[int32]` | Element IDs |
| `element_type` | `str` | Element type ("CROD", "CSHEAR", "CQDMEM", etc.) |
| `stresses` | `dict[str, NDArray[float64]]` | Stress components by name |
| `subcase` | `int` | Subcase ID |

## Analysis Types

NASTRAN-95 supports these rigid format solution types:

| SOL | Description | Example Input |
|-----|-------------|---------------|
| 1 | Static Analysis | `d01xxx` demos |
| 2 | Static with Inertia Relief | `d02xxx` demos |
| 3 | Normal Modes | `d03xxx` demos |
| 4 | Differential Stiffness | `d04xxx` demos |
| 5 | Buckling | `d05xxx` demos |
| 6 | Piecewise Linear Static | `d06xxx` demos |
| 7 | Direct Complex Eigenvalues | `d07xxx` demos |
| 8 | Direct Frequency Response | `d08xxx` demos |
| 9 | Direct Transient Response | `d09xxx` demos |
| 10 | Modal Complex Eigenvalues | `d10xxx` demos |
| 11 | Modal Frequency Response | `d11xxx` demos |
| 12 | Modal Transient Response | `d12xxx` demos |
| 13 | Normal Modes with Diff. Stiffness | `d13xxx` demos |

See the `inp_clean/` directory for 132 working demo problems.

## Tips

1. **Input format**: NASTRAN-95 uses 80-column fixed-format card images.
   Each field is 8 characters wide. See the User's Manual (`um/` directory)
   for format details.

2. **Memory**: The default `DBMEM=12000000` and `OCMEM=2000000` (words)
   work for most problems. Increase for large models:
   ```python
   runner = pynastran95.NastranRunner(dbmem=24_000_000, ocmem=4_000_000)
   ```

3. **Timeout**: Long-running analyses may need a longer timeout:
   ```python
   result = pynastran95.run(deck, timeout=600.0)  # 10 minutes
   ```

4. **Full output**: The complete F06-style output is in `result.output`.
   This is useful for debugging or for accessing data that the parser
   doesn't yet extract.

5. **Comparing results**: Use `result.output` to compare against reference
   output in the `demoout/` directory.
