"""Tests for the f2py extension module."""

from __future__ import annotations

import numpy as np
import pytest

from pynastran95._fortran import is_built
from tests.conftest import INP_CLEAN_DIR

pytestmark = pytest.mark.skipif(not is_built(), reason="f2py extension not built")


class TestF2pyRunner:
    @pytest.mark.slow
    def test_run_static_f2py(self) -> None:
        """Run static analysis via f2py extension."""
        from pynastran95.runner import NastranRunner

        input_file = INP_CLEAN_DIR / "d01011a.inp"
        if not input_file.exists():
            pytest.skip("Input file not found")

        runner = NastranRunner(mode="f2py")
        result = runner.run(input_file, timeout=120.0)

        assert result.completed, f"Not completed. RC={result.returncode}"
        assert result.returncode == 0
        assert len(result.displacements) > 0

        disp = result.displacements[0]
        idx_11 = np.where(disp.node_ids == 11)[0]
        assert len(idx_11) == 1
        np.testing.assert_allclose(disp.translations[idx_11[0], 2], 3.889221e-02, rtol=0.05)

    @pytest.mark.slow
    def test_run_eigenvalue_f2py(self) -> None:
        """Run eigenvalue analysis via f2py extension."""
        from pynastran95.runner import NastranRunner

        input_file = INP_CLEAN_DIR / "d03011a.inp"
        if not input_file.exists():
            pytest.skip("Input file not found")

        runner = NastranRunner(mode="f2py")
        result = runner.run(input_file, timeout=120.0)

        assert result.completed
        assert result.eigenvalues is not None
        assert len(result.eigenvalues.mode_numbers) == 3
        np.testing.assert_allclose(result.eigenvalues.frequencies[0], 9.055634e-01, rtol=0.05)

    @pytest.mark.slow
    def test_f2py_run_convenience(self) -> None:
        """Test the module-level run() with f2py mode."""
        from pynastran95 import run

        input_file = INP_CLEAN_DIR / "d01011a.inp"
        if not input_file.exists():
            pytest.skip("Input file not found")

        result = run(input_file, mode="f2py", timeout=120.0)
        assert result.completed


class TestF2pyCommonBlocks:
    def test_common_blocks_accessible(self) -> None:
        """Verify COMMON blocks are accessible from Python."""
        from pynastran95._fortran import get_core

        core = get_core()

        # These should all be accessible
        assert hasattr(core, "system")
        assert hasattr(core, "dbm")
        assert hasattr(core, "lstadd")
        assert hasattr(core, "logout")

        # System common block should have isystm array
        assert hasattr(core.system, "isystm")
        assert len(core.system.isystm) == 94
