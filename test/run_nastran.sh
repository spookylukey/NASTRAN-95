#!/bin/bash
# Run a NASTRAN test case
# Usage: ./run_nastran.sh <input_file> [output_file]
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

INPUT="$1"
BASE=$(basename "$INPUT" .inp)
OUTPUT="${2:-${BASE}.test.out}"
SCRATCH="$SCRIPT_DIR/scratch_${BASE}"

mkdir -p "$SCRATCH"

export RFDIR="$REPO_ROOT/rf_clean"
export DBMEM=12000000
export OCMEM=2000000
export DIRCTY="$SCRATCH"
export LOGNM="$SCRATCH/${BASE}.log"
export NPTPNM="$SCRATCH/${BASE}.nptp"
export PLTNM="/dev/null"
export DICTNM="$SCRATCH/${BASE}.dic"
export PUNCHNM="/dev/null"
export OPTPNM="/dev/null"
export SOF1="/dev/null"
export SOF2="/dev/null"

for i in $(seq 11 23); do
    export FTN${i}="${SCRATCH}/ftn${i}"
done

"$REPO_ROOT/build/nastrn" < "$INPUT" > "$OUTPUT" 2>&1
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
