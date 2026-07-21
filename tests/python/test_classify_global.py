"""T025 — pytest para classify_models.py: flujo completo del almacen de la maquina."""

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".specify" / "scripts" / "python" / "classify_models.py"


def _load():
    spec = importlib.util.spec_from_file_location("classify_models", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


classify_models = _load()


def _parse_stdout(capsys):
    captured = capsys.readouterr()
    return json.loads(captured.out)


def test_main_primera_corrida_sin_almacen_pregunta_global(tmp_path, monkeypatch, capsys):
    """Sin almacen previo, main(["--json"]) indica que hay que preguntar al usuario."""
    monkeypatch.setenv("GEN_SPECKIT_GLOBAL_DIR", str(tmp_path))

    code = classify_models.main(["--json"])

    assert code == 0
    summary = _parse_stdout(capsys)
    assert summary["preguntar_global"] is True


def test_main_global_si_guarda_decision_y_no_repregunta(tmp_path, monkeypatch, capsys):
    """--global si persiste la decision; una segunda corrida sin flag no repregunta."""
    monkeypatch.setenv("GEN_SPECKIT_GLOBAL_DIR", str(tmp_path))

    code1 = classify_models.main(["--global", "si", "--json"])
    assert code1 == 0
    summary1 = _parse_stdout(capsys)
    assert summary1["preguntar_global"] is False

    capsys.readouterr()  # descartar buffers para la segunda corrida
    code2 = classify_models.main(["--json"])
    assert code2 == 0
    summary2 = _parse_stdout(capsys)
    assert summary2["preguntar_global"] is False


def test_main_global_no_persiste_decision_aunque_no_comparta(tmp_path, monkeypatch, capsys):
    """--global no guarda la decision de no compartir, pero no almacena clasificacion."""
    monkeypatch.setenv("GEN_SPECKIT_GLOBAL_DIR", str(tmp_path))

    code = classify_models.main(["--global", "no", "--json"])
    assert code == 0

    # La salida indica que ya no hay que preguntar (la decision quedo guardada).
    summary = _parse_stdout(capsys)
    assert summary["preguntar_global"] is False

    # El archivo global existe y contiene compartir="no".
    store = classify_models.load_global_store(classify_models._global_path())
    assert store["estado"] == "valido"
    assert store["data"]["compartir"] == "no"


def test_resolver_fuente_clasificacion_usa_global_cuando_no_hay_red(tmp_path, monkeypatch):
    """Segundo proyecto: sin red, reutiliza el snapshot global guardado."""
    monkeypatch.setenv("GEN_SPECKIT_GLOBAL_DIR", str(tmp_path))

    entradas = [
        {
            "model_name": "claude-opus-4",
            "organization": "Anthropic",
            "rating": 9.5,
            "rank_dataset": 1,
            "vote_count": 1000,
            "leaderboard_publish_date": "2026-07-20",
            "categorias": {},
        }
    ]
    data = {
        "version": 1,
        "compartir": "si",
        "clasificacion": {"entradas": entradas},
    }
    path = classify_models._global_path()
    classify_models.save_global_store(path, data)

    store = classify_models.load_global_store(path)
    result = classify_models.resolver_fuente_clasificacion(store["data"], None)

    assert result["fuente_ganadora"] == "global"
    assert result["entradas"] == entradas


@pytest.mark.parametrize(
    "plan_local,planes_global,expected_fuente,expected_plan",
    [
        ("Max 5x", {"claude": {"plan": "Pro"}}, "local", "Max 5x"),
        ("desconocido", {"claude": {"plan": "Pro"}}, "global", "Pro"),
        (None, {}, "ninguna", "desconocido"),
    ],
)
def test_resolver_fuente_plan_precedencia(plan_local, planes_global, expected_fuente, expected_plan):
    """resolver_fuente_plan respeta la precedencia: local > global > ninguna."""
    global_data = {"version": 1, "planes": planes_global}
    result = classify_models.resolver_fuente_plan(global_data, "claude", plan_local)

    assert result["fuente_ganadora"] == expected_fuente
    assert result["plan"] == expected_plan


def test_save_global_store_degrade_graceful_si_directorio_no_escribible(
    tmp_path, monkeypatch, capsys
):
    """Si _platform.write_json_atomic falla por permisos, save_global_store no lanza y avisa."""
    original_write = classify_models._platform.write_json_atomic

    def _raise_permission_error(*args, **kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(classify_models._platform, "write_json_atomic", _raise_permission_error)

    target = tmp_path / "global.json"
    clean_data = {"version": 1, "compartir": "si"}

    result = classify_models.save_global_store(str(target), clean_data)

    assert result is None
    captured = capsys.readouterr()
    assert "no se pudo" in captured.err.lower() or "aviso" in captured.err.lower()

    # Restaurar no es estrictamente necesario porque monkeypatch revierte al terminar,
    # pero lo dejamos explicito por claridad.
    monkeypatch.setattr(classify_models._platform, "write_json_atomic", original_write)
