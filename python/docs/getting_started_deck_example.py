import sys
import nastran95
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
GRID    2               10.0    0.0     0.0
GRID    3               20.0    0.0     0.0
GRID    4               30.0    0.0     0.0
GRID    5               40.0    0.0     0.0
GRID    6               50.0    0.0     0.0
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

result = nastran95.run(deck)

if result.completed:
    if not result.displacements:
        print("ERROR:")
        print(result.output)
        sys.exit(1)
    disp = result.displacements[0]
    # Get tip deflection (node 6)
    idx = np.where(disp.node_ids == 6)[0][0]
    print(f"Tip deflection: {disp.translations[idx, 2]:.6e} in")
else:
    print("ERROR:")
    print(result.output)
    