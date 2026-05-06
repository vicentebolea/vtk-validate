"""Top-level public API for vtk-validate.

Hot path usage::

    from vtk_validate import validate
    from vtk_knowledge import VTKAPIIndex

    index = VTKAPIIndex.from_jsonl(path)
    report = validate(source_code, index)
    if report.status != "ok":
        for d in report.diagnostics:
            print(d.message)
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from .analyzer import analyze
from .diagnostics import ValidationReport

if TYPE_CHECKING:
    from vtk_knowledge import VTKAPIIndex


def validate(source: str, index: "VTKAPIIndex") -> ValidationReport:
    """Validate a Python source string against a VTK API index.

    Pure function. No I/O. No global state. Safe to call from any context.

    Performance target: <20 ms per call for typical scripts (≤200 lines).

    Args:
        source: Python source code to validate.
        index: Loaded VTKAPIIndex (load once, reuse across calls).

    Returns:
        ValidationReport with status and diagnostics.
    """
    t0 = time.perf_counter()
    diagnostics = analyze(source, index)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return ValidationReport.from_diagnostics(
        diagnostics,
        vtk_version=index.vtk_version,
        elapsed_ms=elapsed_ms,
    )
