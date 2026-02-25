"""Tests for the NASTRAN runner."""

from __future__ import annotations

import numpy as np
import pytest

from tests.conftest import INP_CLEAN_DIR


class TestNastranRunner:
    @pytest.mark.slow
    def test_run_static_analysis(self, nastran_runner) -> None:
        """Run the d01011a static analysis demo problem."""
        input_file = INP_CLEAN_DIR / "d01011a.inp"
        if not input_file.exists():
            pytest.skip("Input file not found")

        result = nastran_runner.run(input_file, timeout=120.0)

        assert result.completed, f"NASTRAN did not complete. RC={result.returncode}"
        assert result.returncode == 0
        assert len(result.displacements) > 0
        assert result.wall_time > 0

        # Check displacement values match reference
        disp = result.displacements[0]
        idx_11 = np.where(disp.node_ids == 11)[0]
        assert len(idx_11) == 1
        # T3 for node 11 should be ~0.0389
        np.testing.assert_allclose(disp.translations[idx_11[0], 2], 3.889221e-02, rtol=0.05)

    @pytest.mark.slow
    def test_run_normal_modes(self, nastran_runner) -> None:
        """Run the d03011a normal modes demo problem."""
        input_file = INP_CLEAN_DIR / "d03011a.inp"
        if not input_file.exists():
            pytest.skip("Input file not found")

        result = nastran_runner.run(input_file, timeout=120.0)

        assert result.completed, f"NASTRAN did not complete. RC={result.returncode}"
        assert result.eigenvalues is not None
        assert len(result.eigenvalues.mode_numbers) == 3
        # First frequency should be ~0.906 Hz
        np.testing.assert_allclose(result.eigenvalues.frequencies[0], 9.055634e-01, rtol=0.05)

    @pytest.mark.slow
    def test_run_from_string(self, nastran_runner) -> None:
        """Run NASTRAN from an input deck string."""
        input_file = INP_CLEAN_DIR / "d01011a.inp"
        if not input_file.exists():
            pytest.skip("Input file not found")

        input_text = input_file.read_text()
        result = nastran_runner.run(input_text, timeout=120.0)

        assert result.completed
        assert len(result.displacements) > 0

    @pytest.mark.slow
    def test_run_convenience_function(self) -> None:
        """Test the module-level run() convenience function."""
        from pynastran95 import run

        input_file = INP_CLEAN_DIR / "d01011a.inp"
        if not input_file.exists():
            pytest.skip("Input file not found")

        result = run(input_file, timeout=120.0)
        assert result.completed
