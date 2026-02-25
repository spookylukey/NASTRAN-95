"""Tests for the output parser."""

from __future__ import annotations

import numpy as np

from pynastran95.parser import (
    is_completed,
    parse_displacements,
    parse_eigenvalues,
    parse_membrane_stresses,
    parse_shear_stresses,
)


class TestIsCompleted:
    def test_end_of_job(self) -> None:
        assert is_completed("some output\n* * * END OF JOB * * *\n")

    def test_job_terminated(self) -> None:
        assert is_completed("output\nJOB TERMINATED\n")

    def test_not_completed(self) -> None:
        assert not is_completed("error happened")


class TestParseDisplacements:
    def test_parse_reference_output(self, reference_output_d01011a: str) -> None:
        """Parse displacements from the d01011a reference output."""
        results = parse_displacements(reference_output_d01011a)
        assert len(results) >= 1

        disp = results[0]
        assert len(disp.node_ids) > 0
        assert disp.translations.shape[1] == 3
        assert disp.rotations.shape[1] == 3

        # Check specific known values from reference output
        # Node 11: T1=0.0, T2=6.326195E-04, T3=3.889221E-02
        idx_11 = np.where(disp.node_ids == 11)[0]
        assert len(idx_11) == 1
        np.testing.assert_allclose(
            disp.translations[idx_11[0]],
            [0.0, 6.326195e-04, 3.889221e-02],
            rtol=1e-5,
        )

        # Node 16: T3=-4.237940E-01
        idx_16 = np.where(disp.node_ids == 16)[0]
        assert len(idx_16) == 1
        np.testing.assert_allclose(disp.translations[idx_16[0], 2], -4.237940e-01, rtol=1e-5)


class TestParseEigenvalues:
    def test_parse_reference_output(self, reference_output_d03011a: str) -> None:
        """Parse eigenvalues from the d03011a reference output."""
        result = parse_eigenvalues(reference_output_d03011a)
        assert result is not None

        # d03011a is a 10x20 plate vibration problem with 3 modes
        assert len(result.mode_numbers) == 3
        assert result.mode_numbers[0] == 1
        assert result.mode_numbers[1] == 2
        assert result.mode_numbers[2] == 3

        # Check known eigenvalues
        np.testing.assert_allclose(result.eigenvalues[0], 3.237408e01, rtol=1e-5)
        np.testing.assert_allclose(result.frequencies[0], 9.055634e-01, rtol=1e-5)

    def test_no_eigenvalues(self, reference_output_d01011a: str) -> None:
        """Static analysis should have no eigenvalues."""
        result = parse_eigenvalues(reference_output_d01011a)
        assert result is None


class TestParseStresses:
    def test_parse_membrane_stresses(self, reference_output_d01011a: str) -> None:
        """Parse membrane stresses from d01011a."""
        results = parse_membrane_stresses(reference_output_d01011a)
        assert len(results) >= 1

        # Find CQDMEM results
        qdmem = [r for r in results if r.element_type == "CQDMEM"]
        assert len(qdmem) >= 1

        stress = qdmem[0]
        assert len(stress.element_ids) > 0
        assert "normal_x" in stress.stresses
        assert "normal_y" in stress.stresses
        assert "shear_xy" in stress.stresses

        # Element 1: NORMAL-X = 1.067032E+03
        idx_1 = np.where(stress.element_ids == 1)[0]
        assert len(idx_1) == 1
        np.testing.assert_allclose(stress.stresses["normal_x"][idx_1[0]], 1.067032e03, rtol=1e-5)

    def test_parse_shear_stresses(self, reference_output_d01011a: str) -> None:
        """Parse shear panel stresses from d01011a."""
        results = parse_shear_stresses(reference_output_d01011a)
        assert len(results) >= 1

        shear = results[0]
        assert shear.element_type == "CSHEAR"
        assert len(shear.element_ids) > 0
        assert "max_shear" in shear.stresses
