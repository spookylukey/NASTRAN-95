"""Integration tests using pyNastran for input generation."""

from __future__ import annotations

import numpy as np
import pytest

from pynastran95 import run


def _build_cantilever_bdf() -> str:
    """Build a simple cantilever beam input deck using pyNastran."""
    try:
        from pyNastran.bdf.bdf import BDF
    except ImportError:
        pytest.skip("pyNastran not installed")

    model = BDF()

    # Materials: steel
    E = 30.0e6  # psi
    nu = 0.3
    rho = 0.283  # lb/in^3
    model.add_mat1(mid=1, E=E, G=None, nu=nu, rho=rho)

    # Properties: rod
    A = 1.0  # in^2
    model.add_prod(pid=1, mid=1, A=A, j=0.0)

    # 10-element cantilever beam using CROD elements
    L = 100.0  # total length
    n_elem = 10
    dx = L / n_elem

    for i in range(n_elem + 1):
        nid = i + 1
        model.add_grid(nid, [i * dx, 0.0, 0.0])

    for i in range(n_elem):
        eid = i + 1
        model.add_conrod(eid, [i + 1, i + 2], mid=1, A=A)

    # Fix the left end (node 1)
    model.add_spc1(1, "123456", [1])

    # Apply a 1000 lb load at the tip (node 11) in Y-direction
    # Actually CROD only has axial - let's use X direction
    model.add_force(1, 11, 1.0, [1000.0, 0.0, 0.0])

    # Executive and case control
    lines = [
        "SOL 1,1",
        "APP DISPLACEMENT",
        "TIME 10",
        "CEND",
    ]
    model.executive_control_lines = [f"{line:<72}" for line in lines]

    case = model.create_subcases(0)
    case.add_integer_type("SPC", 1)
    case.add_integer_type("LOAD", 1)
    case.add_result_type("DISPLACEMENT", "ALL")
    case.add_result_type("SPCFORCES", "ALL")
    case.add_result_type("STRESS", "ALL")

    # Write to string
    from io import StringIO

    buf = StringIO()
    model.write_bdf(buf)
    return buf.getvalue()


def _build_cantilever_manual() -> str:
    """Build a simple cantilever beam input deck manually.

    A 10-element CBAR cantilever with a transverse tip load.
    Known analytical solution: delta = PL^3/(3EI)
    P=1000 lb, L=100 in, I=1.0 in^4, E=30e6 psi
    -> delta = 1000*100^3/(3*30e6*1.0) = 0.01111 in
    """
    lines = []

    # Executive control
    lines.append("ID    CANTILEVER,PYNASTRAN95")
    lines.append("APP   DISPLACEMENT")
    lines.append("SOL   1,1")
    lines.append("TIME  10")
    lines.append("CEND")

    # Case control
    lines.append("TITLE    = CANTILEVER BEAM TEST")
    lines.append("   SPC = 1")
    lines.append("  LOAD = 1")
    lines.append("  DISPLACEMENT = ALL")
    lines.append("  SPCFORCES = ALL")
    lines.append("  ELSTRESS = ALL")
    lines.append("BEGIN BULK")

    # Grid points: 11 nodes along X axis, 10 inches apart
    for i in range(11):
        nid = i + 1
        x = float(i * 10)
        # GRID, NID, CP, X1, X2, X3, CD, PS, SEID
        # 8-char fixed-field format
        lines.append(f"GRID    {nid:<8d}        {x:8.1f}     0.0     0.0")

    # CBAR elements with orientation vector in Z
    for i in range(10):
        eid = i + 1
        n1 = i + 1
        n2 = i + 2
        # CBAR, EID, PID, GA, GB, X1, X2, X3
        lines.append(f"CBAR    {eid:<8d}1       {n1:<8d}{n2:<8d}0.0     0.0     1.0")

    # Property: PBAR (beam), A=1.0 in^2, I1=I2=1.0 in^4, J=2.0 in^4
    lines.append("PBAR    1       1       1.0     1.0     1.0     2.0")

    # Material (MAT1) - steel
    lines.append("MAT1    1       30.0+6          .3      .283")

    # SPC: fix node 1 in all 6 DOFs
    lines.append("SPC1    1       123456  1")

    # Force: 1000 lb in Z direction on node 11
    lines.append("FORCE   1       11      0       1000.0  0.0     0.0     1.0")

    lines.append("ENDDATA")

    # Pad all lines to 80 columns (NASTRAN fixed format)
    return "\n".join(f"{line:<80s}" for line in lines) + "\n"


class TestPyNastranIntegration:
    @pytest.mark.slow
    def test_cantilever_manual(self) -> None:
        """Run a simple cantilever beam and verify analytical solution."""
        deck = _build_cantilever_manual()
        result = run(deck, timeout=120.0)

        assert result.completed, (
            f"NASTRAN did not complete. RC={result.returncode}\n"
            f"Last output: {result.output[-500:]}"
        )

        # Check displacements
        assert len(result.displacements) > 0
        disp = result.displacements[0]

        # Tip displacement (node 11) should be PL^3/(3EI)
        # P=1000, L=100, I=1.0, E=30e6 -> 0.01111 in (Z direction)
        idx_tip = np.where(disp.node_ids == 11)[0]
        assert len(idx_tip) == 1

        tip_disp_z = disp.translations[idx_tip[0], 2]
        analytical = 1000.0 * (100.0**3) / (3.0 * 30.0e6 * 1.0)
        np.testing.assert_allclose(tip_disp_z, analytical, rtol=0.02)

    @pytest.mark.slow
    def test_cantilever_f2py(self) -> None:
        """Run the same cantilever test via f2py."""
        from pynastran95._fortran import is_built

        if not is_built():
            pytest.skip("f2py extension not built")

        deck = _build_cantilever_manual()
        result = run(deck, mode="f2py", timeout=120.0)

        assert result.completed
        assert len(result.displacements) > 0

        disp = result.displacements[0]
        idx_tip = np.where(disp.node_ids == 11)[0]
        assert len(idx_tip) == 1

        tip_disp_z = disp.translations[idx_tip[0], 2]
        analytical = 1000.0 * (100.0**3) / (3.0 * 30.0e6 * 1.0)
        np.testing.assert_allclose(tip_disp_z, analytical, rtol=0.02)
