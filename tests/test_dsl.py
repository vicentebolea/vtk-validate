"""Tests for vtk_validate.dsl — grammar, detector, and translator."""

from __future__ import annotations

from unittest.mock import MagicMock

from helpers import make_mock_index, make_mock_record

from vtk_validate.dsl import DSL_GRAMMAR, class_to_slug, is_dsl, method_to_param

# ── grammar utilities ───────────────────────────────────────────────────────


class TestClassToSlug:
    def test_strips_vtk_prefix(self):
        assert class_to_slug("vtkPlaneSource") == "plane_source"

    def test_camel_to_snake(self):
        assert class_to_slug("vtkArrayCalculator") == "array_calculator"
        assert class_to_slug("vtkWarpScalar") == "warp_scalar"
        assert class_to_slug("vtkLookupTable") == "lookup_table"

    def test_no_vtk_prefix_unchanged_case(self):
        assert class_to_slug("PlaneSource") == "plane_source"

    def test_all_lowercase_class(self):
        assert class_to_slug("vtkactor") == "actor"


class TestMethodToParam:
    def test_strips_set_prefix(self):
        assert method_to_param("SetXResolution") == "x_resolution"

    def test_camel_to_snake(self):
        assert method_to_param("SetScalarRange") == "scalar_range"
        assert method_to_param("SetHueRange") == "hue_range"
        assert method_to_param("SetInputArrayToProcess") == "input_array_to_process"

    def test_no_set_prefix_passthrough(self):
        assert method_to_param("GetOutput") == "get_output"

    def test_single_word(self):
        assert method_to_param("SetRadius") == "radius"


class TestDslGrammar:
    def test_grammar_is_string(self):
        assert isinstance(DSL_GRAMMAR, str)
        assert len(DSL_GRAMMAR) > 0

    def test_grammar_contains_key_keywords(self):
        for kw in ("create", "define", "render", "called", "with"):
            assert kw in DSL_GRAMMAR

    def test_grammar_contains_example(self):
        assert "plane_source" in DSL_GRAMMAR
        assert "x_resolution" in DSL_GRAMMAR


# ── detector ────────────────────────────────────────────────────────────────


class TestIsDsl:
    def test_create_verb(self):
        assert is_dsl("create plane_source called src with x_resolution 60")

    def test_define_verb(self):
        assert is_dsl("define lookup_table called lut with hue_range [0,1]")

    def test_render_verb(self):
        assert is_dsl("render render with background [0,0,0]")

    def test_dsl_marker_called(self):
        assert is_dsl("warp_scalar warp_scalar the src called warp with scale_factor 0.5")

    def test_natural_language_is_not_dsl(self):
        assert not is_dsl("create a red sphere with radius 0.5")

    def test_empty_string_is_not_dsl(self):
        assert not is_dsl("")

    def test_vague_prompt_is_not_dsl(self):
        assert not is_dsl("make a visualization of a sine wave surface")


# ── translator (no LLM) ─────────────────────────────────────────────────────


class TestBuildDslTranslationContext:
    def _make_rich_index(self):
        """Return a mock index with realistic records for plane + elevation."""
        idx = make_mock_index({"vtkPlaneSource": "vtkFiltersSources", "vtkElevationFilter": "vtkFiltersCore"})

        plane = make_mock_record("vtkPlaneSource", "vtkFiltersSources")
        plane.role = MagicMock()
        plane.role.value = "source"
        plane.synopsis = "Create a polygonal plane."
        plane.semantic_methods = ["SetXResolution", "SetYResolution", "SetOrigin"]

        elev = make_mock_record("vtkElevationFilter", "vtkFiltersCore")
        elev.role = MagicMock()
        elev.role.value = "filter"
        elev.synopsis = "Generate elevation scalar values."
        elev.semantic_methods = ["SetLowPoint", "SetHighPoint", "SetScalarRange"]

        def _get_class(name):
            return {"vtkPlaneSource": plane, "vtkElevationFilter": elev}.get(name)

        idx.get_class.side_effect = _get_class
        return idx

    def test_includes_grammar(self):
        from vtk_validate.dsl.translator import build_dsl_translation_context

        idx = make_mock_index({})
        result = build_dsl_translation_context("make a plane", idx)

        assert "plane_source" in result
        assert "SYNTAX" in result

    def test_includes_query(self):
        from vtk_validate.dsl.translator import build_dsl_translation_context

        idx = make_mock_index({})
        result = build_dsl_translation_context("make a simple plane", idx)

        assert "make a simple plane" in result

    def test_class_context_included(self):
        """Relevant class slugs and params appear in the returned context."""
        from vtk_validate.dsl.translator import build_dsl_translation_context

        idx = self._make_rich_index()
        result = build_dsl_translation_context("make a plane", idx)

        assert "plane_source" in result
        assert "x_resolution" in result

    def test_no_llm_call(self):
        """No network/module dependency is required — pure string assembly."""
        from vtk_validate.dsl.translator import build_dsl_translation_context

        idx = make_mock_index({})
        result = build_dsl_translation_context("make a sphere", idx)

        assert isinstance(result, str)
        assert len(result) > 0
