"""CLI for vtk-validate — query the VTK API and validate Python scripts.

Commands:
    vtk-validate check    FILE              -- AST-validate a Python file
    vtk-validate class    CLASS_NAME        -- show class synopsis, role, methods
    vtk-validate search   QUERY            -- search VTK classes by name/description
    vtk-validate method   CLASS METHOD     -- show method signature and doc
    vtk-validate module   MODULE_NAME      -- list classes in a VTK module
"""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(
    name="vtk-validate",
    help="AST validation and API lookup for VTK Python code.",
    no_args_is_help=True,
)

_ARTIFACT_OPTION = typer.Option(
    None,
    "--knowledge-artifact",
    "-k",
    envvar="VTK_KNOWLEDGE_PATH",
    help="Path to vtk-knowledge JSONL artifact (or set VTK_KNOWLEDGE_PATH).",
)


def _load_index(artifact: str | None):
    try:
        from vtk_knowledge import VTKAPIIndex
    except ImportError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    if not artifact:
        typer.echo("Error: --knowledge-artifact is required (or set VTK_KNOWLEDGE_PATH).", err=True)
        raise typer.Exit(1)

    try:
        return VTKAPIIndex.from_jsonl(artifact)
    except Exception as e:
        typer.echo(f"Error: failed to load knowledge artifact: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def check(
    file: Path = typer.Argument(..., help="Python file to validate."),
    knowledge_artifact: str | None = _ARTIFACT_OPTION,
) -> None:
    """Validate a VTK Python file and print diagnostics."""
    try:
        from .api import validate
    except ImportError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    if not file.exists():
        typer.echo(f"Error: file not found: {file}", err=True)
        raise typer.Exit(1)

    try:
        index = _load_index(knowledge_artifact)
        source = file.read_text()
        report = validate(source, index)
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    if report.status == "ok":
        typer.echo(f"OK — {file} passed validation ({report.elapsed_ms:.1f} ms)")
        return

    for d in report.diagnostics:
        prefix = f"{file}:{d.line}"
        tag = "error" if d.severity == "error" else "warning"
        typer.echo(f"{prefix}: {tag}: {d.message}")
        if d.suggestion:
            typer.echo(f"  suggestion: {d.suggestion}")

    total = len(report.diagnostics)
    errors = sum(1 for d in report.diagnostics if d.severity == "error")
    warnings = total - errors
    typer.echo(f"\n{errors} error(s), {warnings} warning(s) in {report.elapsed_ms:.1f} ms")
    if errors:
        raise typer.Exit(1)


@app.command(name="class-info")
def class_info(
    class_name: str = typer.Argument(..., help="VTK class name, e.g. vtkActor."),
    knowledge_artifact: str | None = _ARTIFACT_OPTION,
) -> None:
    """Show synopsis, role, module, visibility, and methods for a VTK class."""
    try:
        from . import tools as T
    except ImportError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    try:
        index = _load_index(knowledge_artifact)
        info = T.vtk_get_class_info(class_name, index)
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    if "error" in info:
        typer.echo(f"Error: {info['error']}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Class:      {class_name}")
    typer.echo(f"Module:     {T.vtk_get_class_module(class_name, index) or '-'}")
    typer.echo(f"Role:       {T.vtk_get_class_role(class_name, index)}")
    visibility = T.vtk_get_class_visibility(class_name, index)
    typer.echo(f"Visibility: {visibility:.2f}" if visibility is not None else "Visibility: -")
    synopsis = T.vtk_get_class_synopsis(class_name, index)
    if synopsis:
        typer.echo(f"Synopsis:   {synopsis}")
    action = T.vtk_get_class_action_phrase(class_name, index)
    if action:
        typer.echo(f"Action:     {action}")
    input_dt = T.vtk_get_class_input_datatype(class_name, index)
    output_dt = T.vtk_get_class_output_datatype(class_name, index)
    if input_dt:
        typer.echo(f"Input:      {input_dt}")
    if output_dt:
        typer.echo(f"Output:     {output_dt}")
    methods = T.vtk_get_class_methods(class_name, index)
    if methods:
        names = [m.get("name", "") for m in methods[:10]]
        suffix = f" (+{len(methods) - 10} more)" if len(methods) > 10 else ""
        typer.echo(f"Methods:    {', '.join(names)}{suffix}")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (class name or description)."),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of results."),
    knowledge_artifact: str | None = _ARTIFACT_OPTION,
) -> None:
    """Search VTK classes by name or description."""
    try:
        from . import tools as T
    except ImportError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    try:
        index = _load_index(knowledge_artifact)
        results = T.vtk_search_classes(query, index, limit=limit)
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    if not results:
        typer.echo("No results.")
        return

    for r in results:
        synopsis = r.get("synopsis") or ""
        snippet = f" — {synopsis[:80]}" if synopsis else ""
        typer.echo(f"{r['class_name']} ({r['module_name']}){snippet}")


@app.command(name="method-info")
def method_info(
    class_name: str = typer.Argument(..., help="VTK class name."),
    method_name: str = typer.Argument(..., help="Method name."),
    knowledge_artifact: str | None = _ARTIFACT_OPTION,
) -> None:
    """Show signature and documentation for a VTK method."""
    try:
        from . import tools as T
    except ImportError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    try:
        index = _load_index(knowledge_artifact)
        info = T.vtk_get_method_info(class_name, method_name, index)
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    if "error" in info:
        typer.echo(f"Error: {info['error']}", err=True)
        raise typer.Exit(1)

    sig = T.vtk_get_method_signature(class_name, method_name, index)
    doc = T.vtk_get_method_doc(class_name, method_name, index)
    typer.echo(f"Method:    {class_name}.{method_name}")
    if sig:
        typer.echo(f"Signature: {sig}")
    if doc:
        typer.echo(f"Doc:       {doc}")


@app.command(name="module")
def module_classes(
    module_name: str = typer.Argument(..., help="VTK module name, e.g. vtkRenderingCore."),
    knowledge_artifact: str | None = _ARTIFACT_OPTION,
) -> None:
    """List all classes in a VTK module."""
    try:
        from . import tools as T
    except ImportError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    try:
        index = _load_index(knowledge_artifact)
        classes = T.vtk_get_module_classes(module_name, index)
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    if not classes:
        typer.echo(f"No classes found in module '{module_name}'.")
        return

    typer.echo(f"{len(classes)} class(es) in {module_name}:")
    for name in sorted(classes):
        typer.echo(f"  {name}")


if __name__ == "__main__":
    app()
