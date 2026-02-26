      SUBROUTINE CPUTIM (ICPUSC,RCPUSC,IFLAG)        
C        
C     GFORTRAN VERSION - ETIME is an intrinsic function
C        
      REAL ARRAY(2), T
      T = ETIME(ARRAY)
      T = ARRAY(1) + ARRAY(2)
      IF (IFLAG .NE. 0) GO TO 30        
      ICPUSC = T + .49        
      GO TO 40        
   30 SAVE   = RCPUSC        
      RCPUSC = T        
      IF (RCPUSC .LE. SAVE) RCPUSC = RCPUSC + 0.0001        
   40 RETURN        
      END        
