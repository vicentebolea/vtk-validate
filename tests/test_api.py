"""Tests for vtk_validate.api.validate()."""

from __future__ import annotations

from helpers import make_mock_index

from vtk_validate.api import validate
from vtk_validate.diagnostics import ErrorType


class TestValidate:
    def test_clean_code_returns_ok(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        report = validate("x = 1 + 1", idx)
        assert report.status == "ok"

    def test_security_violation_returns_errors(self):
        idx = make_mock_index({})
        report = validate("import os", idx)
        assert report.status == "errors"
        assert any(d.type == ErrorType.FORBIDDEN_IMPORT for d in report.diagnostics)

    def test_unknown_class_returns_errors(self):
        idx = make_mock_index({})
        report = validate("vtkNonExistent()", idx)
        assert report.status == "errors"

    def test_ordering_issue_returns_warnings(self):
        idx = make_mock_index({})
        # check_ordering only triggers on bare expression statements, not assignments
        source = "reader.GetOutput()"
        report = validate(source, idx)
        assert report.status == "warnings"

    def test_syntax_error_returns_errors(self):
        idx = make_mock_index({})
        report = validate("def (:", idx)
        assert report.status == "errors"

    def test_vtk_version_from_index(self):
        idx = make_mock_index({})
        idx.vtk_version = "9.6.1"
        report = validate("x = 1", idx)
        assert report.vtk_version == "9.6.1"

    def test_elapsed_ms_positive(self):
        idx = make_mock_index({})
        report = validate("x = 1", idx)
        assert report.elapsed_ms >= 0.0

    def test_multiple_errors_collected(self):
        idx = make_mock_index({})
        source = "import os\nimport subprocess"
        report = validate(source, idx)
        assert len(report.diagnostics) >= 2

    def test_empty_source_is_ok(self):
        idx = make_mock_index({})
        report = validate("", idx)
        assert report.status == "ok"

    def test_valid_vtk_import_no_error(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        report = validate("from vtkRenderingCore import vtkActor", idx)
        assert report.status == "ok"
