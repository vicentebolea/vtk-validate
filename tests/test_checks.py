"""Tests for vtk_validate.checks.*"""

from __future__ import annotations

from helpers import make_mock_index, parse

from vtk_validate.checks.constructors import check_constructors
from vtk_validate.checks.imports import check_imports
from vtk_validate.checks.methods import check_methods
from vtk_validate.checks.ordering import check_ordering
from vtk_validate.checks.security import check_security
from vtk_validate.diagnostics import ErrorType

# ---------------------------------------------------------------------------
# check_security
# ---------------------------------------------------------------------------


class TestCheckSecurity:
    def test_forbidden_import_os(self):
        idx = make_mock_index()
        tree = parse("import os")
        diags = check_security(tree, idx)
        assert len(diags) == 1
        assert diags[0].type == ErrorType.FORBIDDEN_IMPORT

    def test_forbidden_import_subprocess(self):
        idx = make_mock_index()
        tree = parse("import subprocess")
        diags = check_security(tree, idx)
        assert any(d.type == ErrorType.FORBIDDEN_IMPORT for d in diags)

    def test_forbidden_from_import(self):
        idx = make_mock_index()
        tree = parse("from os import path")
        diags = check_security(tree, idx)
        assert any(d.type == ErrorType.FORBIDDEN_IMPORT for d in diags)

    def test_forbidden_eval_call(self):
        idx = make_mock_index()
        tree = parse("eval('1+1')")
        diags = check_security(tree, idx)
        assert any(d.type == ErrorType.FORBIDDEN_CALL for d in diags)

    def test_forbidden_exec_call(self):
        idx = make_mock_index()
        tree = parse("exec('x = 1')")
        diags = check_security(tree, idx)
        assert any(d.type == ErrorType.FORBIDDEN_CALL for d in diags)

    def test_clean_vtk_code_no_diags(self):
        idx = make_mock_index()
        tree = parse("from vtkmodules.vtkRenderingCore import vtkActor\nactor = vtkActor()")
        diags = check_security(tree, idx)
        assert diags == []

    def test_line_number_recorded(self):
        idx = make_mock_index()
        tree = parse("x = 1\nimport os")
        diags = check_security(tree, idx)
        assert diags[0].line == 2


# ---------------------------------------------------------------------------
# check_imports
# ---------------------------------------------------------------------------


class TestCheckImports:
    def test_correct_module_no_diag(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        tree = parse("from vtkRenderingCore import vtkActor")
        diags = check_imports(tree, idx)
        assert diags == []

    def test_wrong_module_produces_unknown_module(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        tree = parse("from vtkFiltersCore import vtkActor")
        diags = check_imports(tree, idx)
        assert len(diags) == 1
        assert diags[0].type == ErrorType.UNKNOWN_MODULE

    def test_unknown_vtk_class_produces_missing_class(self):
        idx = make_mock_index({})
        tree = parse("from vtkRenderingCore import vtkNonExistent")
        diags = check_imports(tree, idx)
        assert any(d.type == ErrorType.MISSING_CLASS for d in diags)

    def test_import_vtkmodules_all_allowed(self):
        idx = make_mock_index({})
        tree = parse("from vtkmodules.all import vtkActor")
        diags = check_imports(tree, idx)
        assert diags == []

    def test_plain_import_vtk_allowed(self):
        idx = make_mock_index({})
        tree = parse("import vtk")
        diags = check_imports(tree, idx)
        assert diags == []

    def test_direct_vtkmodules_import_not_in_allowlist(self):
        idx = make_mock_index({})
        tree = parse("import vtkmodules.vtkRenderingCore")
        diags = check_imports(tree, idx)
        assert any(d.type == ErrorType.UNKNOWN_MODULE for d in diags)

    def test_allowed_direct_vtkmodules_import(self):
        idx = make_mock_index({})
        tree = parse("import vtkmodules.vtkRenderingOpenGL2")
        diags = check_imports(tree, idx)
        assert diags == []

    def test_suggestion_in_wrong_module_diag(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        tree = parse("from vtkFiltersCore import vtkActor")
        diags = check_imports(tree, idx)
        assert diags[0].suggestion is not None
        assert "vtkRenderingCore" in diags[0].suggestion

    def test_non_vtk_from_import_ignored(self):
        idx = make_mock_index({})
        tree = parse("from pathlib import Path")
        diags = check_imports(tree, idx)
        assert diags == []


# ---------------------------------------------------------------------------
# check_constructors
# ---------------------------------------------------------------------------


class TestCheckConstructors:
    def test_known_class_no_diag(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        tree = parse("vtkActor()")
        diags = check_constructors(tree, idx)
        assert diags == []

    def test_unknown_vtk_class_missing_class(self):
        idx = make_mock_index({})
        tree = parse("vtkBadClass()")
        diags = check_constructors(tree, idx)
        assert len(diags) == 1
        assert diags[0].type == ErrorType.MISSING_CLASS

    def test_non_vtk_call_ignored(self):
        idx = make_mock_index({})
        tree = parse("range(10)")
        diags = check_constructors(tree, idx)
        assert diags == []

    def test_line_number_in_diag(self):
        idx = make_mock_index({})
        tree = parse("x = 1\nvtkGhost()")
        diags = check_constructors(tree, idx)
        assert diags[0].line == 2

    def test_class_name_recorded(self):
        idx = make_mock_index({})
        tree = parse("vtkBadClass()")
        diags = check_constructors(tree, idx)
        assert diags[0].class_name == "vtkBadClass"


# ---------------------------------------------------------------------------
# check_methods
# ---------------------------------------------------------------------------


class TestCheckMethods:
    def test_known_method_no_diag(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        # Give the record a method
        idx.get_method.side_effect = lambda c, m: object() if (c == "vtkActor" and m == "SetVisibility") else None
        idx.get_class.return_value.methods = []
        tree = parse("actor = vtkActor()\nactor.SetVisibility(1)")
        diags = check_methods(tree, idx)
        assert diags == []

    def test_unknown_method_produces_missing_method(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        idx.get_method.return_value = None
        tree = parse("actor = vtkActor()\nactor.NonExistentMethod()")
        diags = check_methods(tree, idx)
        assert any(d.type == ErrorType.MISSING_METHOD for d in diags)

    def test_untracked_variable_ignored(self):
        idx = make_mock_index({})
        tree = parse("actor.SetVisibility(1)")
        diags = check_methods(tree, idx)
        assert diags == []

    def test_method_name_and_class_in_diag(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        idx.get_method.return_value = None
        idx.get_class.return_value.methods = []
        tree = parse("actor = vtkActor()\nactor.BadMethod()")
        diags = check_methods(tree, idx)
        assert diags[0].class_name == "vtkActor"
        assert diags[0].method_name == "BadMethod"


# ---------------------------------------------------------------------------
# check_ordering
# ---------------------------------------------------------------------------


class TestCheckOrdering:
    def test_update_before_get_output_no_warning(self):
        idx = make_mock_index({})
        source = "reader.Update()\nout = reader.GetOutput()"
        tree = parse(source)
        diags = check_ordering(tree, idx)
        assert diags == []

    def test_get_output_before_update_warns(self):
        idx = make_mock_index({})
        # check_ordering only triggers on bare expression statements, not assignments
        source = "reader.GetOutput()\nreader.Update()"
        tree = parse(source)
        diags = check_ordering(tree, idx)
        assert any(d.type == ErrorType.PIPELINE_ORDERING for d in diags)

    def test_ordering_diag_is_warning_severity(self):
        idx = make_mock_index({})
        source = "reader.GetOutput()"
        tree = parse(source)
        diags = check_ordering(tree, idx)
        assert all(d.severity == "warning" for d in diags)

    def test_no_get_output_no_diag(self):
        idx = make_mock_index({})
        tree = parse("reader.Update()")
        diags = check_ordering(tree, idx)
        assert diags == []

    def test_suggestion_references_update(self):
        idx = make_mock_index({})
        source = "reader.GetOutput()"
        tree = parse(source)
        diags = check_ordering(tree, idx)
        assert "Update" in (diags[0].suggestion or "")
