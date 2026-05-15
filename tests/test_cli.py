"""Tests for vtk_validate.cli Typer app."""

from __future__ import annotations

import re

from helpers import make_mock_index
from typer.testing import CliRunner

from vtk_validate.cli import app

runner = CliRunner()


def _strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def _write_py(tmp_path, source: str, name: str = "script.py"):
    p = tmp_path / name
    p.write_text(source)
    return p


# ---------------------------------------------------------------------------
# check command
# ---------------------------------------------------------------------------


class TestCheckCommand:
    def test_clean_file_exits_zero(self, tmp_path, monkeypatch):
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: make_mock_index({"vtkActor": "vtkRenderingCore"}))
        f = _write_py(tmp_path, "x = 1 + 1")
        result = runner.invoke(app, ["check", str(f), "-k", "fake.jsonl"])
        assert result.exit_code == 0
        assert "OK" in result.output

    def test_file_with_errors_exits_nonzero(self, tmp_path, monkeypatch):
        idx = make_mock_index({})
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        f = _write_py(tmp_path, "import os")
        result = runner.invoke(app, ["check", str(f), "-k", "fake.jsonl"])
        assert result.exit_code != 0

    def test_missing_file_exits_nonzero(self):
        result = runner.invoke(app, ["check", "nonexistent.py", "-k", "fake.jsonl"])
        assert result.exit_code != 0

    def test_diagnostic_line_number_shown(self, tmp_path, monkeypatch):
        idx = make_mock_index({})
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        f = _write_py(tmp_path, "import os")
        result = runner.invoke(app, ["check", str(f), "-k", "fake.jsonl"])
        assert ":1" in result.output

    def test_warning_only_exits_zero(self, tmp_path, monkeypatch):
        idx = make_mock_index({})
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        f = _write_py(tmp_path, "reader.GetOutput()")
        result = runner.invoke(app, ["check", str(f), "-k", "fake.jsonl"])
        assert result.exit_code == 0
        assert "warning" in result.output

    def test_help_shows_usage(self):
        result = runner.invoke(app, ["check", "--help"])
        out = _strip_ansi(result.output)
        assert result.exit_code == 0
        assert "FILE" in out


# ---------------------------------------------------------------------------
# class-info command
# ---------------------------------------------------------------------------


class TestClassInfoCommand:
    def test_known_class_exits_zero(self, monkeypatch):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        result = runner.invoke(app, ["class-info", "vtkActor", "-k", "fake.jsonl"])
        assert result.exit_code == 0

    def test_output_contains_class_name(self, monkeypatch):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        result = runner.invoke(app, ["class-info", "vtkActor", "-k", "fake.jsonl"])
        assert "vtkActor" in result.output

    def test_output_contains_module(self, monkeypatch):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        result = runner.invoke(app, ["class-info", "vtkActor", "-k", "fake.jsonl"])
        assert "vtkRenderingCore" in result.output

    def test_unknown_class_exits_nonzero(self, monkeypatch):
        idx = make_mock_index({})
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        result = runner.invoke(app, ["class-info", "vtkGhost", "-k", "fake.jsonl"])
        assert result.exit_code != 0

    def test_help_lists_argument(self):
        result = runner.invoke(app, ["class-info", "--help"])
        out = _strip_ansi(result.output)
        assert "CLASS_NAME" in out


# ---------------------------------------------------------------------------
# search command
# ---------------------------------------------------------------------------


class TestSearchCommand:
    def test_returns_results(self, monkeypatch):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        result = runner.invoke(app, ["search", "actor", "-k", "fake.jsonl"])
        assert result.exit_code == 0
        assert "vtkActor" in result.output

    def test_empty_results_message(self, monkeypatch):
        idx = make_mock_index({})
        idx.search_classes.side_effect = None
        idx.search_classes.return_value = []
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        result = runner.invoke(app, ["search", "nothing", "-k", "fake.jsonl"])
        assert result.exit_code == 0
        assert "No results" in result.output

    def test_limit_option_forwarded(self, monkeypatch):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        runner.invoke(app, ["search", "vtk", "--limit", "5", "-k", "fake.jsonl"])
        idx.search_classes.assert_called_with("vtk", limit=5)

    def test_help_shows_limit_option(self):
        result = runner.invoke(app, ["search", "--help"])
        out = _strip_ansi(result.output)
        assert "--limit" in out


# ---------------------------------------------------------------------------
# method-info command
# ---------------------------------------------------------------------------


class TestMethodInfoCommand:
    def test_known_method_exits_zero(self, monkeypatch):
        from helpers import make_mock_method

        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        idx.get_method.side_effect = None
        idx.get_method.return_value = make_mock_method("SetVisibility")
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        result = runner.invoke(app, ["method-info", "vtkActor", "SetVisibility", "-k", "fake.jsonl"])
        assert result.exit_code == 0

    def test_output_contains_method_name(self, monkeypatch):
        from helpers import make_mock_method

        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        idx.get_method.side_effect = None
        idx.get_method.return_value = make_mock_method("SetVisibility")
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        result = runner.invoke(app, ["method-info", "vtkActor", "SetVisibility", "-k", "fake.jsonl"])
        assert "SetVisibility" in result.output

    def test_unknown_method_exits_nonzero(self, monkeypatch):
        idx = make_mock_index({"vtkActor": "vtkRenderingCore"})
        idx.get_method.side_effect = None
        idx.get_method.return_value = None
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        result = runner.invoke(app, ["method-info", "vtkActor", "BadMethod", "-k", "fake.jsonl"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# module command
# ---------------------------------------------------------------------------


class TestModuleCommand:
    def test_lists_classes(self, monkeypatch):
        idx = make_mock_index({})
        idx.classes_in_module.return_value = ["vtkActor", "vtkRenderer"]
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        result = runner.invoke(app, ["module", "vtkRenderingCore", "-k", "fake.jsonl"])
        assert result.exit_code == 0
        assert "vtkActor" in result.output
        assert "vtkRenderer" in result.output

    def test_empty_module_message(self, monkeypatch):
        idx = make_mock_index({})
        idx.classes_in_module.return_value = []
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        result = runner.invoke(app, ["module", "vtkUnknown", "-k", "fake.jsonl"])
        assert result.exit_code == 0
        assert "No classes" in result.output

    def test_count_shown(self, monkeypatch):
        idx = make_mock_index({})
        idx.classes_in_module.return_value = ["vtkActor", "vtkRenderer"]
        monkeypatch.setattr("vtk_validate.cli._load_index", lambda _: idx)
        result = runner.invoke(app, ["module", "vtkRenderingCore", "-k", "fake.jsonl"])
        assert "2" in result.output


# ---------------------------------------------------------------------------
# top-level app
# ---------------------------------------------------------------------------


class TestApp:
    def test_no_args_shows_help(self):
        result = runner.invoke(app, [])
        assert result.exit_code in (0, 2)
        out = _strip_ansi(result.output)
        assert "check" in out
        assert "search" in out
