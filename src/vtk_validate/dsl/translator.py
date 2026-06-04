"""Translate natural language VTK requests into the pipeline DSL.

Requires the ``litellm`` optional dependency:
    pip install vtk-validate[translate]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .grammar import DSL_GRAMMAR, class_to_slug, method_to_param

if TYPE_CHECKING:
    from vtk_knowledge import VTKAPIIndex

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = f"""\
You translate natural language VTK visualization requests into a structured pipeline DSL.

{DSL_GRAMMAR}

INSTRUCTIONS
------------
1. Identify the VTK pipeline stages needed (source → filter(s) → mapper/output).
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
        params = [
            method_to_param(m)
            for m in (record.semantic_methods or [])
            if m.startswith("Set")
        ][:12]
        lines.append(f"- {slug} ({class_name}) [role: {role}] — {synopsis}")
        if params:
            lines.append(f"  params: {', '.join(params)}")

    return "\n".join(lines)


def translate_to_dsl(
    query: str,
    api_index: "VTKAPIIndex",
    model: str = "anthropic/claude-haiku-4-5",
    base_url: str | None = None,
    api_key: str | None = None,
) -> str:
    """Translate a natural language VTK request into the pipeline DSL.

    Args:
        query: Natural language description of the desired VTK visualization.
        api_index: Loaded VTKAPIIndex for class lookup.
        model: LiteLLM model identifier. For Ollama use e.g. ``ollama/llama3``.
        base_url: Custom API base URL for OpenAI-compatible endpoints such as
            Ollama (``http://localhost:11434``) or LM Studio.
        api_key: API key for the endpoint. Pass ``"ollama"`` for Ollama (which
            requires a non-empty but otherwise arbitrary key).

    Returns:
        DSL string ready to be passed to the vtk-prompt code generator.

    Raises:
        ImportError: If litellm is not installed.
        RuntimeError: If the LLM call fails.
    """
    try:
        import litellm
    except ImportError as e:
        raise ImportError(
            "litellm is required for DSL translation. "
            "Install with: pip install vtk-validate[translate]"
        ) from e

    class_context = _build_class_context(query, api_index)
    user_content = f"Request: {query}"
    if class_context:
        user_content = f"{class_context}\n\n{user_content}"

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    kwargs: dict = {"model": model, "messages": messages, "temperature": 0.1}
    if base_url:
        kwargs["api_base"] = base_url
    if api_key:
        kwargs["api_key"] = api_key

    try:
        response = litellm.completion(**kwargs)
        dsl = response.choices[0].message.content.strip()
        logger.debug("DSL translation result:\n%s", dsl)
        return dsl
    except Exception as exc:
        raise RuntimeError(f"DSL translation failed: {exc}") from exc
