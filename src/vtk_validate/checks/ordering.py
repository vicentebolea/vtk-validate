"""Pipeline ordering checks: Update() before GetOutput()."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from ..diagnostics import Diagnostic, ErrorType

if TYPE_CHECKING:
    from vtk_knowledge import VTKAPIIndex


def check_ordering(tree: ast.AST, index: "VTKAPIIndex") -> list[Diagnostic]:
    """Warn when GetOutput() is called without a preceding Update()."""
    diagnostics: list[Diagnostic] = []
    updated_vars: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Attribute):
            continue
        obj = call.func.value
        method = call.func.attr
        var_name = obj.id if isinstance(obj, ast.Name) else None
        if method == "Update" and var_name:
            updated_vars.add(var_name)
        if method == "GetOutput" and var_name and var_name not in updated_vars:
            diagnostics.append(
                Diagnostic(
                    type=ErrorType.PIPELINE_ORDERING,
                    severity="warning",
                    line=getattr(node, "lineno", 0),
                    message=(
                        f"GetOutput() called on '{var_name}' before Update(). "
                        "Call Update() first to ensure the pipeline executes."
                    ),
                    call_expression=f"{var_name}.GetOutput()",
                    suggestion=f"{var_name}.Update()",
                )
            )
    return diagnostics
