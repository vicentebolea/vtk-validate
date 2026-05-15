"""18 high-level tool functions used by the MCP server and library consumers.

Each function accepts an ``index: VTKAPIIndex`` so they can be called
in-process without going through a protocol.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from vtk_knowledge import VTKAPIIndex


def vtk_get_class_info(class_name: str, index: "VTKAPIIndex") -> dict[str, Any]:
    r = index.get_class(class_name)
    if r is None:
        return {"error": f"Class '{class_name}' not found."}
    return r.model_dump()


def vtk_search_classes(query: str, index: "VTKAPIIndex", limit: int = 10) -> list[dict[str, Any]]:
    results = index.search_classes(query, limit=limit)
    return [{"class_name": r.class_name, "module_name": r.module_name, "synopsis": r.synopsis or ""} for r in results]


def vtk_get_method_info(class_name: str, method_name: str, index: "VTKAPIIndex") -> dict[str, Any]:
    m = index.get_method(class_name, method_name)
    if m is None:
        return {"error": f"Method '{method_name}' not found on '{class_name}'."}
    return m.model_dump()


def vtk_get_class_role(class_name: str, index: "VTKAPIIndex") -> str:
    return index.get_class_role(class_name) or "unknown"


def vtk_get_class_input_datatype(class_name: str, index: "VTKAPIIndex") -> str:
    return index.get_class_input_datatype(class_name) or ""


def vtk_get_class_output_datatype(class_name: str, index: "VTKAPIIndex") -> str:
    return index.get_class_output_datatype(class_name) or ""


def vtk_get_class_semantic_methods(class_name: str, index: "VTKAPIIndex") -> list[str]:
    return index.get_class_semantic_methods(class_name)


def vtk_get_class_doc(class_name: str, index: "VTKAPIIndex") -> str:
    return index.get_class_doc(class_name) or ""


def vtk_validate_import(import_statement: str, index: "VTKAPIIndex") -> dict[str, Any]:
    from .api import validate

    report = validate(import_statement, index)
    return {
        "valid": report.status == "ok",
        "diagnostics": [d.model_dump() for d in report.diagnostics],
    }


def vtk_is_a_class(class_name: str, index: "VTKAPIIndex") -> bool:
    return index.has_class(class_name)


def vtk_get_class_module(class_name: str, index: "VTKAPIIndex") -> str:
    return index.get_class_module(class_name) or ""


def vtk_get_class_methods(class_name: str, index: "VTKAPIIndex") -> list[dict[str, Any]]:
    return [m.model_dump() for m in index.get_class_methods(class_name)]


def vtk_get_module_classes(module: str, index: "VTKAPIIndex") -> list[str]:
    return index.classes_in_module(module)


def vtk_get_method_doc(class_name: str, method_name: str, index: "VTKAPIIndex") -> str:
    return index.get_method_doc(class_name, method_name) or ""


def vtk_get_method_signature(class_name: str, method_name: str, index: "VTKAPIIndex") -> str:
    return index.get_method_signature(class_name, method_name) or ""


def vtk_get_class_synopsis(class_name: str, index: "VTKAPIIndex") -> str:
    return index.get_class_synopsis(class_name) or ""


def vtk_get_class_action_phrase(class_name: str, index: "VTKAPIIndex") -> str:
    return index.get_class_action_phrase(class_name) or ""


def vtk_get_class_visibility(class_name: str, index: "VTKAPIIndex") -> Optional[float]:
    return index.get_class_visibility(class_name)
