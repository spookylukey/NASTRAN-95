# API Reference

## Module: pynastran95

### `pynastran95.run(input_data, *, timeout=300.0, mode="subprocess", **kwargs)`

Convenience function to run a NASTRAN analysis.

**Parameters:**
- `input_data` (`str | Path`): Path to input file or input deck string.
- `timeout` (`float | None`): Maximum wall time in seconds. Default: 300.
- `mode` (`"subprocess" | "f2py"`): Execution mode. Default: `"subprocess"`.
- `**kwargs`: Additional arguments passed to `NastranRunner`.

**Returns:** `NastranResult`

### `pynastran95.NastranRunner`

```python
class NastranRunner(
    executable: str | Path | None = None,
    rfdir: str | Path | None = None,
    dbmem: int = 12_000_000,
    ocmem: int = 2_000_000,
    scratch_root: str | Path | None = None,
    mode: Literal["subprocess", "f2py"] = "subprocess",
)
```

NASTRAN-95 analysis runner. Create once and reuse for multiple runs.

#### `NastranRunner.run(input_data, *, timeout=300.0, cleanup=True)`

**Parameters:**
- `input_data` (`str | Path`): Input file path or deck string.
- `timeout` (`float | None`): Max wall time in seconds.
- `cleanup` (`bool`): Remove scratch files after run. Default: True.

**Returns:** `NastranResult`

## Data Models

### `pynastran95.NastranResult`

```python
@dataclass
class NastranResult:
    returncode: int
    output: str
    log: str = ""
    completed: bool = False
    displacements: list[DisplacementResult] = field(default_factory=list)
    stresses: list[StressResult] = field(default_factory=list)
    eigenvalues: EigenvalueResult | None = None
    wall_time: float = 0.0
```

### `pynastran95.DisplacementResult`

```python
@dataclass
class DisplacementResult:
    node_ids: NDArray[np.int32]       # Grid point IDs
    translations: NDArray[np.float64] # Shape (N, 3): T1, T2, T3
    rotations: NDArray[np.float64]    # Shape (N, 3): R1, R2, R3
    subcase: int = 1
```

### `pynastran95.EigenvalueResult`

```python
@dataclass
class EigenvalueResult:
    mode_numbers: NDArray[np.int32]
    eigenvalues: NDArray[np.float64]           # (rad/s)^2
    frequencies: NDArray[np.float64]           # Hz
    generalized_mass: NDArray[np.float64]
    generalized_stiffness: NDArray[np.float64]
```

### `pynastran95.StressResult`

```python
@dataclass
class StressResult:
    element_ids: NDArray[np.int32]
    element_type: str                          # "CROD", "CSHEAR", etc.
    stresses: dict[str, NDArray[np.float64]]   # component -> values
    subcase: int = 1
```

Stress component keys by element type:

| Element Type | Components |
|-------------|------------|
| `CROD` | `axial`, `torsion` |
| `CSHEAR` | `max_shear`, `avg_shear` |
| `CQDMEM` | `normal_x`, `normal_y`, `shear_xy`, `major`, `minor`, `max_shear` |
| `CTRMEM` | Same as CQDMEM |

## f2py Extension

### Building

```bash
python -m pynastran95._fortran.build_ext
```

This compiles all NASTRAN Fortran sources and builds a Python C extension
module. Takes about 60 seconds.

### `pynastran95._fortran.is_built()`

Returns `True` if the f2py extension has been built.

### `pynastran95._fortran.get_core()`

Returns the `_nastran_core` extension module with:
- `nastran_solve(inputf, outputf)` → `ireturn` (int)
- COMMON block objects: `system`, `dbm`, `lstadd`, `logout`, `resdic`, etc.

## Parser Functions

Low-level functions for parsing NASTRAN output text:

```python
from pynastran95.parser import (
    parse_displacements,    # → list[DisplacementResult]
    parse_eigenvalues,      # → EigenvalueResult | None
    parse_rod_stresses,     # → list[StressResult]
    parse_shear_stresses,   # → list[StressResult]
    parse_membrane_stresses,# → list[StressResult]
    is_completed,           # → bool
)
```
