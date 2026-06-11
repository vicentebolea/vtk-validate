"""Tests for vtk_validate.dsl — grammar, detector, and translator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
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


class TestTranslateToDsl:
    def _make_rich_index(self):
        """Return a mock index with realistic records for plane + elevation."""
        idx = make_mock_index({"vtkPlaneSource": "vtkFiltersSources",
                               "vtkElevationFilter": "vtkFiltersCore"})

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

    def test_missing_litellm_raises_import_error(self):
        from vtk_validate.dsl.translator import translate_to_dsl

        idx = make_mock_index({})
        with patch.dict("sys.modules", {"litellm": None}):
            with pytest.raises(ImportError, match="litellm"):
                translate_to_dsl("make a plane", idx)

    def test_calls_litellm_with_query(self):
        from vtk_validate.dsl.translator import translate_to_dsl

        idx = self._make_rich_index()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = (
            "create plane_source called src with x_resolution 10"
        )

        mock_litellm = MagicMock()
        mock_litellm.completion.return_value = mock_response

        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            translate_to_dsl("make a simple plane", idx, model="test-model")

        mock_litellm.completion.assert_called_once()
        call_kwargs = mock_litellm.completion.call_args
        assert call_kwargs.kwargs["model"] == "test-model"
        messages = call_kwargs.kwargs["messages"]
        assert any("make a simple plane" in m["content"] for m in messages)

    def test_returns_dsl_string(self):
        from vtk_validate.dsl.translator import translate_to_dsl

        idx = self._make_rich_index()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = (
            "create plane_source called src with x_resolution 10"
        )
        mock_litellm = MagicMock()
        mock_litellm.completion.return_value = mock_response

        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            result = translate_to_dsl("make a plane", idx)

        assert "plane_source" in result

    def test_class_context_included_in_prompt(self):
        """Relevant class slugs and params appear in the user message."""
        from vtk_validate.dsl.translator import translate_to_dsl

        idx = self._make_rich_index()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "create plane_source called src"
        mock_litellm = MagicMock()
        mock_litellm.completion.return_value = mock_response

        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            translate_to_dsl("make a plane", idx)

        messages = mock_litellm.completion.call_args.kwargs["messages"]
        user_content = next(m["content"] for m in messages if m["role"] == "user")
        assert "plane_source" in user_content
        assert "x_resolution" in user_content

    def test_litellm_failure_raises_runtime_error(self):
        from vtk_validate.dsl.translator import translate_to_dsl

        idx = make_mock_index({})
        mock_litellm = MagicMock()
        mock_litellm.completion.side_effect = Exception("network error")

        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            with pytest.raises(RuntimeError, match="DSL translation failed"):
                translate_to_dsl("make a sphere", idx)
