"""Pruebas unitarias para la administracion de CLIs sin invocar CLIs reales."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / ".specify" / "scripts" / "python" / "clis_config.py"
SPEC = importlib.util.spec_from_file_location("clis_config_under_test", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
clis_config = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(clis_config)


def _modelo(model_id="base", capacidad=5):
    return {"id": model_id, "capacidad": capacidad, "costo": 1}


@pytest.fixture
def inventory_path(tmp_path):
    specify_dir = tmp_path / ".specify"
    specify_dir.mkdir()
    models_path = specify_dir / "models.json"
    models_path.write_text(
        json.dumps(
            {
                "clis": {
                    "registered-cli": {
                        "instalado": False,
                        "autenticado": False,
                        "version": "desconocido",
                        "headless": "registered-cli run {prompt}",
                        "plan": "desconocido",
                        "cuota": "desconocido",
                        "origen": "registrado",
                        "modelos": [_modelo()],
                    }
                },
                "asignacion": {"alta": [], "media": [], "baja": []},
            }
        ),
        encoding="utf-8",
    )
    (specify_dir / "clis-catalog.json").write_text(
        json.dumps({"version": 1, "clis": {"catalog-cli": {}}}), encoding="utf-8"
    )
    return models_path


def _read_inventory(models_path):
    return json.loads(models_path.read_text(encoding="utf-8"))


def test_get_cli_validation_problems_detects_v1_v3_and_v5():
    problems = clis_config.get_cli_validation_problems(
        "not_kebab",
        "example run",
        [_modelo(capacidad=11)],
        [],
        {},
    )

    assert any(problem.startswith("V1:") for problem in problems)
    assert any(problem.startswith("V3:") for problem in problems)
    assert any(problem.startswith("V5:") and "capacidad" in problem for problem in problems)


def test_add_cli_definition_adds_valid_cli_to_inventory(inventory_path):
    result = clis_config.add_cli_definition(
        inventory_path,
        "pytest-added-cli",
        "pytest-added-cli run {prompt}",
        [_modelo("added")],
    )

    entry = _read_inventory(inventory_path)["clis"]["pytest-added-cli"]
    assert result["operacion"] == "agregar"
    assert entry["headless"] == "pytest-added-cli run {prompt}"
    assert entry["modelos"] == [_modelo("added")]


def test_edit_cli_definition_modifies_headless(inventory_path):
    result = clis_config.edit_cli_definition(
        inventory_path, "registered-cli", headless="registered-cli exec {prompt}"
    )

    assert result == {"operacion": "editar", "cli": "registered-cli"}
    assert _read_inventory(inventory_path)["clis"]["registered-cli"]["headless"] == (
        "registered-cli exec {prompt}"
    )


def test_remove_cli_definition_requires_confirmation_and_removes_non_catalog_cli(inventory_path):
    with pytest.raises(ValueError, match="confirmacion explicita"):
        clis_config.remove_cli_definition(inventory_path, "registered-cli")

    result = clis_config.remove_cli_definition(
        inventory_path, "registered-cli", confirmado=True
    )

    assert result["cambio"] == "eliminado"
    assert "registered-cli" not in _read_inventory(inventory_path)["clis"]
