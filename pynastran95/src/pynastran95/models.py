"""Data models for NASTRAN-95 results."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt


@dataclass
class DisplacementResult:
    """Displacement results from a NASTRAN analysis.

    Attributes:
        node_ids: Array of grid point IDs.
        translations: (N, 3) array of T1, T2, T3 translations.
        rotations: (N, 3) array of R1, R2, R3 rotations.
        subcase: Subcase ID this result belongs to.
    """

    node_ids: npt.NDArray[np.int32]
    translations: npt.NDArray[np.float64]
    rotations: npt.NDArray[np.float64]
    subcase: int = 1


@dataclass
class StressResult:
    """Element stress results from a NASTRAN analysis.

    Attributes:
        element_ids: Array of element IDs.
        element_type: Element type string (e.g. "CROD", "CBAR", "CTRIA3").
        stresses: Dict mapping stress component name to array of values.
        subcase: Subcase ID.
    """

    element_ids: npt.NDArray[np.int32]
    element_type: str
    stresses: dict[str, npt.NDArray[np.float64]]
    subcase: int = 1


@dataclass
class EigenvalueResult:
    """Eigenvalue results from a real eigenvalue analysis.

    Attributes:
        mode_numbers: Array of mode numbers.
        eigenvalues: Array of eigenvalues (radians/sec)^2.
        frequencies: Array of natural frequencies (cycles/sec).
        generalized_mass: Array of generalized masses.
        generalized_stiffness: Array of generalized stiffnesses.
    """

    mode_numbers: npt.NDArray[np.int32]
    eigenvalues: npt.NDArray[np.float64]
    frequencies: npt.NDArray[np.float64]
    generalized_mass: npt.NDArray[np.float64]
    generalized_stiffness: npt.NDArray[np.float64]


@dataclass
class NastranResult:
    """Complete results from a NASTRAN-95 analysis run.

    Attributes:
        returncode: Process return code (0 = success).
        output: Full text of the printed output (F06-style).
        log: Contents of the log file.
        completed: Whether "END OF JOB" was found in output.
        displacements: List of displacement results by subcase.
        stresses: List of stress results.
        eigenvalues: Eigenvalue results (if modal analysis).
        wall_time: Wall clock time for the run in seconds.
    """

    returncode: int
    output: str
    log: str = ""
    completed: bool = False
    displacements: list[DisplacementResult] = field(default_factory=list)
    stresses: list[StressResult] = field(default_factory=list)
    eigenvalues: EigenvalueResult | None = None
    wall_time: float = 0.0
