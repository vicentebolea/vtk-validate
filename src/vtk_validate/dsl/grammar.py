"""DSL grammar specification and slug-conversion utilities."""

from __future__ import annotations

import re

DSL_GRAMMAR = """\
VTK Pipeline DSL
================

SYNTAX
------
# Source (0 input ports) — use 'create':
create <class_slug> called <var> with <param> <value> [with <param> <value> ...]

# Filter (>0 input ports) — repeat the slug twice, then name the input:
<class_slug> <class_slug> the <source_var> called <var> with <param> <value> [...]

# Auxiliary object (lookup table, property, transfer function):
define <class_slug> called <var> with <param> <value> [...]

# Connect an object attribute to another object:
add the <var> with <attr> the <other_var>

# Add a widget (scalar bar, axes, etc.):
add <widget_slug> called <var> with <param> <value> [...]

# Final render (must be last):
render render with background [r,g,b]

NAMING RULES
------------
<class_slug>  VTK class without 'vtk' prefix, CamelCase converted to snake_case:
  vtkPlaneSource      → plane_source
  vtkElevationFilter  → elevation_filter
  vtkArrayCalculator  → array_calculator
  vtkWarpScalar       → warp_scalar
  vtkLookupTable      → lookup_table
  vtkScalarBarActor   → scalar_bar_actor

<param>  VTK setter without 'Set' prefix, CamelCase converted to snake_case:
  SetXResolution          → x_resolution
  SetScalarRange          → scalar_range
  SetHueRange             → hue_range
  SetScaleFactor          → scale_factor
  SetInputArrayToProcess  → input_array_to_process

<var>  Any identifier chosen by the author to reference the object later.

EXAMPLE
-------
create plane_source called source with x_resolution 60 with y_resolution 60 with origin [-1.0,-1.0,0.0] with point1 [1.0,-1.0,0.0] with point2 [-1.0,1.0,0.0]
elevation_filter elevation_filter the source called elevation with low_point [-1.0,-1.0,0.0] with high_point [1.0,1.0,0.0] with scalar_range [0.0,1.0]
array_calculator array_calculator the elevation called calculator with function 'sin(3.14159 * x) * cos(3.14159 * y)' with result_array_name 'SinCos' with result_array_type 10
warp_scalar warp_scalar the calculator called warp with input_array_to_process [0,0,0,0,SinCos] with scale_factor 0.25
define lookup_table called lut with hue_range [0.667,0.0] with range [-1.0,1.0]
add the warp with lookup_table the lut
add scalar_bar_actor called scalar_bar with lookup_table the lut with title 'sin(pix)*cos(piy)' with number_of_labels 5 with width 0.08 with height 0.6 with position [0.9,0.2]
render render with background [0.2,0.302,0.4]
"""


def class_to_slug(class_name: str) -> str:
    """Convert a VTK class name to a DSL slug.

    vtkPlaneSource → plane_source
    """
    name = class_name[3:] if class_name.startswith("vtk") else class_name
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def method_to_param(method_name: str) -> str:
    """Convert a VTK setter name to a DSL parameter name.

    SetXResolution → x_resolution
    """
    name = method_name[3:] if method_name.startswith("Set") else method_name
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
