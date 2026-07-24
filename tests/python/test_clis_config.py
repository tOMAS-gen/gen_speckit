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


# Tests TDD para acciones modelo-* y preferido-* (feature 008)


def _snapshot_inventory(models_path):
    return json.loads(models_path.read_text(encoding="utf-8"))


def _write_inventory(models_path, data):
    models_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_deshabilitar_modelo_marca_modelo_como_deshabilitado(inventory_path):
    result = clis_config.deshabilitar_modelo(inventory_path, "registered-cli", "base")

    assert result["ok"] is True
    assert result["cambios"] == "modelo deshabilitado"
    modelo = _read_inventory(inventory_path)["clis"]["registered-cli"]["modelos"][0]
    assert modelo.get("deshabilitado") is True


def test_deshabilitar_modelo_falla_si_cli_no_existe_sin_escribir(inventory_path):
    original = _snapshot_inventory(inventory_path)
    with pytest.raises(ValueError, match="no existe en el inventario"):
        clis_config.deshabilitar_modelo(inventory_path, "missing-cli", "base")

    assert _read_inventory(inventory_path) == original


def test_deshabilitar_modelo_falla_si_modelo_no_existe_sin_escribir(inventory_path):
    original = _snapshot_inventory(inventory_path)
    with pytest.raises(ValueError, match="modelo.*no existe"):
        clis_config.deshabilitar_modelo(inventory_path, "registered-cli", "missing-model")

    assert _read_inventory(inventory_path) == original


def test_deshabilitar_modelo_advierte_tareas_pendientes_del_cli_modelo(inventory_path, tmp_path):
    specs_dir = tmp_path / "specs" / "feature-008"
    specs_dir.mkdir(parents=True)
    (specs_dir / "tasks.md").write_text(
        "- [ ] Tarea pendiente [M:registered-cli/base]\n", encoding="utf-8"
    )

    result = clis_config.deshabilitar_modelo(inventory_path, "registered-cli", "base")

    assert result["ok"] is True
    assert any("registered-cli/base" in str(w) for w in result["advertencias"])


def test_habilitar_modelo_quita_deshabilitado(inventory_path):
    data = _snapshot_inventory(inventory_path)
    data["clis"]["registered-cli"]["modelos"][0]["deshabilitado"] = True
    _write_inventory(inventory_path, data)

    result = clis_config.habilitar_modelo(inventory_path, "registered-cli", "base")

    assert result["ok"] is True
    assert result["cambios"] == "modelo habilitado"
    modelo = _read_inventory(inventory_path)["clis"]["registered-cli"]["modelos"][0]
    assert modelo.get("deshabilitado") is not True


def test_habilitar_modelo_falla_si_cli_no_existe_sin_escribir(inventory_path):
    original = _snapshot_inventory(inventory_path)
    with pytest.raises(ValueError, match="no existe en el inventario"):
        clis_config.habilitar_modelo(inventory_path, "missing-cli", "base")

    assert _read_inventory(inventory_path) == original


def test_habilitar_modelo_falla_si_modelo_no_existe_sin_escribir(inventory_path):
    original = _snapshot_inventory(inventory_path)
    with pytest.raises(ValueError, match="modelo.*no existe"):
        clis_config.habilitar_modelo(inventory_path, "registered-cli", "missing-model")

    assert _read_inventory(inventory_path) == original


def test_fijar_preferido_escribe_campo_preferido(inventory_path):
    result = clis_config.fijar_preferido(inventory_path, "registered-cli")

    assert result["ok"] is True
    assert result["cambios"] == "preferido fijado"
    assert _read_inventory(inventory_path)["preferido"] == "registered-cli"


def test_fijar_preferido_falla_si_cli_no_existe_sin_escribir(inventory_path):
    original = _snapshot_inventory(inventory_path)
    with pytest.raises(ValueError, match="no existe en el inventario"):
        clis_config.fijar_preferido(inventory_path, "missing-cli")

    assert _read_inventory(inventory_path) == original


def test_fijar_preferido_advierte_si_cli_esta_deshabilitado(inventory_path):
    data = _snapshot_inventory(inventory_path)
    data["clis"]["registered-cli"]["deshabilitado"] = True
    _write_inventory(inventory_path, data)

    result = clis_config.fijar_preferido(inventory_path, "registered-cli")

    assert result["ok"] is True
    assert result["cambios"] == "preferido fijado"
    assert _read_inventory(inventory_path)["preferido"] == "registered-cli"
    assert any("deshabilitado" in str(w).lower() for w in result["advertencias"])


def test_fijar_preferido_advierte_si_no_hay_modelos_habilitados(inventory_path):
    data = _snapshot_inventory(inventory_path)
    data["clis"]["registered-cli"]["modelos"][0]["deshabilitado"] = True
    _write_inventory(inventory_path, data)

    result = clis_config.fijar_preferido(inventory_path, "registered-cli")

    assert result["ok"] is True
    assert result["cambios"] == "preferido fijado"
    assert _read_inventory(inventory_path)["preferido"] == "registered-cli"
    assert any("habilitados" in str(w).lower() for w in result["advertencias"])


def test_quitar_preferido_elimina_campo_preferido(inventory_path):
    data = _snapshot_inventory(inventory_path)
    data["preferido"] = "registered-cli"
    _write_inventory(inventory_path, data)

    result = clis_config.quitar_preferido(inventory_path)

    assert result["ok"] is True
    assert result["cambios"] == "preferido quitado"
    assert "preferido" not in _read_inventory(inventory_path)


def test_quitar_preferido_es_noop_si_no_hay_preferido(inventory_path):
    result = clis_config.quitar_preferido(inventory_path)

    assert result["ok"] is True
    assert "preferido" not in _read_inventory(inventory_path)
