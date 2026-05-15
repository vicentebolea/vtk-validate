"""Tests for vtk_validate.tools — the 18 high-level tool functions."""

from __future__ import annotations

from helpers import make_mock_index, make_mock_method

import vtk_validate.tools as T


class TestVtkGetClassInfo:
    def test_known_class_returns_dict(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        result = T.vtk_get_class_info("vtkActor", idx)
        assert isinstance(result, dict)
        assert "error" not in result

    def test_unknown_class_returns_error(self):
        idx = make_mock_index({})
        result = T.vtk_get_class_info("vtkGhost", idx)
        assert "error" in result

    def test_error_message_includes_class_name(self):
        idx = make_mock_index({})
        result = T.vtk_get_class_info("vtkGhost", idx)
        assert "vtkGhost" in result["error"]


class TestVtkSearchClasses:
    def test_returns_list(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        result = T.vtk_search_classes("actor", idx)
        assert isinstance(result, list)

    def test_result_items_have_expected_keys(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        result = T.vtk_search_classes("actor", idx, limit=1)
        assert len(result) >= 1
        assert "class_name" in result[0]
        assert "module_name" in result[0]
        assert "synopsis" in result[0]

    def test_limit_forwarded(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore", "vtkRenderer": "vtkRenderingCore"})
        T.vtk_search_classes("vtk", idx, limit=5)
        idx.search_classes.assert_called_with("vtk", limit=5)


class TestVtkGetMethodInfo:
    def test_known_method_returns_dict(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        method = make_mock_method("SetVisibility")
        idx.get_method.side_effect = None
        idx.get_method.return_value = method
        result = T.vtk_get_method_info("vtkActor", "SetVisibility", idx)
        assert isinstance(result, dict)
        assert "error" not in result

    def test_unknown_method_returns_error(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        idx.get_method.return_value = None
        result = T.vtk_get_method_info("vtkActor", "BadMethod", idx)
        assert "error" in result

    def test_error_includes_method_name(self):
        idx = make_mock_index({})
        idx.get_method.return_value = None
        result = T.vtk_get_method_info("vtkActor", "BadMethod", idx)
        assert "BadMethod" in result["error"]


class TestVtkGetClassRole:
    def test_returns_string(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        result = T.vtk_get_class_role("vtkActor", idx)
        assert isinstance(result, str)

    def test_none_becomes_unknown(self):
        idx = make_mock_index({})
        idx.get_class_role.return_value = None
        result = T.vtk_get_class_role("vtkActor", idx)
        assert result == "unknown"


class TestVtkGetClassDataTypes:
    def test_input_datatype_returns_string(self):
        idx = make_mock_index({})
        result = T.vtk_get_class_input_datatype("vtkActor", idx)
        assert isinstance(result, str)

    def test_output_datatype_returns_string(self):
        idx = make_mock_index({})
        result = T.vtk_get_class_output_datatype("vtkActor", idx)
        assert isinstance(result, str)

    def test_input_none_becomes_empty_string(self):
        idx = make_mock_index({})
        idx.get_class_input_datatype.return_value = None
        result = T.vtk_get_class_input_datatype("vtkActor", idx)
        assert result == ""


class TestVtkIsAClass:
    def test_known_class_true(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        assert T.vtk_is_a_class("vtkActor", idx) is True

    def test_unknown_class_false(self):
        idx = make_mock_index({})
        assert T.vtk_is_a_class("vtkGhost", idx) is False


class TestVtkGetClassModule:
    def test_returns_string(self):
        idx = make_mock_index({})
        result = T.vtk_get_class_module("vtkActor", idx)
        assert isinstance(result, str)

    def test_none_becomes_empty_string(self):
        idx = make_mock_index({})
        idx.get_class_module.return_value = None
        result = T.vtk_get_class_module("vtkActor", idx)
        assert result == ""


class TestVtkGetClassMethods:
    def test_returns_list(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        result = T.vtk_get_class_methods("vtkActor", idx)
        assert isinstance(result, list)


class TestVtkGetModuleClasses:
    def test_returns_list(self):
        idx = make_mock_index({})
        result = T.vtk_get_module_classes("vtkRenderingCore", idx)
        assert isinstance(result, list)


class TestVtkGetMethodDoc:
    def test_returns_string(self):
        idx = make_mock_index({})
        result = T.vtk_get_method_doc("vtkActor", "GetOutput", idx)
        assert isinstance(result, str)

    def test_none_becomes_empty_string(self):
        idx = make_mock_index({})
        idx.get_method_doc.return_value = None
        result = T.vtk_get_method_doc("vtkActor", "GetOutput", idx)
        assert result == ""


class TestVtkGetMethodSignature:
    def test_returns_string(self):
        idx = make_mock_index({})
        result = T.vtk_get_method_signature("vtkActor", "GetOutput", idx)
        assert isinstance(result, str)

    def test_none_becomes_empty_string(self):
        idx = make_mock_index({})
        idx.get_method_signature.return_value = None
        result = T.vtk_get_method_signature("vtkActor", "GetOutput", idx)
        assert result == ""


class TestVtkGetClassSynopsis:
    def test_returns_string(self):
        idx = make_mock_index({})
        result = T.vtk_get_class_synopsis("vtkActor", idx)
        assert isinstance(result, str)

    def test_none_becomes_empty_string(self):
        idx = make_mock_index({})
        idx.get_class_synopsis.return_value = None
        result = T.vtk_get_class_synopsis("vtkActor", idx)
        assert result == ""


class TestVtkGetClassActionPhrase:
    def test_returns_string(self):
        idx = make_mock_index({})
        result = T.vtk_get_class_action_phrase("vtkActor", idx)
        assert isinstance(result, str)

    def test_none_becomes_empty_string(self):
        idx = make_mock_index({})
        idx.get_class_action_phrase.return_value = None
        result = T.vtk_get_class_action_phrase("vtkActor", idx)
        assert result == ""


class TestVtkGetClassVisibility:
    def test_returns_float(self):
        idx = make_mock_index({})
        result = T.vtk_get_class_visibility("vtkActor", idx)
        assert result == 0.9

    def test_none_returned_when_not_available(self):
        idx = make_mock_index({})
        idx.get_class_visibility.return_value = None
        result = T.vtk_get_class_visibility("vtkActor", idx)
        assert result is None


class TestVtkValidateImport:
    def test_valid_import_returns_valid_true(self):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        result = T.vtk_validate_import("from vtkRenderingCore import vtkActor", idx)
        assert result["valid"] is True

    def test_forbidden_import_returns_valid_false(self):
        idx = make_mock_index({})
        result = T.vtk_validate_import("import os", idx)
        assert result["valid"] is False

    def test_result_has_diagnostics_key(self):
        idx = make_mock_index({})
        result = T.vtk_validate_import("import os", idx)
        assert "diagnostics" in result
        assert isinstance(result["diagnostics"], list)
