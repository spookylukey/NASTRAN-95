"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

# Paths relative to the pynastran95 project
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INP_CLEAN_DIR = REPO_ROOT / "inp_clean"
DEMOOUT_DIR = REPO_ROOT / "demoout"
BUILD_DIR = REPO_ROOT / "build"
RF_CLEAN_DIR = REPO_ROOT / "rf_clean"


@pytest.fixture
def nastran_runner():
    """Create a NastranRunner with default settings."""
    from pynastran95.runner import NastranRunner

    executable = BUILD_DIR / "nastrn"
    if not executable.exists():
        pytest.skip("NASTRAN executable not found")
    return NastranRunner(executable=executable, rfdir=RF_CLEAN_DIR)


@pytest.fixture
def reference_output_d01011a() -> str:
    """Load reference output for demo problem d01011a."""
    path = DEMOOUT_DIR / "d01011a.out"
    if not path.exists():
        pytest.skip("Reference output not found")
    return path.read_text()


@pytest.fixture
def reference_output_d03011a() -> str:
    """Load reference output for demo problem d03011a."""
    path = DEMOOUT_DIR / "d03011a.out"
    if not path.exists():
        pytest.skip("Reference output not found")
    return path.read_text()
