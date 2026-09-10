"""VTK Pipeline DSL — grammar, detection, and translation."""

from .detector import is_dsl
from .grammar import DSL_GRAMMAR, class_to_slug, method_to_param
from .translator import build_dsl_translation_context

__all__ = ["DSL_GRAMMAR", "build_dsl_translation_context", "class_to_slug", "is_dsl", "method_to_param"]
