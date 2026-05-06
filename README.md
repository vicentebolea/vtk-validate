# vtk-validate

Library-first AST validation for VTK Python code.

## Installation

```bash
pip install vtk-validate          # library only
pip install vtk-validate[mcp]     # adds optional MCP server entry point
```

## Usage

```python
from vtk_knowledge import VTKAPIIndex
from vtk_validate import validate

index = VTKAPIIndex.from_jsonl("vtk-knowledge-9.3.0.jsonl")
report = validate(source_code, index)
if report.status != "ok":
    for d in report.diagnostics:
        print(f"{d.line}: {d.message}")
```

## Architecture

Part of the [VTK LLM tooling](https://github.com/vicentebolea/vtk-llm-architecture) stack:

- [vtk-knowledge](https://github.com/vicentebolea/vtk-knowledge) — Layer 1: knowledge schema + artifact
- [vtk-index](https://github.com/vicentebolea/vtk-index) — Layer 2: chunking + retrieval
- **vtk-validate** (this repo) — Layer 3: AST validation
- [vtk-mcp](https://github.com/vicentebolea/vtk-mcp) — Layer 4: MCP gateway
