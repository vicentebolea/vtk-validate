"""Validate VTK import statements against the known module map."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from ..diagnostics import Diagnostic, ErrorType

if TYPE_CHECKING:
    from vtk_knowledge import VTKAPIIndex


_ALLOWED_DIRECT_IMPORTS = {
    "vtkmodules.vtkRenderingOpenGL2",
    "vtkmodules.vtkInteractionStyle",
    "vtkmodules.vtkRenderingFreeType",
    "vtkmodules.vtkRenderingVolumeOpenGL2",
}


def check_imports(tree: ast.AST, index: "VTKAPIIndex") -> list[Diagnostic]:
    """Return diagnostics for incorrect VTK import statements."""
    diagnostics: list[Diagnostic] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                diag = _check_plain_import(alias.name, node.lineno)
                if diag:
                    diagnostics.append(diag)
        elif isinstance(node, ast.ImportFrom):
            if node.module and "vtk" in node.module.lower():
                for alias in node.names:
                    diag = _check_from_import(
                        node.module, alias.name, node.lineno, index
                    )
                    if diag:
                        diagnostics.append(diag)

    return diagnostics


def _check_plain_import(module: str, lineno: int) -> Diagnostic | None:
    if module in ("vtk", "vtkmodules.all"):
        return None
    if module.startswith("vtkmodules.") and module not in _ALLOWED_DIRECT_IMPORTS:
        return Diagnostic(
            type=ErrorType.UNKNOWN_MODULE,
            line=lineno,
            message=(
                f"Direct import of '{module}' is not allowed. "
                f"Use 'from {module} import ClassName' instead."
            ),
            suggestion=f"from {module} import <ClassName>",
        )
    return None


def _check_from_import(
    module: str, name: str, lineno: int, index: "VTKAPIIndex"
) -> Diagnostic | None:
    if module in ("vtkmodules.all",):
        return None

    # Check if name is a class in the index
    record = index.get_class(name)
    if record is None:
        if name.startswith("vtk"):
            return Diagnostic(
                type=ErrorType.MISSING_CLASS,
                line=lineno,
                message=f"Class '{name}' not found in the VTK API.",
                class_name=name,
            )
        return None

    if record.module_name != module:
        suggestion = f"from {record.module_name} import {name}"
        return Diagnostic(
            type=ErrorType.UNKNOWN_MODULE,
            line=lineno,
            message=(
                f"'{name}' is in '{record.module_name}', not '{module}'."
            ),
            class_name=name,
            suggestion=suggestion,
        )
    return None
