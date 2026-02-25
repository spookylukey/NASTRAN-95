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
C     IMPLEMENTATION: Called in the forked child process.
C     If EXIT/STOP occurs, the child terminates cleanly.
C
      SUBROUTINE NASTRAN_SOLVE_IMPL(INPUTF, OUTPUTF, IRETURN)
      CHARACTER*(*) INPUTF
      CHARACTER*(*) OUTPUTF
      INTEGER IRETURN
C
      CHARACTER*80    VALUE
      CHARACTER*5     TMP
      INTEGER         SPERLK
      REAL            SYSTM(94)
      COMMON / LSTADD / LASTAD
      COMMON / SYSTEM / ISYSTM(94),SPERLK
      COMMON / SOFDSN / SDSN(10)
      COMMON / LOGOUT / LOUT
      COMMON / RESDIC / IRDICT, IROPEN
      COMMON / ZZZZZZ / IZ(14000000)
      COMMON / DBM    / IDBBAS, IDBFRE, IDBDIR, INDBAS, INDCLR, INDCBP
     &,                 NBLOCK, LENALC, IOCODE, IFILEX, NAME,   MAXALC
     &,                 MAXBLK, MAXDSK, IDBLEN, IDBADR, IBASBF, INDDIR
     &,                 NUMOPN, NUMCLS, NUMWRI, NUMREA, LENOPC
      INCLUDE 'NASNAMES.COM'
      CHARACTER*80    SDSN
      EQUIVALENCE    ( ISYSTM, SYSTM )
C
      IRETURN = 0
      LENOPC = 14000000
C
C     REDIRECT STDIN/STDOUT TO FILES
C     Unit 5 = stdin for NASTRAN, Unit 6 = stdout for NASTRAN
C
      OPEN(5, FILE=INPUTF, STATUS='OLD', ERR=900)
      OPEN(6, FILE=OUTPUTF, STATUS='UNKNOWN', ERR=900)
C
C     SAVE STARTING CPU TIME AND WALL CLOCK TIME IN /SYSTEM/
C
      ISYSTM(18) = 0
      CALL SECOND (SYSTM(18))
      CALL WALTIM (ISYSTM(32))
C
C     EXECUTE NASTRAN SUPER LINK
C
      LEN = 80
      VALUE = ' '
      CALL BTSTRP
      CALL GETENV ( 'DBMEM', VALUE )
      READ ( VALUE, *, ERR=900 ) IDBLEN
      CALL GETENV ( 'OCMEM', VALUE )
      READ ( VALUE, *, ERR=900 ) IOCMEM
      IF ( IOCMEM .LE. LENOPC ) GO TO 10
      PRINT *,' LARGEST VALUE FOR OPEN CORE ALLOWED IS:',LENOPC
      IRETURN = -61
      GO TO 999
10    IF ( IDBLEN .NE. 0 ) IDBLEN = LENOPC - IOCMEM
      LASTAD = LOCFX( IZ( IOCMEM ) )
      IF ( IDBLEN .NE. 0 ) IDBADR = LOCFX( IZ( IOCMEM+1 ) )
      LENOPC = IOCMEM
      CALL DBMINT
      LOUT   = 3
      IRDICT = 4
      SPERLK = 1
      ISYSTM(11) = 1
      VALUE = ' '
      CALL GETENV ( 'RFDIR',  RFDIR  )
      VALUE = ' '
      CALL GETENV ( 'DIRCTY', DIRTRY )
      LEN = INDEX( DIRTRY, ' ' ) - 1
      DO 20 I = 1, 90
      IF ( I .LE. 9 ) WRITE ( TMP, 901 ) I
      IF ( I .GT. 9 ) WRITE ( TMP, 902 ) I
901   FORMAT('scr',I1)
902   FORMAT('scr',I2)
      DSNAMES( I ) = DIRTRY(1:LEN)//'/'//TMP
20    CONTINUE
      CALL GETENV ( 'LOGNM', LOG )
      DSNAMES(3) = LOG
      CALL GETENV ( 'OPTPNM', OPTP )
      DSNAMES(7)  = OPTP
      CALL GETENV ( 'NPTPNM', NPTP )
      DSNAMES(8)  = NPTP
      CALL GETENV ( 'FTN11', OUT11 )
      DSNAMES(11) = OUT11
      CALL GETENV ( 'FTN12', IN12 )
      DSNAMES(12) = IN12
      CALL GETENV ( 'FTN13', VALUE )
      DSNAMES(13) = VALUE
      CALL GETENV ( 'FTN14', VALUE )
      DSNAMES(14) = VALUE
      CALL GETENV ( 'FTN15', VALUE )
      DSNAMES(15) = VALUE
      CALL GETENV ( 'FTN16', VALUE )
      DSNAMES(16) = VALUE
      CALL GETENV ( 'FTN17', VALUE )
      DSNAMES(17) = VALUE
      CALL GETENV ( 'FTN18', VALUE )
      DSNAMES(18) = VALUE
      CALL GETENV ( 'FTN19', VALUE )
      DSNAMES(19) = VALUE
      CALL GETENV ( 'FTN20', VALUE )
      DSNAMES(20) = VALUE
      CALL GETENV ( 'FTN21', VALUE )
      DSNAMES(21) = VALUE
      CALL GETENV ( 'PLTNM', PLOT )
      DSNAMES(10) = PLOT
      CALL GETENV ( 'DICTNM', DIC )
      DSNAMES(4) = DIC
      CALL GETENV ( 'PUNCHNM', PUNCH )
      DSNAMES(1) = PUNCH
      CALL GETENV ( 'SOF1', VALUE )
      SDSN(1) = VALUE
      CALL GETENV ( 'SOF2', VALUE )
      SDSN(2) = VALUE
      CALL GETENV ( 'SOF3', VALUE )
      SDSN(3) = VALUE
      CALL GETENV ( 'SOF4', VALUE )
      SDSN(4) = VALUE
      CALL GETENV ( 'SOF5', VALUE )
      SDSN(5) = VALUE
      CALL GETENV ( 'SOF6', VALUE )
      SDSN(6) = VALUE
      CALL GETENV ( 'SOF7', VALUE )
      SDSN(7) = VALUE
      CALL GETENV ( 'SOF8', VALUE )
      SDSN(8) = VALUE
      CALL GETENV ( 'SOF9', VALUE )
      SDSN(9) = VALUE
      CALL GETENV ( 'SOF10', VALUE )
      SDSN(10) = VALUE
      OPEN (  3, FILE=DSNAMES(3) ,STATUS='UNKNOWN')
      IF ( DSNAMES(11) .NE. 'none' )
     & OPEN ( 11, FILE=DSNAMES(11),STATUS='UNKNOWN')
      IF ( DSNAMES(12) .NE. 'none' )
     & OPEN ( 12, FILE=DSNAMES(12),STATUS='UNKNOWN')
      IF ( DSNAMES(10) .NE. 'none' )
     & OPEN ( 10, FILE=DSNAMES(10),STATUS='UNKNOWN')
      IF ( DSNAMES(4) .NE. 'none' )
     & OPEN ( 4, FILE=DSNAMES(4),STATUS='UNKNOWN')
      IF ( DSNAMES(1) .NE. 'none' )
     & OPEN ( 1, FILE=DSNAMES(1),STATUS='UNKNOWN')
      CALL XSEM00
C
C     IF WE GET HERE, XSEM00 RETURNED NORMALLY (SHOULDN'T HAPPEN
C     BECAUSE PEXIT CALLS EXIT). BUT HANDLE IT ANYWAY.
C
      IRETURN = 0
      GO TO 999
C
900   IRETURN = -1
C
999   CONTINUE
      CLOSE(5, ERR=991)
991   CLOSE(6, ERR=992)
992   CONTINUE
      RETURN
      END
