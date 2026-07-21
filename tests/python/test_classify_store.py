"""T008 — pytest para classify_models.py: load_global_store, save_global_store, validar_sin_claves_prohibidas."""

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


# ---------------------------------------------------------------- load_global_store


def test_load_global_store_ruta_no_existe(tmp_path):
    """load_global_store sobre ruta no existe: estado 'ausente', data con version 1."""
    target = tmp_path / "nonexistent.json"

    result = classify_models.load_global_store(str(target))

    assert result["estado"] == "ausente"
    assert result["data"] == {"version": 1}


def test_load_global_store_json_valido_version_1(tmp_path):
    """load_global_store sobre JSON válido con version 1: estado 'valido', data igual al archivo."""
    target = tmp_path / "valid.json"
    original_data = {"version": 1, "planes": {"claude": {}}, "otros": "datos"}
    target.write_text(json.dumps(original_data), encoding="utf-8")

    result = classify_models.load_global_store(str(target))

    assert result["estado"] == "valido"
    assert result["data"] == original_data


def test_load_global_store_json_invalido_no_modifica_archivo(tmp_path):
    """load_global_store sobre JSON inválido: estado 'corrupto', archivo original no se modifica."""
    target = tmp_path / "corrupted.json"
    original_content = "{ invalid json }"
    target.write_text(original_content, encoding="utf-8")

    result = classify_models.load_global_store(str(target))

    assert result["estado"] == "corrupto"
    assert result["data"] == {"version": 1}
    # Verifica que el archivo no se modificó
    reread_content = target.read_text(encoding="utf-8")
    assert reread_content == original_content


def test_load_global_store_version_desconocida_preserva_planes_mapeos(tmp_path):
    """load_global_store sobre version 99 con planes/mapeos: preserva esos dos campos, descarta otros."""
    target = tmp_path / "unknown_version.json"
    original_data = {
        "version": 99,
        "planes": {"claude": {"nivel": 3}},
        "mapeos": {"gpt-4": "claude-opus"},
        "otro_campo_viejo": "sera_descartado",
        "estado_antiguo": "irrelevante"
    }
    target.write_text(json.dumps(original_data), encoding="utf-8")

    result = classify_models.load_global_store(str(target))

    assert result["estado"] == "version-desconocida"
    assert result["data"]["version"] == 1
    assert result["data"]["planes"] == {"claude": {"nivel": 3}}
    assert result["data"]["mapeos"] == {"gpt-4": "claude-opus"}
    assert "otro_campo_viejo" not in result["data"]
    assert "estado_antiguo" not in result["data"]


# ---------------------------------------------------------------- validar_sin_claves_prohibidas


def test_validar_sin_claves_prohibidas_dict_limpio(tmp_path):
    """validar_sin_claves_prohibidas sobre dict limpio: devuelve lista vacía."""
    clean_data = {
        "planes": {"claude": {"nivel": 3}},
        "mapeos": {"gpt-4": "claude-opus"},
        "otros": {"subnivel": "ok"}
    }

    result = classify_models.validar_sin_claves_prohibidas(clean_data)

    assert result == []


def test_validar_sin_claves_prohibidas_clave_anidada(tmp_path):
    """validar_sin_claves_prohibidas con clave prohibida anidada: detecta ruta anidada."""
    dirty_data = {
        "planes": {
            "claude": {
                "cuota": "5000"  # 'cuota' es prohibida, anidada bajo planes.claude
            }
        }
    }

    result = classify_models.validar_sin_claves_prohibidas(dirty_data)

    assert len(result) > 0, "Debería detectar al menos una clave prohibida"
    # Verifica que la lista contiene la palabra "cuota" (no es necesario verificar el formato exacto de la ruta)
    assert any("cuota" in item for item in result), "Debería detectar la clave 'cuota' en la ruta anidada"


# ---------------------------------------------------------------- save_global_store


def test_save_global_store_con_clave_prohibida_no_crea_archivo_y_lanza_excepcion(tmp_path):
    """save_global_store con clave prohibida: no crea archivo, lanza excepción."""
    target = tmp_path / "should_not_exist.json"
    dirty_data = {
        "planes": {"claude": {}},
        "token": "secret123"  # 'token' es prohibida
    }

    with pytest.raises(ValueError):
        classify_models.save_global_store(str(target), dirty_data)

    # Verifica que el archivo no fue creado
    assert not target.exists(), "El archivo no debería haber sido creado"


def test_save_global_store_dict_limpio_crea_archivo_y_relectura_da_lo_mismo(tmp_path):
    """save_global_store con dict limpio: crea archivo, relectura con json.load da el mismo contenido."""
    target = tmp_path / "clean_store.json"
    clean_data = {
        "version": 1,
        "planes": {"claude": {"nivel": 3}},
        "mapeos": {"gpt-4": "claude-opus"}
    }

    classify_models.save_global_store(str(target), clean_data)

    # Verifica que el archivo fue creado
    assert target.exists(), "El archivo debería haber sido creado"

    # Relectura y verificación de contenido
    reread = json.loads(target.read_text(encoding="utf-8"))
    assert reread == clean_data
