"""Thin FastMCP entry point wrapping vtk_validate.tools functions."""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from vtk_knowledge import VTKAPIIndex
from vtk_validate import tools as T

mcp = FastMCP("vtk-validate")

# The index is loaded once at startup (passed via CLI arg or env var).
_index: VTKAPIIndex | None = None


def _get_index() -> VTKAPIIndex:
    if _index is None:
        raise RuntimeError("VTKAPIIndex not initialised. Call init_server() first.")
    return _index


def init_server(jsonl_path: Path) -> None:
    global _index
    _index = VTKAPIIndex.from_jsonl(jsonl_path)


# Register all 18 tools
@mcp.tool()
def vtk_get_class_info(class_name: str) -> dict:
    return T.vtk_get_class_info(class_name, _get_index())

@mcp.tool()
def vtk_search_classes(query: str, limit: int = 10) -> list:
    return T.vtk_search_classes(query, _get_index(), limit=limit)

@mcp.tool()
def vtk_get_method_info(class_name: str, method_name: str) -> dict:
    return T.vtk_get_method_info(class_name, method_name, _get_index())

@mcp.tool()
def vtk_get_class_role(class_name: str) -> str:
    return T.vtk_get_class_role(class_name, _get_index())

@mcp.tool()
def vtk_get_class_input_datatype(class_name: str) -> str:
    return T.vtk_get_class_input_datatype(class_name, _get_index())

@mcp.tool()
def vtk_get_class_output_datatype(class_name: str) -> str:
    return T.vtk_get_class_output_datatype(class_name, _get_index())

@mcp.tool()
def vtk_get_class_semantic_methods(class_name: str) -> list:
    return T.vtk_get_class_semantic_methods(class_name, _get_index())

@mcp.tool()
def vtk_get_class_doc(class_name: str) -> str:
    return T.vtk_get_class_doc(class_name, _get_index())

@mcp.tool()
def vtk_validate_import(import_statement: str) -> dict:
    return T.vtk_validate_import(import_statement, _get_index())

@mcp.tool()
def vtk_is_a_class(class_name: str) -> bool:
    return T.vtk_is_a_class(class_name, _get_index())

@mcp.tool()
def vtk_get_class_module(class_name: str) -> str:
    return T.vtk_get_class_module(class_name, _get_index())

@mcp.tool()
def vtk_get_class_methods(class_name: str) -> list:
    return T.vtk_get_class_methods(class_name, _get_index())

@mcp.tool()
def vtk_get_module_classes(module: str) -> list:
    return T.vtk_get_module_classes(module, _get_index())

@mcp.tool()
def vtk_get_method_doc(class_name: str, method_name: str) -> str:
    return T.vtk_get_method_doc(class_name, method_name, _get_index())

@mcp.tool()
def vtk_get_method_signature(class_name: str, method_name: str) -> str:
    return T.vtk_get_method_signature(class_name, method_name, _get_index())

@mcp.tool()
def vtk_get_class_synopsis(class_name: str) -> str:
    return T.vtk_get_class_synopsis(class_name, _get_index())

@mcp.tool()
def vtk_get_class_action_phrase(class_name: str) -> str:
    return T.vtk_get_class_action_phrase(class_name, _get_index())

@mcp.tool()
def vtk_get_class_visibility(class_name: str) -> float | None:
    return T.vtk_get_class_visibility(class_name, _get_index())


def main() -> None:
    import argparse, os
    parser = argparse.ArgumentParser(description="vtk-validate MCP server")
    parser.add_argument(
        "--knowledge-artifact",
        default=os.environ.get("VTK_KNOWLEDGE_PATH", ""),
        help="Path to vtk-knowledge JSONL artifact.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
    )
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if not args.knowledge_artifact:
        parser.error("--knowledge-artifact is required (or set VTK_KNOWLEDGE_PATH)")

    init_server(Path(args.knowledge_artifact))

    if args.transport == "http":
        import asyncio
        asyncio.run(mcp.run_http_async(host="127.0.0.1", port=args.port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
