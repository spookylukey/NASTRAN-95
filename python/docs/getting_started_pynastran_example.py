from io import StringIO
from pyNastran.bdf.bdf import BDF
import nastran95
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
    model.add_cbar(i + 1, 1, [i + 1, i + 2], x=[0.0, 0.0, 1.0], g0=None)

# Boundary conditions
model.add_spc1(1, '123456', [1])

# Load
model.add_force(1, 11, 1.0, [0.0, 0.0, 1000.0])

# Executive control (NASTRAN-95 format)
model.executive_control_lines = [
    'ID    CANTILEVER,PYNASTRAN',
    'SOL 1,1',
    'APP DISPLACEMENT',
    'TIME 10',
    'CEND',
]

# Case control
subcases = model.create_subcases(0)
case = subcases[0]
case.add_integer_type('SPC', 1)
case.add_integer_type('LOAD', 1)
case.add_result_type('DISPLACEMENT', 'ALL', [])

# Write to string and run
buf = StringIO()
model.write_bdf(buf, enddata=True, close=False)
result = nastran95.run(buf.getvalue())

if result.completed:
    disp = result.displacements[0]
    idx = np.where(disp.node_ids == 11)[0][0]
    print(f"Tip Z-deflection: {disp.translations[idx, 2]:.6e} in")
