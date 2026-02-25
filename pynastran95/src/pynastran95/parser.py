"""Parser for NASTRAN-95 printed output (F06-style)."""

from __future__ import annotations

import re

import numpy as np

from pynastran95.models import DisplacementResult, EigenvalueResult, StressResult

# Fortran carriage control: column 1 is a control character, not data.
# '1' = new page, '0' = double space, ' ' = single space, '+' = overprint
# We detect page breaks by looking at the ORIGINAL (not stripped) line.


def _is_page_break(line: str) -> bool:
    """Check if this is a Fortran page-break line (starts with '1' in column 1)."""
    return len(line) > 0 and line[0] == "1"


def _is_double_space(line: str) -> bool:
    """Check if this is a Fortran double-space line (starts with '0' in column 1)."""
    return len(line) > 0 and line[0] == "0"


def _is_data_line(line: str) -> bool:
    """Check if a line looks like it contains numeric data (not a header/page break)."""
    stripped = line.strip()
    if not stripped:
        return False
    # Data lines start with a number (node/element ID)
    return bool(re.match(r"^\d+", stripped))


def parse_displacements(output: str, subcase: int = 1) -> list[DisplacementResult]:
    """Parse displacement vectors from NASTRAN output.

    Returns a list of DisplacementResult (one per displacement table found).
    """
    results: list[DisplacementResult] = []
    lines = output.splitlines()
    i = 0
    while i < len(lines):
        if "D I S P L A C E M E N T   V E C T O R" in lines[i]:
            # Skip to the column header line
            i += 1
            while i < len(lines) and "POINT ID." not in lines[i]:
                i += 1
            i += 1  # skip the column header line itself

            node_ids: list[int] = []
            translations: list[list[float]] = []
            rotations: list[list[float]] = []

            while i < len(lines):
                line = lines[i]
                if _is_page_break(line) or _is_double_space(line):
                    break
                stripped = line.strip()
                if not stripped:
                    i += 1
                    continue
                parts = stripped.split()
                if len(parts) >= 8:
                    try:
                        nid = int(parts[0])
                        # parts[1] is type (G or S)
                        t1 = float(parts[2])
                        t2 = float(parts[3])
                        t3 = float(parts[4])
                        r1 = float(parts[5])
                        r2 = float(parts[6])
                        r3 = float(parts[7])
                        node_ids.append(nid)
                        translations.append([t1, t2, t3])
                        rotations.append([r1, r2, r3])
                    except (ValueError, IndexError):
                        break
                else:
                    break
                i += 1

            if node_ids:
                results.append(
                    DisplacementResult(
                        node_ids=np.array(node_ids, dtype=np.int32),
                        translations=np.array(translations, dtype=np.float64),
                        rotations=np.array(rotations, dtype=np.float64),
                        subcase=subcase,
                    )
                )
        else:
            i += 1
    return results


def parse_eigenvalues(output: str) -> EigenvalueResult | None:
    """Parse real eigenvalue table from NASTRAN output."""
    lines = output.splitlines()
    i = 0
    mode_numbers: list[int] = []
    eigenvalues: list[float] = []
    frequencies: list[float] = []
    gen_mass: list[float] = []
    gen_stiff: list[float] = []

    while i < len(lines):
        if "R E A L   E I G E N V A L U E S" in lines[i]:
            # Skip header lines to find the "MODE" header
            i += 1
            while i < len(lines) and "MODE" not in lines[i]:
                i += 1
            if i >= len(lines):
                break
            i += 1  # skip "MODE" line
            # Skip "NO. ORDER ..." sub-header line if present
            if i < len(lines) and "NO." in lines[i]:
                i += 1

            while i < len(lines):
                line = lines[i]
                if _is_page_break(line):
                    break
                stripped = line.strip()
                if not stripped:
                    i += 1
                    continue
                # Skip info messages embedded in eigenvalue table
                if stripped.startswith("*") or stripped.startswith("+") or "MESSAGE" in stripped:
                    i += 1
                    continue
                parts = stripped.split()
                if len(parts) >= 7:
                    try:
                        mode = int(parts[0])
                        _ = int(parts[1])  # extraction order
                        ev = float(parts[2])
                        # parts[3] = radian freq
                        freq = float(parts[4])
                        gm = float(parts[5])
                        gs = float(parts[6])
                        mode_numbers.append(mode)
                        eigenvalues.append(ev)
                        frequencies.append(freq)
                        gen_mass.append(gm)
                        gen_stiff.append(gs)
                    except (ValueError, IndexError):
                        # Not a data line (could be header text)
                        i += 1
                        continue
                else:
                    # Could be an info line with few tokens, skip
                    i += 1
                    continue
                i += 1
            break  # Only parse first eigenvalue table
        i += 1

    if not mode_numbers:
        return None

    return EigenvalueResult(
        mode_numbers=np.array(mode_numbers, dtype=np.int32),
        eigenvalues=np.array(eigenvalues, dtype=np.float64),
        frequencies=np.array(frequencies, dtype=np.float64),
        generalized_mass=np.array(gen_mass, dtype=np.float64),
        generalized_stiffness=np.array(gen_stiff, dtype=np.float64),
    )


def parse_rod_stresses(output: str, subcase: int = 1) -> list[StressResult]:
    """Parse rod element stresses from NASTRAN output."""
    results: list[StressResult] = []
    lines = output.splitlines()
    i = 0
    while i < len(lines):
        if "S T R E S S E S   I N   R O D" in lines[i]:
            i += 1
            # Skip to the "ELEMENT" header
            while i < len(lines) and "ELEMENT" not in lines[i]:
                i += 1
            i += 1  # skip column header
            # Skip the "ID." sub-header if present
            if i < len(lines) and "ID." in lines[i]:
                i += 1

            elem_ids: list[int] = []
            axial: list[float] = []
            torsion: list[float] = []

            while i < len(lines):
                line = lines[i]
                if _is_page_break(line) or _is_double_space(line):
                    break
                stripped = line.strip()
                if not stripped:
                    i += 1
                    continue
                parts = stripped.split()
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        ax = float(parts[1])
                        # parts[2] may be safety margin
                        tor = float(parts[3]) if len(parts) > 3 else 0.0
                        elem_ids.append(eid)
                        axial.append(ax)
                        torsion.append(tor)
                    except (ValueError, IndexError):
                        break
                else:
                    break
                i += 1

            if elem_ids:
                results.append(
                    StressResult(
                        element_ids=np.array(elem_ids, dtype=np.int32),
                        element_type="CROD",
                        stresses={
                            "axial": np.array(axial, dtype=np.float64),
                            "torsion": np.array(torsion, dtype=np.float64),
                        },
                        subcase=subcase,
                    )
                )
        i += 1
    return results


def parse_shear_stresses(output: str, subcase: int = 1) -> list[StressResult]:
    """Parse shear panel stresses from NASTRAN output."""
    results: list[StressResult] = []
    lines = output.splitlines()
    i = 0
    while i < len(lines):
        if "S T R E S S E S   I N   S H E A R   P A N E L S" in lines[i]:
            i += 1
            # Skip to the first "ELEMENT" header line
            while i < len(lines) and "ELEMENT" not in lines[i]:
                i += 1
            i += 1  # skip first header
            # Skip "ID." line
            if i < len(lines) and "ID." in lines[i]:
                i += 1

            elem_ids: list[int] = []
            max_shear: list[float] = []
            avg_shear: list[float] = []

            while i < len(lines):
                line = lines[i]
                if _is_page_break(line) or _is_double_space(line):
                    break
                stripped = line.strip()
                if not stripped:
                    i += 1
                    continue
                # Shear stress lines have pairs of elements:
                # EID  MAX_SHEAR  AVG_SHEAR  [MARGIN]  EID  MAX_SHEAR  AVG_SHEAR  [MARGIN]
                parts = stripped.split()
                j = 0
                parsed_any = False
                try:
                    while j < len(parts):
                        eid = int(parts[j])
                        ms = float(parts[j + 1])
                        avs = float(parts[j + 2])
                        elem_ids.append(eid)
                        max_shear.append(ms)
                        avg_shear.append(avs)
                        j += 3
                        parsed_any = True
                        # Check if next item is a safety margin or next element
                        if j < len(parts):
                            try:
                                int(parts[j])
                            except ValueError:
                                j += 1  # skip safety margin
                except (ValueError, IndexError):
                    if not parsed_any:
                        break
                i += 1

            if elem_ids:
                results.append(
                    StressResult(
                        element_ids=np.array(elem_ids, dtype=np.int32),
                        element_type="CSHEAR",
                        stresses={
                            "max_shear": np.array(max_shear, dtype=np.float64),
                            "avg_shear": np.array(avg_shear, dtype=np.float64),
                        },
                        subcase=subcase,
                    )
                )
        i += 1
    return results


def parse_membrane_stresses(output: str, subcase: int = 1) -> list[StressResult]:
    """Parse quadrilateral/triangular membrane stresses from NASTRAN output."""
    results: list[StressResult] = []
    lines = output.splitlines()
    i = 0
    while i < len(lines):
        if re.search(r"S T R E S S E S   I N   (Q U A D|T R I A N G)", lines[i]):
            etype = "CQDMEM" if "Q U A D" in lines[i] else "CTRMEM"
            i += 1
            # Skip to the "ELEMENT" header
            while i < len(lines) and "ELEMENT" not in lines[i]:
                i += 1
            i += 1  # skip first header
            # Skip "ID." line
            if i < len(lines) and "ID." in lines[i]:
                i += 1

            elem_ids: list[int] = []
            normal_x: list[float] = []
            normal_y: list[float] = []
            shear_xy: list[float] = []
            major: list[float] = []
            minor: list[float] = []
            max_shear_vals: list[float] = []

            while i < len(lines):
                line = lines[i]
                if _is_page_break(line) or _is_double_space(line):
                    break
                stripped = line.strip()
                if not stripped:
                    i += 1
                    continue
                parts = stripped.split()
                if len(parts) >= 8:
                    try:
                        eid = int(parts[0])
                        nx = float(parts[1])
                        ny = float(parts[2])
                        sxy = float(parts[3])
                        # parts[4] = angle
                        maj = float(parts[5])
                        minn = float(parts[6])
                        ms = float(parts[7])
                        elem_ids.append(eid)
                        normal_x.append(nx)
                        normal_y.append(ny)
                        shear_xy.append(sxy)
                        major.append(maj)
                        minor.append(minn)
                        max_shear_vals.append(ms)
                    except (ValueError, IndexError):
                        break
                else:
                    break
                i += 1

            if elem_ids:
                results.append(
                    StressResult(
                        element_ids=np.array(elem_ids, dtype=np.int32),
                        element_type=etype,
                        stresses={
                            "normal_x": np.array(normal_x, dtype=np.float64),
                            "normal_y": np.array(normal_y, dtype=np.float64),
                            "shear_xy": np.array(shear_xy, dtype=np.float64),
                            "major": np.array(major, dtype=np.float64),
                            "minor": np.array(minor, dtype=np.float64),
                            "max_shear": np.array(max_shear_vals, dtype=np.float64),
                        },
                        subcase=subcase,
                    )
                )
        i += 1
    return results


def is_completed(output: str) -> bool:
    """Check if NASTRAN run completed successfully."""
    return "END OF JOB" in output or "JOB TERMINATED" in output
