C     NASTRAN-95 ENTRY POINT FOR PYTHON WRAPPER
C     This subroutine replaces the PROGRAM NASTRN so it can be
C     called from Python via f2py. It reads configuration from
C     environment variables (same as the original program) and
C     runs the NASTRAN solver.
C
C     INPUTF: Path to input file (will be opened as unit 5)
C     OUTPUTF: Path to output file (will be opened as unit 6)
C     IRETURN: Return code (0=success, nonzero=error)
C
C
C     PUBLIC API: Runs NASTRAN in a forked child process.
C     This is safe because EXIT/STOP in the child won't kill Python.
C
      SUBROUTINE NASTRAN_SOLVE(INPUTF, OUTPUTF, IRETURN)
Cf2py intent(in) inputf
Cf2py intent(in) outputf
Cf2py intent(out) ireturn
      CHARACTER*(*) INPUTF
      CHARACTER*(*) OUTPUTF
      INTEGER IRETURN
      CALL NASTRAN_SOLVE_FORKED(INPUTF, OUTPUTF, IRETURN)
      RETURN
      END
C
C     Expose selected COMMON blocks to Python via f2py.
C     Only integer/real blocks are exposed here; CHARACTER*4096
C     blocks (DOSNAM, DSNAME, SOFDSN) are deliberately excluded
C     because f2py cannot represent them correctly and the
C     mismatched layout corrupts shared COMMON block memory.
C
      SUBROUTINE F2PY_COMMON_HELPER()
      INTEGER         SPERLK
      COMMON / LSTADD / LASTAD
      COMMON / SYSTEM / ISYSTM(94),SPERLK
      COMMON / LOGOUT / LOUT
      COMMON / RESDIC / IRDICT, IROPEN
      COMMON / ZZZZZZ / IZ(14000000)
      COMMON / DBM    / IDBBAS, IDBFRE, IDBDIR, INDBAS, INDCLR, INDCBP
     &,                 NBLOCK, LENALC, IOCODE, IFILEX, NAME,   MAXALC
     &,                 MAXBLK, MAXDSK, IDBLEN, IDBADR, IBASBF, INDDIR
     &,                 NUMOPN, NUMCLS, NUMWRI, NUMREA, LENOPC
      RETURN
      END
