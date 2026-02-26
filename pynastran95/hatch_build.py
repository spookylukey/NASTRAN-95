"""Custom Hatch build hook to compile NASTRAN-95 Fortran sources.

This hook compiles the nastrn executable from Fortran sources and copies
rigid format data files into the package so they're bundled in the wheel.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

# Compiler flags matching the README
FLAGS = [
    "-std=legacy",
    "-fno-range-check",
    "-w",
    "-fallow-argument-mismatch",
    "-fallow-invalid-boz",
    "-fno-automatic",
]


class NastranBuildHook(BuildHookInterface):
    PLUGIN_NAME = "nastran-build"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Compile nastrn and bundle data files into the package."""
        # Resolve paths
        root = Path(self.root)
        # The NASTRAN repo root is one level up from pynastran95/
        repo_root = root.parent
        src_mis = repo_root / "build" / "src_mis"
        src_mds = repo_root / "build" / "src_mds"
        src_bd = repo_root / "build" / "src_bd"
        src_bin = repo_root / "build" / "src_bin"
        stubs = repo_root / "build" / "stubs.f"
        include_dir = repo_root / "build"
        rf_clean = repo_root / "rf_clean"

        # Target directories inside the package
        pkg_data = root / "src" / "pynastran95" / "_data"
        pkg_bin = pkg_data / "bin"
        pkg_rf = pkg_data / "rf"
        pkg_bin.mkdir(parents=True, exist_ok=True)
        pkg_rf.mkdir(parents=True, exist_ok=True)

        is_windows = platform.system() == "Windows"
        exe_name = "nastrn.exe" if is_windows else "nastrn"
        exe_path = pkg_bin / exe_name

        # Check if pre-built executable exists (set by CIBW_BEFORE_BUILD or manual)
        prebuilt = os.environ.get("NASTRAN_PREBUILT_EXE")
        if prebuilt and Path(prebuilt).exists():
            print(f"Using pre-built executable: {prebuilt}")
            shutil.copy2(prebuilt, exe_path)
        elif not exe_path.exists():
            self._compile_nastran(
                src_mis, src_mds, src_bd, src_bin, stubs, include_dir, exe_path
            )

        # Make executable
        if not is_windows:
            exe_path.chmod(0o755)

        # Copy rigid format files
        if rf_clean.is_dir():
            for rf_file in sorted(rf_clean.iterdir()):
                if rf_file.is_file():
                    dest = pkg_rf / rf_file.name
                    if not dest.exists():
                        shutil.copy2(rf_file, dest)
            print(f"Copied {len(list(pkg_rf.iterdir()))} rigid format files")

        # Tell hatch to include bin/ and rf/ subdirectories
        # (_data/__init__.py is already picked up by package discovery)
        build_data["force_include"] = {
            str(pkg_bin): "pynastran95/_data/bin",
            str(pkg_rf): "pynastran95/_data/rf",
        }

        # Mark wheel as platform-specific (contains native binary)
        # This makes the wheel tag e.g. cp312-cp312-linux_x86_64
        build_data["pure_python"] = False
        build_data["infer_tag"] = True

    def _compile_nastran(
        self,
        src_mis: Path,
        src_mds: Path,
        src_bd: Path,
        src_bin: Path,
        stubs: Path,
        include_dir: Path,
        exe_path: Path,
    ) -> None:
        """Compile all Fortran sources into the nastrn executable."""
        print("Compiling NASTRAN-95 from Fortran sources...")

        # Collect all source files
        sources: list[Path] = []
        sources.extend(sorted(src_mis.glob("*.f")))
        # Exclude chkfil.f and nastrn.f from src_mds (both have PROGRAM main)
        skip_mds = {"chkfil.f", "nastrn.f"}
        mds_sources = sorted(src_mds.glob("*.f"))
        sources.extend(f for f in mds_sources if f.name not in skip_mds)
        sources.extend(sorted(src_bd.glob("*.f")))
        sources.append(stubs)
        # Add main program
        sources.append(src_bin / "nastrn.f")

        print(f"  {len(sources)} source files")

        # Compile to object files in a temp directory
        obj_dir = exe_path.parent / "_obj"
        obj_dir.mkdir(exist_ok=True)

        objects: list[Path] = []
        for i, src in enumerate(sources):
            # Use index prefix to avoid name collisions across directories
            obj = obj_dir / f"{i:04d}_{src.stem}.o"
            objects.append(obj)
            cmd = [
                "gfortran", "-c", *FLAGS,
                f"-I{include_dir}",
                str(src), "-o", str(obj),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"Failed to compile {src.name}: {result.stderr[:500]}"
                )

        print(f"  Compiled {len(objects)} objects")

        # Link with static libgfortran if possible (for manylinux compat)
        link_flags = list(FLAGS)
        link_flags.extend(["-static-libgfortran", "-static-libgcc"])

        cmd = [
            "gfortran", *link_flags,
            *[str(o) for o in objects],
            "-o", str(exe_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Retry without static flags
            print("  Static linking failed, trying dynamic...")
            cmd = [
                "gfortran", *FLAGS,
                *[str(o) for o in objects],
                "-o", str(exe_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"Link failed (rc={result.returncode}):\n"
                    f"STDERR: {result.stderr[-2000:]}\n"
                    f"STDOUT: {result.stdout[-500:]}"
                )

        print(f"  Linked: {exe_path.name}")

        # Clean up object files
        shutil.rmtree(obj_dir, ignore_errors=True)
