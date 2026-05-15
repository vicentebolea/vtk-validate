# vtk-validate

Library-first AST validation and API lookup for VTK Python code.

## Installation

```bash
pip install vtk-validate
```

`vtk-knowledge` is not on PyPI; install it from GitHub first:

```bash
pip install "vtk-knowledge @ git+https://github.com/vicentebolea/vtk-knowledge.git"
pip install vtk-validate
```

## CLI

All commands require a path to a vtk-knowledge JSONL artifact, supplied via
`--knowledge-artifact / -k` or the `VTK_KNOWLEDGE_PATH` environment variable.

```bash
export VTK_KNOWLEDGE_PATH=/path/to/vtk-knowledge-9.3.0.jsonl
```

### check — validate a Python file

```
vtk-validate check script.py
```

Runs AST checks (imports, constructors, methods, pipeline ordering, security)
and prints each diagnostic with file, line, severity, message, and suggestion.
Exits non-zero when there are errors (warnings alone do not fail).

```
script.py:4: error: Class 'vtkSphereSrc' not found in the VTK API.
  suggestion: vtkSphereSource
script.py:7: warning: GetOutput() called on 'sphere' before Update().
  suggestion: sphere.Update()

1 error(s), 1 warning(s) in 2.3 ms
```

### class-info — look up a class

```
vtk-validate class-info vtkActor
```

```
Class:      vtkActor
Module:     vtkRenderingCore
Role:       actor
Visibility: 0.95
Synopsis:   Represents an object (geometry and properties) in a rendered scene.
Action:     renders geometry and properties in a scene
Input:      vtkMapper
Methods:    SetMapper, GetMapper, SetVisibility, GetVisibility, ...
```

### search — find classes by name or description

```
vtk-validate search "sphere source" --limit 5
```

```
vtkSphereSource (vtkFiltersSources) — Create a polygonal sphere centered at the origin.
vtkCylinderSource (vtkFiltersSources) — Create a polygonal cylinder centered at the origin.
...
```

### method-info — inspect a method

```
vtk-validate method-info vtkSphereSource SetRadius
```

```
Method:    vtkSphereSource.SetRadius
Signature: SetRadius(double r) -> None
Doc:       Set the radius of the sphere. Default is 0.5.
```

### module — list classes in a module

```
vtk-validate module vtkRenderingCore
```

```
42 class(es) in vtkRenderingCore:
  vtkActor
  vtkActor2D
  vtkCamera
  ...
```

## Python API

```python
from vtk_knowledge import VTKAPIIndex
from vtk_validate import validate

index = VTKAPIIndex.from_jsonl("vtk-knowledge-9.3.0.jsonl")
report = validate(source_code, index)
if report.status != "ok":
    for d in report.diagnostics:
        print(f"{d.line}: [{d.severity}] {d.message}")
        if d.suggestion:
            print(f"  suggestion: {d.suggestion}")
```

The 18 lookup functions used by the CLI are also available directly:

```python
from vtk_validate import tools as T

info   = T.vtk_get_class_info("vtkActor", index)
hits   = T.vtk_search_classes("sphere", index, limit=5)
method = T.vtk_get_method_info("vtkSphereSource", "SetRadius", index)
valid  = T.vtk_validate_import("from vtkRenderingCore import vtkActor", index)
```

### What is validated

| Check | Description |
|---|---|
| Security | Flags `import os/subprocess/...` and `eval()`/`exec()` |
| Imports | `from vtkmodules.X import Y` verified against the module map |
| Constructors | Unknown VTK class names flagged with difflib suggestions |
| Methods | Method calls on typed variables checked against the API |
| Pipeline ordering | `GetOutput()` before `Update()` flagged as a warning |

## Architecture

Part of the [VTK LLM tooling](https://github.com/vicentebolea/vtk-llm-architecture) stack:

- [vtk-knowledge](https://github.com/vicentebolea/vtk-knowledge) — Layer 1: knowledge schema + artifact
- [vtk-index](https://github.com/vicentebolea/vtk-index) — Layer 2: chunking + retrieval
- **vtk-validate** (this repo) — Layer 3: AST validation + API lookup CLI
- [vtk-mcp](https://github.com/vicentebolea/vtk-mcp) — Layer 4: MCP gateway
