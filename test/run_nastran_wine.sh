#!/bin/bash
# Run the cross-compiled NASTRAN Windows exe under Wine.
# Usage: ./run_nastran_wine.sh <input_file> [output_file]
#
# Prerequisites:
#   sudo apt install gfortran-mingw-w64-x86-64 wine
#   cd ../build && make nastrn.exe
#
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

INPUT="$1"
if [ -z "$INPUT" ]; then
    echo "Usage: $0 <input_file> [output_file]" >&2
    exit 1
fi

BASE=$(basename "$INPUT" .inp)
OUTPUT="${2:-${BASE}.wine.out}"
SCRATCH="$SCRIPT_DIR/scratch_wine_${BASE}"

mkdir -p "$SCRATCH"

EXE="$REPO_ROOT/build/nastrn.exe"
if [ ! -f "$EXE" ]; then
    echo "Error: $EXE not found. Run 'make nastrn.exe' in build/ first." >&2
    exit 1
fi

# Wine maps Z:\ to Linux root filesystem
WIN_RF="Z:$(realpath "$REPO_ROOT/rf_clean")"
WIN_SCRATCH="Z:$(realpath "$SCRATCH")"

export RFDIR="$WIN_RF"
export DBMEM=12000000
export OCMEM=2000000
export DIRCTY="$WIN_SCRATCH"
export LOGNM="${WIN_SCRATCH}/${BASE}.log"
export NPTPNM="${WIN_SCRATCH}/${BASE}.nptp"
export PLTNM="NUL"
export DICTNM="${WIN_SCRATCH}/${BASE}.dic"
export PUNCHNM="NUL"
export OPTPNM="NUL"
export SOF1="NUL"
export SOF2="NUL"

for i in $(seq 11 23); do
    export FTN${i}="${WIN_SCRATCH}/ftn${i}"
done

export WINEDEBUG=-all

wine "$EXE" < "$INPUT" > "$OUTPUT" 2>&1
RC=$?

# Check results
if grep -q "END OF JOB" "$OUTPUT"; then
    echo "PASS: $BASE (END OF JOB found)"
elif grep -q "JOB TERMINATED" "$OUTPUT"; then
    echo "PASS: $BASE (JOB TERMINATED found)"
else
    echo "FAIL: $BASE"
    grep -i "error\|fatal" "$OUTPUT" | head -5
fi

exit $RC
