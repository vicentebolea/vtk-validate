"""Validate VTK class instantiation against the known API."""

from __future__ import annotations

import ast
import difflib
from typing import TYPE_CHECKING

from ..diagnostics import Diagnostic, ErrorType

if TYPE_CHECKING:
    from vtk_knowledge import VTKAPIIndex


def check_constructors(tree: ast.AST, index: "VTKAPIIndex") -> list[Diagnostic]:
    """Return diagnostics for unknown VTK class instantiations."""
    diagnostics: list[Diagnostic] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        class_name = _get_call_name(node)
        if not class_name or not class_name.startswith("vtk"):
            continue
        if index.has_class(class_name):
            continue

        suggestion = _suggest(class_name, index)
        diagnostics.append(
            Diagnostic(
                type=ErrorType.MISSING_CLASS,
                line=getattr(node, "lineno", 0),
                column=getattr(node, "col_offset", 0),
                message=f"Class '{class_name}' not found in the VTK API.",
                class_name=class_name,
                suggestion=suggestion,
            )
        )
    return diagnostics


def _get_call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _suggest(class_name: str, index: "VTKAPIIndex") -> str | None:
    candidates = [r.class_name for r in index.search_classes(class_name[:10], limit=3)]
    matches = difflib.get_close_matches(class_name, candidates, n=1, cutoff=0.6)
    return matches[0] if matches else (candidates[0] if candidates else None)
