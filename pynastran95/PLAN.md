# pynastran95 - Python Wrapper for NASTRAN-95

## Implementation Status

### Phase 1: Project Setup ✅
- [x] Python project with uv, pytest, ruff, pyright
- [x] pyproject.toml, pre-commit config

### Phase 2: Subprocess-based Runner ✅
- [x] Python wrapper that sets up env, creates scratch dir, runs nastrn binary
- [x] Capture and return stdout output
- [x] Tests: d01011a (static), d03011a (eigenvalue), string input, convenience function

### Phase 3: f2py Fortran Extension ✅
- [x] Created nastran_entry.f wrapper subroutine replacing PROGRAM
- [x] exit_override.c with fork()-based execution (handles EXIT/STOP)
- [x] build_ext.py script compiles all 1843 NASTRAN objects + f2py
- [x] Tests: static analysis, eigenvalue, convenience function, COMMON blocks

### Phase 4: Output Parsing ✅
- [x] Displacements (tested against reference d01011a output)
- [x] Eigenvalues (tested against reference d03011a output)
- [x] Membrane stresses (CQDMEM, CTRMEM)
- [x] Shear panel stresses (CSHEAR)
- [x] Rod stresses (CROD)

### Phase 5: Integration Testing ✅
- [x] Cantilever beam built manually, verified against PL³/3EI analytical solution
- [x] Same test via f2py mode
- [x] 18 total tests, all passing

### Phase 6: Documentation ✅
- [x] Getting started guide (docs/getting-started.md)
- [x] API reference (docs/api-reference.md)
- [x] README.md

## Architecture

NASTRAN-95 is a monolithic Fortran 77 batch program. Two approaches:

1. **Subprocess mode**: Run the `nastrn` binary with stdin/stdout redirection.
   Robust, works always.

2. **f2py mode**: A Fortran wrapper subroutine (`nastran_entry.f`) replicates
   the PROGRAM logic. The C file `exit_override.c` uses `fork()` to run NASTRAN
   in a child process, preventing EXIT/STOP from killing Python. All 1843
   NASTRAN source files are compiled and linked into a single `.so` via f2py.

Both modes produce identical results. The parser extracts structured data
(displacements, stresses, eigenvalues) from the F06-style text output.
