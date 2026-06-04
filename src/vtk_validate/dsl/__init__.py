"""VTK Pipeline DSL — grammar, detection, and translation."""

from .detector import is_dsl
from .grammar import DSL_GRAMMAR, class_to_slug, method_to_param
from .translator import translate_to_dsl

__all__ = ["DSL_GRAMMAR", "class_to_slug", "is_dsl", "method_to_param", "translate_to_dsl"]
