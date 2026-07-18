"""Unit tests for the Python secondary-CLI dispatcher."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / ".specify" / "scripts" / "python" / "invoke_secondary.py"
SPEC = importlib.util.spec_from_file_location("invoke_secondary_under_test", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
invoke_secondary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(invoke_secondary)


def test_get_headless_command_sanitizes_prompt_and_appends_model():
    inventory = {
        "clis": {
            "example": {
                "headless": 'example run --prompt "{prompt}"',
            }
        }
    }

    command = invoke_secondary.get_headless_command(
        inventory,
        "example",
        "gpt-5.6-terra",
        '  primera linea\n segunda   "citada"  ',
    )

    assert command == (
        'example run --prompt "primera linea segunda \\"citada\\"" '
        "--model gpt-5.6-terra"
    )


def test_get_headless_command_replaces_model_placeholder_in_template():
    inventory = {
        "clis": {
            "example": {
                "headless": 'example run --model {modelo} --prompt "{prompt}"',
            }
        }
    }

    command = invoke_secondary.get_headless_command(
        inventory, "example", "gpt-5.6-terra", "hacer tarea"
    )

    assert command == (
        'example run --model gpt-5.6-terra --prompt "hacer tarea"'
    )


@pytest.mark.parametrize("quota_text", ["HTTP 429 Too Many Requests", "Rate limit exceeded"])
def test_quota_pattern_detects_quota_errors_but_not_clean_text(quota_text):
    patterns = [r"\b429\b", "rate limit"]

    assert invoke_secondary.test_quota_pattern(patterns, quota_text)
    assert not invoke_secondary.test_quota_pattern(patterns, "Tarea completada correctamente")


def test_get_quota_patterns_uses_defaults_without_catalog():
    inventory = {"clis": {"example": {"headless": "example {prompt}"}}}

    patterns = invoke_secondary.get_quota_patterns(inventory, None, "example")

    assert patterns == invoke_secondary.DEFAULT_QUOTA_PATTERNS
    assert patterns is not invoke_secondary.DEFAULT_QUOTA_PATTERNS
