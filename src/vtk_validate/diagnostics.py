"""Pydantic models for validation errors and reports."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ErrorType(str, Enum):
    MISSING_CLASS = "MissingClass"
    MISSING_METHOD = "MissingMethod"
    SIGNATURE_MISMATCH = "SignatureMismatch"
    FORBIDDEN_IMPORT = "ForbiddenImport"
    FORBIDDEN_CALL = "ForbiddenCall"
    PIPELINE_ORDERING = "PipelineOrdering"
    UNKNOWN_MODULE = "UnknownModule"


class Diagnostic(BaseModel):
    type: ErrorType
    severity: str = "error"
    line: int = 0
    column: int = 0
    message: str
    class_name: Optional[str] = None
    method_name: Optional[str] = None
    call_expression: Optional[str] = None
    candidate_signatures: list[str] = []
    suggestion: Optional[str] = None


class ValidationReport(BaseModel):
    status: str = "ok"
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    elapsed_ms: float = 0.0
    vtk_version: str = ""

    @classmethod
    def ok(cls, vtk_version: str = "", elapsed_ms: float = 0.0) -> "ValidationReport":
        return cls(status="ok", vtk_version=vtk_version, elapsed_ms=elapsed_ms)

    @classmethod
    def from_diagnostics(
        cls,
        diagnostics: list[Diagnostic],
        vtk_version: str = "",
        elapsed_ms: float = 0.0,
    ) -> "ValidationReport":
        errors = [d for d in diagnostics if d.severity == "error"]
        warnings = [d for d in diagnostics if d.severity == "warning"]
        if errors:
            status = "errors"
        elif warnings:
            status = "warnings"
        else:
            status = "ok"
        return cls(
            status=status,
            diagnostics=diagnostics,
            vtk_version=vtk_version,
            elapsed_ms=elapsed_ms,
        )
