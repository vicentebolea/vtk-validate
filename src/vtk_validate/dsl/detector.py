"""Heuristic detector for the VTK pipeline DSL."""

from __future__ import annotations

# Keywords that appear in DSL statements but not in typical natural language prompts
_DSL_MARKERS = frozenset({"called", "define", "warp_scalar", "array_calculator", "lookup_table"})


def is_dsl(text: str) -> bool:
    """Return True if *text* looks like a VTK pipeline DSL prompt.

    Uses a simple heuristic: the text contains DSL-specific keywords or
    starts with the DSL render pattern (``render render``).
    """
    if any(marker in text for marker in _DSL_MARKERS):
        return True
    # DSL render line is always "render render with ..." — the double word is distinctive
    return text.strip().lower().startswith("render render")
