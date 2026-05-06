"""vtk-validate — library-first AST validation for VTK Python code."""

__version__ = "1.0.0"

from .api import validate
from .diagnostics import Diagnostic, ErrorType, ValidationReport

__all__ = ["validate", "Diagnostic", "ErrorType", "ValidationReport"]
