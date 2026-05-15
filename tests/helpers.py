"""Shared fixtures and helpers for vtk_validate tests."""

from __future__ import annotations

import ast
from unittest.mock import MagicMock


def make_mock_method(name: str = "GetOutput") -> MagicMock:
    m = MagicMock()
    m.name = name
    m.model_dump.return_value = {"name": name, "signature": f"{name}() -> None"}
    return m


def make_mock_record(
    class_name: str = "vtkActor",
    module_name: str = "vtkRenderingCore",
    methods: list[str] | None = None,
) -> MagicMock:
    r = MagicMock()
    r.class_name = class_name
    r.module_name = module_name
    r.methods = [make_mock_method(m) for m in (methods or [])]
    r.synopsis = f"{class_name} synopsis"
    r.model_dump.return_value = {
        "class_name": class_name,
        "module_name": module_name,
        "synopsis": r.synopsis,
    }
    return r


def make_mock_index(
    known_classes: dict[str, str] | None = None,
) -> MagicMock:
    """Return a mock VTKAPIIndex.

    known_classes maps class_name → module_name.
    """
    idx = MagicMock()
    idx.vtk_version = "9.3.0"

    classes = known_classes or {"vtkActor": "vtkRenderingCore"}
    records = {name: make_mock_record(name, mod) for name, mod in classes.items()}

    def _get_class(name):
        return records.get(name)

    def _has_class(name):
        return name in records

    def _search_classes(query, limit=10):
        return list(records.values())[:limit]

    def _get_method(class_name, method_name):
        rec = records.get(class_name)
        if rec is None:
            return None
        for m in rec.methods:
            if m.name == method_name:
                return m
        return None

    def _get_class_methods(class_name):
        rec = records.get(class_name)
        return rec.methods if rec else []

    idx.get_class.side_effect = _get_class
    idx.has_class.side_effect = _has_class
    idx.search_classes.side_effect = _search_classes
    idx.get_method.side_effect = _get_method
    idx.get_class_methods.side_effect = _get_class_methods
    idx.get_class_role.return_value = "filter"
    idx.get_class_input_datatype.return_value = "vtkDataSet"
    idx.get_class_output_datatype.return_value = "vtkPolyData"
    idx.get_class_semantic_methods.return_value = ["SetInput", "GetOutput"]
    idx.get_class_doc.return_value = "A doc string."
    idx.get_class_module.return_value = "vtkRenderingCore"
    idx.classes_in_module.return_value = ["vtkActor", "vtkRenderer"]
    idx.get_method_doc.return_value = "Method doc."
    idx.get_method_signature.return_value = "GetOutput() -> vtkPolyData"
    idx.get_class_synopsis.return_value = "Short synopsis."
    idx.get_class_action_phrase.return_value = "renders geometry"
    idx.get_class_visibility.return_value = 0.9
    return idx


def parse(source: str) -> ast.AST:
    return ast.parse(source)
