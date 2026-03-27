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
        from nastran95 import run

        input_file = INP_CLEAN_DIR / "d01011a.inp"
        if not input_file.exists():
            pytest.skip("Input file not found")

        result = run(input_file, timeout=120.0)
        assert result.completed


class TestPathLengthValidation:
    """Tests for NASTRAN file path length validation."""

    def test_long_scratch_dir_raises(self) -> None:
        """Scratch directory paths that exceed the Fortran limit are rejected."""
        from nastran95.runner import NastranPathTooLongError, _FORTRAN_PATH_MAX, _validate_env_paths

        long_dir = "/tmp/" + "a" * _FORTRAN_PATH_MAX
        env = {
            "DIRCTY": long_dir,
            "LOGNM": long_dir + "/run.log",
        }
        with pytest.raises(NastranPathTooLongError, match="too long for NASTRAN"):
            _validate_env_paths(env)

    def test_long_rfdir_raises(self) -> None:
        """RFDIR paths that exceed the Fortran limit are rejected."""
        from nastran95.runner import NastranPathTooLongError, _FORTRAN_PATH_MAX, _validate_env_paths

        long_dir = "/opt/" + "r" * _FORTRAN_PATH_MAX
        env = {"RFDIR": long_dir}
        with pytest.raises(NastranPathTooLongError, match="too long for NASTRAN"):
            _validate_env_paths(env)

    def test_normal_paths_ok(self) -> None:
        """Normal-length paths pass validation without error."""
        from nastran95.runner import _validate_env_paths

        env = {
            "RFDIR": "/home/user/nastran/rf",
            "DIRCTY": "/tmp/nastran_abc123",
            "LOGNM": "/tmp/nastran_abc123/run.log",
            "NPTPNM": "/tmp/nastran_abc123/run.nptp",
            "DICTNM": "/tmp/nastran_abc123/run.dic",
            "PLTNM": "/tmp/nastran_abc123/plot.dat",
            "PUNCHNM": "/tmp/nastran_abc123/punch.dat",
            "OPTPNM": "none",
            "FTN11": "/tmp/nastran_abc123/ftn11",
            "SOF1": "none",
        }
        # Should not raise
        _validate_env_paths(env)

    def test_max_length_boundary(self) -> None:
        """Paths exactly at the limit pass; one char over fails."""
        from nastran95.runner import (
            NastranPathTooLongError,
            _FORTRAN_PATH_MAX,
            _MAX_DIR_SUFFIX_LEN,
            _validate_env_paths,
        )

        max_dir_len = _FORTRAN_PATH_MAX - _MAX_DIR_SUFFIX_LEN

        # Exactly at limit: should pass
        env_ok = {
            "RFDIR": "/" + "x" * (max_dir_len - 1),
            "DIRCTY": "/" + "y" * (max_dir_len - 1),
            "LOGNM": "/" + "z" * (_FORTRAN_PATH_MAX - 1),
        }
        _validate_env_paths(env_ok)  # no error

        # One over limit for directory: should fail
        env_bad = {
            "DIRCTY": "/" + "y" * max_dir_len,
        }
        with pytest.raises(NastranPathTooLongError):
            _validate_env_paths(env_bad)

        # One over limit for file path: should fail
        env_bad2 = {
            "LOGNM": "/" + "z" * _FORTRAN_PATH_MAX,
        }
        with pytest.raises(NastranPathTooLongError):
            _validate_env_paths(env_bad2)
