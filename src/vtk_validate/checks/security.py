"""Forbidden import and call checks for untrusted code."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from ..diagnostics import Diagnostic, ErrorType

if TYPE_CHECKING:
    from vtk_knowledge import VTKAPIIndex

_FORBIDDEN_MODULES = frozenset(
    {
        "os",
        "subprocess",
        "sys",
        "socket",
        "urllib",
        "requests",
        "http",
        "ftplib",
        "smtplib",
    }
)

_FORBIDDEN_BUILTINS = frozenset({"eval", "exec", "__import__", "compile"})


def check_security(tree: ast.AST, index: "VTKAPIIndex") -> list[Diagnostic]:
    """Return diagnostics for forbidden imports and dangerous built-in calls."""
    diagnostics: list[Diagnostic] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = node.names[0].name if isinstance(node, ast.Import) else (node.module or "")
            root = module.split(".")[0]
            if root in _FORBIDDEN_MODULES:
                diagnostics.append(
                    Diagnostic(
                        type=ErrorType.FORBIDDEN_IMPORT,
                        line=getattr(node, "lineno", 0),
                        message=f"Import of '{module}' is not allowed in VTK scripts.",
                    )
                )
        elif isinstance(node, ast.Call):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            if name in _FORBIDDEN_BUILTINS:
                diagnostics.append(
                    Diagnostic(
                        type=ErrorType.FORBIDDEN_CALL,
                        line=getattr(node, "lineno", 0),
                        message=f"Call to '{name}()' is not allowed in VTK scripts.",
                        call_expression=name,
                    )
                )
    return diagnostics
