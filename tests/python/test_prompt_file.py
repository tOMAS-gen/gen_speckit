"""TDD contract tests for the --prompt-file flag in invoke_secondary.py.

These tests express the contract defined in
specs/008-multi-model-phase-dispatch/contracts/prompt-file.md. The flag is not
implemented yet, so every test is expected to fail naturally when imported or
run against the current script.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / ".specify" / "scripts" / "python" / "invoke_secondary.py"
SPEC = importlib.util.spec_from_file_location("invoke_secondary_under_test", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
invoke_secondary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(invoke_secondary)


@pytest.fixture
def models_path(tmp_path):
    """Minimal inventory with a fake CLI headless template."""
    path = tmp_path / "models.json"
    path.write_text(
        json.dumps(
            {
                "clis": {
                    "fakecli": {
                        "headless": 'fakecli run --prompt "{prompt}"',
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def _run_main(argv):
    """Thin wrapper around the script's main entry point."""
    return invoke_secondary.main(argv)


def _fake_run_process_success(*args, **kwargs):
    """Stub that simulates a successful CLI run."""
    return {"exitCode": 0, "timedOut": False}


class TestPromptFileValidation:
    """Error paths for --prompt-file."""

    def test_both_prompt_and_prompt_file_exits_with_code_2(
        self, tmp_path, models_path
    ):
        prompt_file = tmp_path / "prompt.md"
        prompt_file.write_text("contenido", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            _run_main(
                [
                    "--cli",
                    "fakecli",
                    "--prompt",
                    "inline prompt",
                    "--prompt-file",
                    str(prompt_file),
                    "--models-path",
                    str(models_path),
                    "--log-dir",
                    str(tmp_path / "logs"),
                ]
            )

        assert exc_info.value.code == 2

    def test_missing_prompt_file_exits_with_code_2(self, tmp_path, models_path):
        with pytest.raises(SystemExit) as exc_info:
            _run_main(
                [
                    "--cli",
                    "fakecli",
                    "--prompt-file",
                    str(tmp_path / "no_existe.md"),
                    "--models-path",
                    str(models_path),
                    "--log-dir",
                    str(tmp_path / "logs"),
                ]
            )

        assert exc_info.value.code == 2

    def test_empty_prompt_file_exits_with_code_2(self, tmp_path, models_path):
        prompt_file = tmp_path / "empty.md"
        prompt_file.write_text("", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            _run_main(
                [
                    "--cli",
                    "fakecli",
                    "--prompt-file",
                    str(prompt_file),
                    "--models-path",
                    str(models_path),
                    "--log-dir",
                    str(tmp_path / "logs"),
                ]
            )

        assert exc_info.value.code == 2

    def test_prompt_file_outside_repo_exits_with_code_2(
        self, tmp_path, models_path
    ):
        # tmp_path lives outside the repository, so the file is outside the repo
        # when the script is told to work inside REPO_ROOT.
        prompt_file = tmp_path / "outside.md"
        prompt_file.write_text("contenido", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            _run_main(
                [
                    "--cli",
                    "fakecli",
                    "--prompt-file",
                    str(prompt_file),
                    "--models-path",
                    str(models_path),
                    "--log-dir",
                    str(tmp_path / "logs"),
                    "--working-directory",
                    str(REPO_ROOT),
                ]
            )

        assert exc_info.value.code == 2


class TestPromptFileSuccess:
    """Happy path for --prompt-file."""

    def test_valid_prompt_file_uses_short_pointer_command(
        self, tmp_path, models_path, monkeypatch, capsys
    ):
        working_directory = tmp_path
        prompt_file = working_directory / "plan.prompt.md"
        long_content = "INSTRUCCIONES LARGAS\n" * 500
        prompt_file.write_text(long_content, encoding="utf-8")

        monkeypatch.setattr(
            invoke_secondary._platform, "run_process", _fake_run_process_success
        )

        exit_code = _run_main(
            [
                "--cli",
                "fakecli",
                "--prompt-file",
                str(prompt_file),
                "--models-path",
                str(models_path),
                "--log-dir",
                str(tmp_path / "logs"),
                "--working-directory",
                str(working_directory),
            ]
        )

        captured = capsys.readouterr()
        assert exit_code == 0
        result = json.loads(captured.out)

        assert result["promptFile"] == "plan.prompt.md"

        command = result["comando"]
        assert len(command) < 500
        assert "plan.prompt.md" in command
        assert "INSTRUCCIONES LARGAS" not in command


class TestPromptBackwardCompatibility:
    """Existing --prompt behaviour must remain unchanged."""

    def test_prompt_inline_sets_prompt_file_null(
        self, tmp_path, models_path, monkeypatch, capsys
    ):
        monkeypatch.setattr(
            invoke_secondary._platform, "run_process", _fake_run_process_success
        )

        exit_code = _run_main(
            [
                "--cli",
                "fakecli",
                "--prompt",
                "hacer tarea",
                "--models-path",
                str(models_path),
                "--log-dir",
                str(tmp_path / "logs"),
            ]
        )

        captured = capsys.readouterr()
        assert exit_code == 0
        result = json.loads(captured.out)

        assert result["promptFile"] is None
        assert result["comando"] == 'fakecli run --prompt "hacer tarea"'

    def test_prompt_inline_preserves_whitespace_and_quote_escaping(
        self, tmp_path, models_path, monkeypatch, capsys
    ):
        monkeypatch.setattr(
            invoke_secondary._platform, "run_process", _fake_run_process_success
        )

        exit_code = _run_main(
            [
                "--cli",
                "fakecli",
                "--prompt",
                '  primera linea\n segunda   "citada"  ',
                "--models-path",
                str(models_path),
                "--log-dir",
                str(tmp_path / "logs"),
            ]
        )

        captured = capsys.readouterr()
        assert exit_code == 0
        result = json.loads(captured.out)

        assert result["promptFile"] is None
        assert result["comando"] == (
            'fakecli run --prompt "primera linea segunda \\"citada\\""'
        )
