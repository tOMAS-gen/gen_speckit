"""T004 — pytest para el descubrimiento de modelos de scan_models.py (feature 006).

Ejercita las funciones nuevas: _extract_models, _plausible_model_id,
detect_models (con TOML temporal) y apply_detected_models. No ejecuta CLIs
reales ni toca .specify/models.json.
"""

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".specify" / "scripts" / "python" / "scan_models.py"


def _load():
    spec = importlib.util.spec_from_file_location("scan_models_discovery", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


scan_models = _load()


# ---------------------------------------------------------------- _extract_models

def test_extract_models_dict_estilo_toml():
    data = {
        "models": {
            "prov/model-a1": {"support_efforts": ["low", "high"]},
            "prov/model-b2": {},
        }
    }
    found = scan_models._extract_models(data)
    assert set(found.keys()) == {"model-a1", "model-b2"}
    assert found["model-a1"]["esfuerzos"] == ["low", "high"]
    assert found["model-b2"] == {}


# ---------------------------------------------------------- _plausible_model_id

def test_plausible_model_id_acepta_ids_reales():
    for mid in ("k3", "gpt-5.6-sol", "claude-opus-4-8"):
        assert scan_models._plausible_model_id(mid), mid


def test_plausible_model_id_rechaza_campos_de_config():
    for campo in ("lastusedat", "usagecount", "trust_level"):
        assert not scan_models._plausible_model_id(campo), campo


# ---------------------------------------------------------------- detect_models

def _catalog_con_hints(path):
    os_fam = scan_models._platform.os_family()
    return {"clis": {"testcli": {"config_hints": {os_fam: [str(path)]}}}}


def test_detect_models_extrae_de_toml_temporal(tmp_path):
    toml = tmp_path / "config.toml"
    toml.write_text(
        '[models]\n'
        '[models."prov/model-a1"]\n'
        'support_efforts = ["low", "high"]\n'
        '[models."prov/model-b2"]\n',
        encoding="utf-8",
    )
    detected = scan_models.detect_models("testcli", None, _catalog_con_hints(toml))
    assert set(detected.keys()) == {"model-a1", "model-b2"}
    assert detected["model-a1"]["esfuerzos"] == ["low", "high"]


def test_detect_models_ruta_inexistente_devuelve_vacio(tmp_path):
    missing = tmp_path / "no-existe.toml"
    detected = scan_models.detect_models("testcli", None, _catalog_con_hints(missing))
    assert detected == {}


def test_detect_models_toml_corrupto_devuelve_vacio(tmp_path):
    bad = tmp_path / "roto.toml"
    bad.write_text("esto no = [es toml valido", encoding="utf-8")
    detected = scan_models.detect_models("testcli", None, _catalog_con_hints(bad))
    assert detected == {}


# -------------------------------------------------------- apply_detected_models

def test_apply_detected_models_origenes_y_agregados():
    modelos = [
        {"id": "model-a1", "capacidad": 8, "costo": 3},
        {"id": "semilla-sin-evidencia", "capacidad": 4, "costo": 1},
    ]
    detected = {"model-a1": {}, "nuevo-detectado": {}}
    result = scan_models.apply_detected_models(modelos, detected)
    by_id = {m["id"]: m for m in result}

    assert by_id["model-a1"]["origen"] == "detectado-local"
    # Semilla sin evidencia: se conserva con origen semilla (no se borra).
    assert by_id["semilla-sin-evidencia"]["origen"] == "semilla"
    # Detectado sin semilla: se agrega con capacidad/costo medios.
    assert by_id["nuevo-detectado"]["origen"] == "detectado-local"
    assert by_id["nuevo-detectado"]["capacidad"] == 5
    assert by_id["nuevo-detectado"]["costo"] == 2


def test_apply_detected_models_sin_duplicados_por_substring():
    modelos = [
        {"id": "kimi-for-coding", "capacidad": 8, "costo": 2},
        {"id": "kimi-for-coding-highspeed", "capacidad": 8, "costo": 2},
    ]
    detected = {"kimi-for-coding": {}, "kimi-for-coding-highspeed": {}}
    result = scan_models.apply_detected_models(modelos, detected)

    assert len(result) == 2
    ids = [m["id"] for m in result]
    assert ids == ["kimi-for-coding", "kimi-for-coding-highspeed"]
    assert all(m["origen"] == "detectado-local" for m in result)
