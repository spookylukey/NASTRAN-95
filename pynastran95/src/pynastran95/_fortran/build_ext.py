"""Build the NASTRAN-95 f2py extension module.

This script compiles all NASTRAN Fortran sources and wraps the entry point
subroutine using f2py. The result is a shared library that can be imported
directly in Python.

Usage:
    python -m pynastran95._fortran.build_ext
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
BUILD_DIR = REPO_ROOT / "build"
SRC_MIS = BUILD_DIR / "src_mis"
SRC_MDS = BUILD_DIR / "src_mds"
SRC_BD = BUILD_DIR / "src_bd"
STUBS = BUILD_DIR / "stubs.f"
INCLUDE_DIR = BUILD_DIR  # For .COM files

FORTRAN_DIR = Path(__file__).resolve().parent
ENTRY_POINT = FORTRAN_DIR / "nastran_entry.f"
EXIT_OVERRIDE = FORTRAN_DIR / "exit_override.f"
OUTPUT_DIR = FORTRAN_DIR

# Compiler flags (same as README)
FLAGS = [
    "-std=legacy",
    "-fno-range-check",
    "-w",
    "-fallow-argument-mismatch",
    "-fallow-invalid-boz",
    "-fno-automatic",
    "-fPIC",  # Required for shared library
]


def collect_sources() -> list[Path]:
    """Collect all Fortran source files."""
    sources: list[Path] = []
    for src_dir in [SRC_MIS, SRC_MDS, SRC_BD]:
        sources.extend(sorted(src_dir.glob("*.f")))
    sources.append(STUBS)
    return sources


def compile_objects(sources: list[Path], obj_dir: Path) -> list[Path]:
    """Compile Fortran sources to object files."""
    obj_dir.mkdir(parents=True, exist_ok=True)
    objects: list[Path] = []
    skip = {"nastrn.o", "chkfil.o"}  # Skip PROGRAM files

    for src in sources:
        obj_name = src.stem + ".o"
        if obj_name in skip:
            continue
        obj_path = obj_dir / obj_name
        objects.append(obj_path)

        # Skip if object is newer than source
        if obj_path.exists() and obj_path.stat().st_mtime > src.stat().st_mtime:
            continue

        cmd = [
            "gfortran",
            "-c",
            *FLAGS,
            f"-I{INCLUDE_DIR}",
            str(src),
            "-o",
            str(obj_path),
        ]
        print(f"  Compiling {src.name}...")
        subprocess.run(cmd, check=True, capture_output=True)

    return objects


def create_archive(objects: list[Path], archive_path: Path) -> None:
    """Create a static library from object files."""
    if archive_path.exists():
        archive_path.unlink()
    # Create archive in batches (command line length limits)
    obj_strs = [str(o) for o in objects]
    cmd = ["ar", "rcs", str(archive_path), *obj_strs]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  Created {archive_path.name} ({len(objects)} objects)")


def build_f2py_extension(
    objects: list[Path], entry_source: Path, obj_dir: Path | None = None
) -> Path:
    """Build the f2py extension module by linking all .o files directly."""
    python = sys.executable
    module_name = "_nastran_core"

    # Compile the C exit override to an object file first
    exit_c = FORTRAN_DIR / "exit_override.c"
    exit_o = obj_dir / "exit_override_c.o" if obj_dir else OUTPUT_DIR / "exit_override_c.o"
    subprocess.run(
        ["gcc", "-c", "-fPIC", "-o", str(exit_o), str(exit_c)],
        check=True,
        capture_output=True,
    )

    # Build with f2py, passing all object files directly instead of archive
    cmd = [
        python,
        "-m",
        "numpy.f2py",
        "-c",
        str(entry_source),
        "-m",
        module_name,
        f"-I{INCLUDE_DIR}",
        "--f77flags=" + " ".join(FLAGS),
        "--build-dir",
        str(OUTPUT_DIR / "_f2py_build"),
    ]
    # Add all object files, including the C exit override
    cmd.append(str(exit_o))
    cmd.extend(str(o) for o in objects)

    print(f"  Building f2py module {module_name} with {len(objects)} objects...")
    # Ensure meson/ninja from venv are on PATH
    env = os.environ.copy()
    venv_bin = str(Path(python).parent)
    env["PATH"] = venv_bin + ":" + env.get("PATH", "")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(OUTPUT_DIR), env=env)
    if result.returncode != 0:
        print("STDOUT:", result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
        print("STDERR:", result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
        msg = f"f2py build failed with return code {result.returncode}"
        raise RuntimeError(msg)

    # Find the built .so file
    so_files = list(OUTPUT_DIR.glob(f"{module_name}*.so"))
    if not so_files:
        # Check build dir
        so_files = list((OUTPUT_DIR / "_f2py_build").rglob(f"{module_name}*.so"))
        if so_files:
            # Move to output dir
            dest = OUTPUT_DIR / so_files[0].name
            shutil.move(str(so_files[0]), str(dest))
            so_files = [dest]

    if not so_files:
        msg = f"Could not find built {module_name}*.so"
        raise RuntimeError(msg)

    print(f"  Built {so_files[0].name}")
    return so_files[0]


def build() -> Path:
    """Build the complete NASTRAN f2py extension."""
    print("Building NASTRAN-95 f2py extension...")

    obj_dir = OUTPUT_DIR / "_obj"

    print("Step 1: Collecting sources...")
    sources = collect_sources()
    print(f"  Found {len(sources)} source files")

    print("Step 2: Compiling to object files...")
    objects = compile_objects(sources, obj_dir)
    print(f"  Compiled {len(objects)} objects")

    print("Step 3: Building f2py extension...")
    so_path = build_f2py_extension(objects, ENTRY_POINT, obj_dir)

    print(f"Done! Extension at: {so_path}")
    return so_path


if __name__ == "__main__":
    build()
