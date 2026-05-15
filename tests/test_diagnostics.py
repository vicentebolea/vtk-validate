"""Tests for vtk_validate.diagnostics models."""

from __future__ import annotations

import pytest

from vtk_validate.diagnostics import Diagnostic, ErrorType, ValidationReport


class TestErrorType:
    def test_all_expected_values_present(self):
        names = {e.value for e in ErrorType}
        assert "MissingClass" in names
        assert "MissingMethod" in names
        assert "SignatureMismatch" in names
        assert "ForbiddenImport" in names
        assert "ForbiddenCall" in names
        assert "PipelineOrdering" in names
        assert "UnknownModule" in names

    def test_is_string_enum(self):
        assert isinstance(ErrorType.MISSING_CLASS, str)


class TestDiagnostic:
    def test_basic_creation(self):
        d = Diagnostic(type=ErrorType.MISSING_CLASS, message="Class not found.")
        assert d.type == ErrorType.MISSING_CLASS
        assert d.message == "Class not found."

    def test_default_severity_is_error(self):
        d = Diagnostic(type=ErrorType.MISSING_CLASS, message="x")
        assert d.severity == "error"

    def test_default_line_and_column(self):
        d = Diagnostic(type=ErrorType.MISSING_CLASS, message="x")
        assert d.line == 0
        assert d.column == 0

    def test_suggestion_is_none_by_default(self):
        d = Diagnostic(type=ErrorType.MISSING_CLASS, message="x")
        assert d.suggestion is None

    def test_candidate_signatures_default_empty(self):
        d = Diagnostic(type=ErrorType.MISSING_CLASS, message="x")
        assert d.candidate_signatures == []

    def test_all_fields_settable(self):
        d = Diagnostic(
            type=ErrorType.MISSING_METHOD,
            severity="warning",
            line=10,
            column=5,
            message="Method not found.",
            class_name="vtkActor",
            method_name="SetBadProp",
            call_expression="actor.SetBadProp()",
            candidate_signatures=["SetProperty(prop)"],
            suggestion="SetProperty",
        )
        assert d.line == 10
        assert d.class_name == "vtkActor"
        assert d.suggestion == "SetProperty"


class TestValidationReport:
    def test_ok_factory(self):
        r = ValidationReport.ok(vtk_version="9.3.0", elapsed_ms=1.5)
        assert r.status == "ok"
        assert r.vtk_version == "9.3.0"
        assert r.elapsed_ms == pytest.approx(1.5)
        assert r.diagnostics == []

    def test_from_diagnostics_empty_is_ok(self):
        r = ValidationReport.from_diagnostics([])
        assert r.status == "ok"

    def test_from_diagnostics_with_errors(self):
        d = Diagnostic(type=ErrorType.MISSING_CLASS, severity="error", message="x")
        r = ValidationReport.from_diagnostics([d])
        assert r.status == "errors"

    def test_from_diagnostics_with_warnings_only(self):
        d = Diagnostic(type=ErrorType.PIPELINE_ORDERING, severity="warning", message="x")
        r = ValidationReport.from_diagnostics([d])
        assert r.status == "warnings"

    def test_from_diagnostics_mixed_error_wins(self):
        e = Diagnostic(type=ErrorType.MISSING_CLASS, severity="error", message="x")
        w = Diagnostic(type=ErrorType.PIPELINE_ORDERING, severity="warning", message="y")
        r = ValidationReport.from_diagnostics([e, w])
        assert r.status == "errors"

    def test_from_diagnostics_stores_all(self):
        d1 = Diagnostic(type=ErrorType.MISSING_CLASS, message="a")
        d2 = Diagnostic(type=ErrorType.FORBIDDEN_IMPORT, message="b")
        r = ValidationReport.from_diagnostics([d1, d2])
        assert len(r.diagnostics) == 2

    def test_vtk_version_stored(self):
        r = ValidationReport.from_diagnostics([], vtk_version="9.6.1")
        assert r.vtk_version == "9.6.1"

    def test_elapsed_ms_stored(self):
        r = ValidationReport.from_diagnostics([], elapsed_ms=12.5)
        assert r.elapsed_ms == pytest.approx(12.5)
