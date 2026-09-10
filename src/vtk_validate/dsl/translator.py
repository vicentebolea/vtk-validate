"""Build translation context for the VTK pipeline DSL.

Rather than calling an LLM itself, this module assembles the DSL grammar and
relevant VTK class context so that an LLM-driven caller (e.g. an MCP client)
can translate a natural language request into the DSL directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .grammar import DSL_GRAMMAR, class_to_slug, method_to_param

if TYPE_CHECKING:
    from vtk_knowledge import VTKAPIIndex

_INSTRUCTIONS = """\
Translate the natural language VTK visualization request below into the pipeline DSL.

INSTRUCTIONS
------------
1. Identify the VTK pipeline stages needed (source -> filter(s) -> mapper/output).
2. Use only the VTK classes listed in the context below.
3. Use only the parameter names shown for each class.
4. Choose short, descriptive variable names.
5. Output ONLY the DSL — no explanation, no markdown, no extra text.
"""


def _build_class_context(query: str, api_index: "VTKAPIIndex", limit: int = 8) -> str:
    """Return a concise block describing classes relevant to *query*."""
    from vtk_validate.tools import vtk_search_classes

    hits = vtk_search_classes(query, api_index, limit=limit)
    if not hits:
        return ""

    lines = ["Relevant VTK classes (slug, VTK name, role, available params):"]
    for hit in hits:
        class_name = hit["class_name"]
        record = api_index.get_class(class_name)
        if record is None:
            continue
        slug = class_to_slug(class_name)
        role = record.role.value if record.role else "unknown"
        synopsis = record.synopsis or hit.get("synopsis", "")
        params = [method_to_param(m) for m in (record.semantic_methods or []) if m.startswith("Set")][:12]
        lines.append(f"- {slug} ({class_name}) [role: {role}] — {synopsis}")
        if params:
            lines.append(f"  params: {', '.join(params)}")

    return "\n".join(lines)


def build_dsl_translation_context(query: str, api_index: "VTKAPIIndex") -> str:
    """Build grammar and relevant-class context for translating *query* into the DSL.

    No LLM call is made here — the caller (typically an LLM-driven MCP client)
    is expected to use this context to write the DSL itself.

    Args:
        query: Natural language description of the desired VTK visualization.
        api_index: Loaded VTKAPIIndex for class lookup.

    Returns:
        A text block combining instructions, the DSL grammar, relevant VTK
        class context, and the original request.
    """
    class_context = _build_class_context(query, api_index)
    parts = [_INSTRUCTIONS, DSL_GRAMMAR]
    if class_context:
        parts.append(class_context)
    parts.append(f"Request: {query}")
    return "\n\n".join(parts)
