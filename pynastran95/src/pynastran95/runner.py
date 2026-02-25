"""NASTRAN-95 execution runner."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Literal

from pynastran95.models import NastranResult
from pynastran95.parser import (
    is_completed,
    parse_displacements,
    parse_eigenvalues,
    parse_membrane_stresses,
    parse_rod_stresses,
    parse_shear_stresses,
)

# Default paths relative to the repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DEFAULT_EXECUTABLE = _REPO_ROOT / "build" / "nastrn"
_DEFAULT_RFDIR = _REPO_ROOT / "rf_clean"


class NastranRunner:
    """Runs NASTRAN-95 analyses.

    Supports two execution modes:
    - "subprocess" (default): Runs the nastrn binary as a subprocess.
      Robust and works without building the f2py extension.
    - "f2py": Calls the Fortran solver directly via f2py in a forked
      child process. Requires building the extension first.

    Args:
        executable: Path to the nastrn binary (subprocess mode only).
        rfdir: Path to the rigid format directory.
        dbmem: Database memory allocation in words.
        ocmem: Open-core memory allocation in words.
        scratch_root: Root directory for scratch files. Uses tempdir if None.
        mode: Execution mode: "subprocess" or "f2py".
    """

    def __init__(
        self,
        executable: str | Path | None = None,
        rfdir: str | Path | None = None,
        dbmem: int = 12_000_000,
        ocmem: int = 2_000_000,
        scratch_root: str | Path | None = None,
        mode: Literal["subprocess", "f2py"] = "subprocess",
    ) -> None:
        self.mode = mode
        self.rfdir = Path(rfdir) if rfdir else _DEFAULT_RFDIR
        self.dbmem = dbmem
        self.ocmem = ocmem
        self.scratch_root = Path(scratch_root) if scratch_root else None

        if mode == "subprocess":
            self.executable = Path(executable) if executable else _DEFAULT_EXECUTABLE
            if not self.executable.exists():
                msg = f"NASTRAN executable not found: {self.executable}"
                raise FileNotFoundError(msg)
        elif mode == "f2py":
            from pynastran95._fortran import is_built

            if not is_built():
                msg = "f2py extension not built. Run: python -m pynastran95._fortran.build_ext"
                raise RuntimeError(msg)
            self.executable = None  # type: ignore[assignment]
        else:
            msg = f"Unknown mode: {mode!r}. Use 'subprocess' or 'f2py'."
            raise ValueError(msg)

        if not self.rfdir.is_dir():
            msg = f"Rigid format directory not found: {self.rfdir}"
            raise FileNotFoundError(msg)

    def run(
        self,
        input_data: str | Path,
        *,
        timeout: float | None = 300.0,
        cleanup: bool = True,
    ) -> NastranResult:
        """Run a NASTRAN analysis.

        Args:
            input_data: Either a path to an input file, or a string containing
                        the NASTRAN input deck.
            timeout: Maximum wall time in seconds. None for no limit.
            cleanup: Whether to remove scratch files after the run.

        Returns:
            NastranResult with output text and parsed results.
        """
        # Handle input
        if isinstance(input_data, Path) or (
            isinstance(input_data, str) and os.path.isfile(input_data)
        ):
            input_path = Path(input_data)
            input_text = input_path.read_text()
        else:
            input_text = input_data

        # Create scratch directory
        scratch_parent = self.scratch_root or Path(tempfile.gettempdir())
        scratch_dir = Path(tempfile.mkdtemp(prefix="nastran_", dir=scratch_parent))

        try:
            if self.mode == "subprocess":
                return self._execute_subprocess(input_text, scratch_dir, timeout)
            else:
                return self._execute_f2py(input_text, scratch_dir, timeout)
        finally:
            if cleanup:
                shutil.rmtree(scratch_dir, ignore_errors=True)

    def _setup_env(self, scratch_dir: Path) -> dict[str, str]:
        """Set up environment variables for NASTRAN."""
        env = os.environ.copy()
        env["RFDIR"] = str(self.rfdir)
        env["DBMEM"] = str(self.dbmem)
        env["OCMEM"] = str(self.ocmem)
        env["DIRCTY"] = str(scratch_dir)
        env["LOGNM"] = str(scratch_dir / "run.log")
        env["NPTPNM"] = str(scratch_dir / "run.nptp")
        env["DICTNM"] = str(scratch_dir / "run.dic")
        env["PLTNM"] = str(scratch_dir / "plot.dat")
        env["PUNCHNM"] = str(scratch_dir / "punch.dat")
        env["OPTPNM"] = "none"
        env["SOF1"] = "none"
        env["SOF2"] = "none"
        for i in range(3, 11):
            env[f"SOF{i}"] = "none"
        for i in range(11, 24):
            env[f"FTN{i}"] = str(scratch_dir / f"ftn{i}")
        return env

    def _parse_results(self, output: str) -> NastranResult:
        """Parse NASTRAN output text into structured results."""
        completed = is_completed(output)
        displacements = parse_displacements(output)
        eigenvalues = parse_eigenvalues(output)
        stresses = (
            parse_rod_stresses(output)
            + parse_shear_stresses(output)
            + parse_membrane_stresses(output)
        )
        return NastranResult(
            returncode=0,
            output=output,
            completed=completed,
            displacements=displacements,
            stresses=stresses,
            eigenvalues=eigenvalues,
        )

    def _execute_subprocess(
        self,
        input_text: str,
        scratch_dir: Path,
        timeout: float | None,
    ) -> NastranResult:
        """Execute NASTRAN as a subprocess."""
        env = self._setup_env(scratch_dir)

        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                [str(self.executable)],
                input=input_text,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd=str(scratch_dir),
            )
            wall_time = time.monotonic() - t0
            output = proc.stdout
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            wall_time = time.monotonic() - t0
            return NastranResult(
                returncode=-1,
                output="",
                log="",
                completed=False,
                wall_time=wall_time,
            )

        # Read log file if it exists
        log_path = scratch_dir / "run.log"
        log = log_path.read_text() if log_path.exists() else ""

        result = self._parse_results(output)
        result.returncode = returncode
        result.log = log
        result.wall_time = wall_time
        return result

    def _execute_f2py(
        self,
        input_text: str,
        scratch_dir: Path,
        timeout: float | None,
    ) -> NastranResult:
        """Execute NASTRAN via the f2py extension (forked child process)."""
        from pynastran95._fortran import get_core

        # Set environment variables (f2py reads them via getenv)
        env = self._setup_env(scratch_dir)
        old_env = {}
        for key, value in env.items():
            old_env[key] = os.environ.get(key)
            os.environ[key] = value

        # Write input to a temp file
        input_file = scratch_dir / "input.dat"
        input_file.write_text(input_text)

        output_file = scratch_dir / "output.out"

        t0 = time.monotonic()
        try:
            core = get_core()
            rc = core.nastran_solve(str(input_file), str(output_file))
            wall_time = time.monotonic() - t0
        finally:
            # Restore environment
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        # Read output
        output = output_file.read_text() if output_file.exists() else ""
        log_path = scratch_dir / "run.log"
        log = log_path.read_text() if log_path.exists() else ""

        result = self._parse_results(output)
        result.returncode = int(rc)
        result.log = log
        result.wall_time = wall_time
        return result


def run(
    input_data: str | Path,
    *,
    timeout: float | None = 300.0,
    mode: Literal["subprocess", "f2py"] = "subprocess",
    **kwargs: object,
) -> NastranResult:
    """Convenience function to run a NASTRAN analysis.

    Args:
        input_data: Path to input file or input deck string.
        timeout: Maximum wall time in seconds.
        mode: Execution mode ("subprocess" or "f2py").
        **kwargs: Additional arguments passed to NastranRunner.

    Returns:
        NastranResult with output and parsed results.
    """
    runner = NastranRunner(mode=mode, **kwargs)  # type: ignore[arg-type]
    return runner.run(input_data, timeout=timeout)
