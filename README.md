# NASTRAN-95

NASTRAN has been released under the
[NASA Open Source Agreement version 1.3](https://github.com/nasa/NASTRAN-95/raw/master/NASA%20Open%20Source%20Agreement-NASTRAN%2095.doc).

NASTRAN is the NASA Structural Analysis System, a finite element analysis
program (FEA) completed in the early 1970's. It was the first of its kind and
opened the door to computer-aided engineering. Subsections of a design can be
modeled and then larger groupings of these elements can again be modeled.
NASTRAN can handle elastic stability analysis, complex eigenvalues for
vibration and dynamic stability analysis, dynamic response for transient and
steady state loads, and random excitation, and static response to concentrated
and distributed loads, thermal expansion, and enforced deformations.

NOTE: There is no technical support available for this software.

## Building from Source

### Prerequisites

- **gfortran** (tested with 13.3.0 on Ubuntu 24.04; other versions may work)
- **GNU make** or just a shell — no Makefile is provided; the build is a
  straightforward compile-and-link
- x86-64 Linux (little-endian). Other architectures have not been tested.

On Debian/Ubuntu:

```bash
sudo apt install gfortran
```

### Quick Build

The `build/` directory contains pre-cleaned, patched source files and a
compiled executable. To rebuild from scratch:

```bash
cd build

# Compile all Fortran sources (takes ~60 seconds)
FLAGS="-std=legacy -fno-range-check -w -fallow-argument-mismatch -fallow-invalid-boz -fno-automatic"
for f in src_mis/*.f src_mds/*.f src_bd/*.f src_bin/*.f stubs.f; do
    gfortran -c $FLAGS "$f"
done

# Link (exclude chkfil.o — it has its own PROGRAM main)
ls *.o | grep -v chkfil.o | xargs gfortran $FLAGS -o nastrn
```

The executable is written to `build/nastrn` (~12 MB).

### Compiler Flags Explained

| Flag | Purpose |
|------|--------|
| `-std=legacy` | Accept Fortran 77 extensions (Hollerith constants, etc.) |
| `-fno-range-check` | Allow integer overflow in constants |
| `-fallow-argument-mismatch` | Accept mismatched subroutine argument types |
| `-fallow-invalid-boz` | Accept BOZ constants in non-DATA contexts |
| `-fno-automatic` | **Critical.** Use static allocation for local variables so they retain values between calls, as Fortran 66/77 assumed |
| `-w` | Suppress warnings (there are thousands) |

`-fno-automatic` is the most important flag. Without it, subroutine-local
variables initialized by DATA statements lose their values between calls,
causing widespread silent data corruption.

### Source Patches

Six source files required changes from the original repository code to compile
and run correctly with gfortran. The patched versions live in `build/src_*/`.

| File | Change | Reason |
|------|--------|--------|
| `src_mis/endsys.f` | Added `EXTERNAL LINK` | `LINK` is a gfortran intrinsic; declaration prevents conflict with the NASTRAN subroutine |
| `src_mis/pexit.f` | Added `EXTERNAL LINK` | Same as above |
| `src_mis/sofut.f` | Added `EXTERNAL RENAME` | `RENAME` is a gfortran intrinsic; declaration prevents conflict |
| `src_mis/xdcode.f` | Replaced `READ(TEMP,'(80A1)') ICHAR` with EQUIVALENCE-based character loop | gfortran's A1 formatted read treats comma as a field separator, breaking rigid format file parsing |
| `src_mds/cputim.f` | Rewrote to call `ETIME` as a function | gfortran provides `ETIME` as an intrinsic function, not the subroutine the original code expected |
| `src_mds/nastim.f` | Same `ETIME` fix | Same reason |
| `src_mds/dbmdia.f` | Changed `DATA SCRATCH / 'SCRA','TCHX' /` to use `4H` Hollerith | CHARACTER literals in DATA for an INTEGER array don't work; Hollerith does |
| `stubs.f` | New file with stub subroutines `Q8SHPD`, `T6SHPD`, `JACOBD` | Referenced but not defined in COSMIC/NASTRAN source |

### Cleaning the Original Sources

The original source files in `mis/`, `mds/`, `bd/`, and `bin/` have DOS line
endings (CRLF) and sometimes DOS EOF characters (`0x1A`). The `build/src_*/`
directories contain cleaned copies with these stripped. If you need to
re-clean:

```bash
for f in mis/*.f; do
    sed 's/\r//g; s/\x1a//g' "$f" > "build/src_mis/$(basename $f)"
done
# Repeat for mds/, bd/, bin/
```

The rigid format files in `rf/` also need cleaning. Cleaned copies are in
`rf_clean/`.

## Running NASTRAN

### Environment Variables

NASTRAN reads its configuration from environment variables (not command-line
arguments). Input is read from **stdin** and printed output goes to **stdout**.

**Required variables:**

| Variable | Description |
|----------|------------|
| `RFDIR` | Path to directory containing rigid format files |
| `DBMEM` | Database memory allocation in words (e.g., `12000000`) |
| `OCMEM` | Open-core memory allocation in words (e.g., `2000000`) |
| `DIRCTY` | Scratch directory for temporary files |
| `LOGNM` | Path for log file output |
| `NPTPNM` | Path for new problem tape (checkpoint) file |
| `DICTNM` | Path for checkpoint dictionary file |
| `PLTNM` | Path for plot file (`/dev/null` if not needed) |
| `PUNCHNM` | Path for punch file (`/dev/null` if not needed) |
| `OPTPNM` | Path for old problem tape (`/dev/null` for new problems) |
| `SOF1` | Substructure operating file 1 (`/dev/null` if not needed) |
| `SOF2` | Substructure operating file 2 (`/dev/null` if not needed) |
| `FTN11`–`FTN23` | Paths for Fortran scratch units (one file per unit) |

### Running a Test Case

The simplest way to run a problem:

```bash
# Set up environment
export RFDIR=/path/to/nastran/rf_clean
export DBMEM=12000000
export OCMEM=2000000

# Create scratch directory
mkdir -p /tmp/nastran_scratch
export DIRCTY=/tmp/nastran_scratch

# Output files
export LOGNM=/tmp/nastran_scratch/run.log
export NPTPNM=/tmp/nastran_scratch/run.nptp
export DICTNM=/tmp/nastran_scratch/run.dic
export PLTNM=/dev/null
export PUNCHNM=/dev/null
export OPTPNM=/dev/null
export SOF1=/dev/null
export SOF2=/dev/null

# Scratch units
for i in $(seq 11 23); do
    export FTN${i}=/tmp/nastran_scratch/ftn${i}
done

# Run (input on stdin, output on stdout)
./build/nastrn < inp_clean/d01011a.inp > output.out
```

A helper script `test/run_nastran.sh` automates this. Usage:

```bash
cd test
./run_nastran.sh ../inp_clean/d01011a.inp
```

### Demo Problems

The `inp/` directory contains 132 demo problems covering static analysis,
normal modes, buckling, frequency response, transient response, and more.
Cleaned (no CRLF) copies are in `inp_clean/`. Reference output is in
`demoout/`. All 132 demo problems run successfully.

| Prefix | Rigid Format | Analysis Type |
|--------|-------------|---------------|
| `d01xxx` | 1 | Static Analysis |
| `d02xxx` | 2 | Static Analysis with Inertia Relief |
| `d03xxx` | 3 | Normal Modes |
| `d04xxx` | 4 | Differential Stiffness |
| `d05xxx` | 5 | Buckling |
| `d06xxx` | 6 | Piecewise Linear Static |
| `d07xxx` | 7 | Direct Complex Eigenvalues |
| `d08xxx` | 8 | Direct Frequency Response |
| `d09xxx` | 9 | Direct Transient Response |
| `d10xxx` | 10 | Modal Complex Eigenvalues |
| `d11xxx` | 11 | Modal Frequency Response |
| `d12xxx` | 12 | Modal Transient Response |
| `d13xxx` | 13 | Normal Modes with Differential Stiffness |

Descriptions of each problem are in the corresponding `inp/*.txt` files.

### Input Format

NASTRAN input is 80-column fixed-format card images. A typical input deck has
three sections:

1. **Executive Control** — selects solution type (`SOL`), time limit, etc.
2. **Case Control** — selects loads, constraints, and output requests
3. **Bulk Data** — defines geometry, elements, materials, loads, and constraints

See the User's Manual text files in `um/` for details on each section.

## Repository Layout

```
mis/          Original NASTRAN source — core routines (1674 files)
mds/          Original NASTRAN source — machine-dependent (130 files)
bd/           Original NASTRAN source — block data (40 files)
bin/          Original NASTRAN source — main program (1 file)
build/        Build directory with cleaned/patched sources and object files
  src_mis/    Cleaned + patched MIS sources
  src_mds/    Cleaned + patched MDS sources
  src_bd/     Cleaned block data sources
  src_bin/    Cleaned main program
  stubs.f     Stub subroutines for missing externals
  nastrn      Compiled executable (x86-64 Linux ELF)
  *.COM       Fortran INCLUDE files (COMMON block definitions)
rf/           Rigid format files (original, with CRLF)
rf_clean/     Rigid format files (cleaned)
inp/          Demo problem input decks (132 problems, with CRLF)
inp_clean/    Demo problem input decks (cleaned)
demoout/      Reference output for demo problems
um/           User's Manual text files
test/         Test runner and scratch area
```
