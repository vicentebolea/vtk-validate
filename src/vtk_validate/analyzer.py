"""AST walker — core validation orchestrator."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from .checks import (
    check_constructors,
    check_imports,
    check_methods,
    check_ordering,
    check_security,
)
from .diagnostics import Diagnostic

if TYPE_CHECKING:
    from vtk_knowledge import VTKAPIIndex


def analyze(source: str, index: "VTKAPIIndex") -> list[Diagnostic]:
    """Parse *source* and run all checks against *index*.

    Returns a flat list of Diagnostic instances. Syntax errors produce a
    single MISSING_CLASS diagnostic (approximate) rather than crashing.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        from .diagnostics import ErrorType

        return [
            Diagnostic(
                type=ErrorType.MISSING_CLASS,
                severity="error",
                line=exc.lineno or 0,
                message=f"SyntaxError: {exc.msg}",
            )
        ]

    diagnostics: list[Diagnostic] = []
    diagnostics.extend(check_security(tree, index))
    diagnostics.extend(check_imports(tree, index))
    diagnostics.extend(check_constructors(tree, index))
    diagnostics.extend(check_methods(tree, index))
    diagnostics.extend(check_ordering(tree, index))
    return diagnostics
