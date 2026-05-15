"""Validate VTK method calls against the known API."""

from __future__ import annotations

import ast
import difflib
from typing import TYPE_CHECKING

from ..diagnostics import Diagnostic, ErrorType

if TYPE_CHECKING:
    from vtk_knowledge import VTKAPIIndex


def check_methods(tree: ast.AST, index: "VTKAPIIndex") -> list[Diagnostic]:
    """Return diagnostics for method calls on typed VTK variables."""
    var_types = _track_var_types(tree)
    diagnostics: list[Diagnostic] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue

        method_name = node.func.attr
        obj = node.func.value

        # Only handle simple Name references
        if not isinstance(obj, ast.Name):
            continue
        class_name = var_types.get(obj.id)
        if not class_name:
            continue

        method = index.get_method(class_name, method_name)
        if method is not None:
            continue

        suggestion = _suggest_method(class_name, method_name, index)
        diagnostics.append(
            Diagnostic(
                type=ErrorType.MISSING_METHOD,
                line=getattr(node, "lineno", 0),
                column=getattr(node, "col_offset", 0),
                message=(f"Method '{method_name}()' not found on '{class_name}'."),
                class_name=class_name,
                method_name=method_name,
                suggestion=suggestion,
            )
        )
    return diagnostics


def _track_var_types(tree: ast.AST) -> dict[str, str]:
    """Map variable names to VTK class names from simple assignments."""
    types: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        class_name = _call_name(node.value)
        if not class_name or not class_name.startswith("vtk"):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                types[target.id] = class_name
    return types


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _suggest_method(class_name: str, method_name: str, index: "VTKAPIIndex") -> str | None:
    record = index.get_class(class_name)
    if not record:
        return None
    valid = [m.name for m in record.methods]
    matches = difflib.get_close_matches(method_name, valid, n=1, cutoff=0.6)
    return matches[0] if matches else None
