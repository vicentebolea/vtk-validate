"""vtk-validate — library-first AST validation for VTK Python code."""

__version__ = "1.0.0"

from .api import validate
from .diagnostics import Diagnostic, ErrorType, ValidationReport
from .dsl import DSL_GRAMMAR, class_to_slug, is_dsl, method_to_param, translate_to_dsl

__all__ = [
    "validate",
    "Diagnostic",
    "ErrorType",
    "ValidationReport",
    "DSL_GRAMMAR",
    "class_to_slug",
    "is_dsl",
    "method_to_param",
    "translate_to_dsl",
]
