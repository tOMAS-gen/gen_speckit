"""T004 — pytest para platform_helper.py: user_config_dir() y write_json_atomic()."""

import importlib.util
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".specify" / "scripts" / "python" / "platform_helper.py"


def _load():
    spec = importlib.util.spec_from_file_location("platform_helper", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


platform_helper = _load()


# ---------------------------------------------------------------- user_config_dir()

def test_user_config_dir_respeta_env_override(monkeypatch):
    """GEN_SPECKIT_GLOBAL_DIR, si está definida y no vacía, es el directorio."""
    override = "/custom/path/gen-speckit"
    monkeypatch.setenv("GEN_SPECKIT_GLOBAL_DIR", override)

    result = platform_helper.user_config_dir()
    assert result == Path(override)


def test_user_config_dir_sin_override_contiene_gen_speckit(monkeypatch):
    """Sin GEN_SPECKIT_GLOBAL_DIR, el directorio contiene 'gen-speckit' al final."""
    monkeypatch.delenv("GEN_SPECKIT_GLOBAL_DIR", raising=False)

    result = platform_helper.user_config_dir()
    # En Windows: C:\Users\...\AppData\Roaming\gen-speckit
    # En macOS: /Users/.../Library/Application Support/gen-speckit
    # En Linux: /home/.../.config/gen-speckit
    # En todos los casos, el último componente debe ser "gen-speckit"
    assert result.name == "gen-speckit"


# ---------------------------------------------------------------- write_json_atomic()

def test_write_json_atomic_escribe_json_correcto(tmp_path):
    """write_json_atomic() escribe un JSON legible, que relectura con json.load da lo original."""
    target = tmp_path / "data.json"
    data = {"key": "value", "number": 42, "nested": {"inner": True}}

    platform_helper.write_json_atomic(str(target), data)

    reread = json.loads(target.read_text(encoding="utf-8"))
    assert reread == data


def test_write_json_atomic_atomicidad_sin_huerfanos_ni_corrupcion(tmp_path, monkeypatch):
    """Si falla durante os.replace(), el destino no se corrompe ni deja .tmp* huérfanos.

    Simulamos una excepción forzando un fallo en os.replace().
    """
    target = tmp_path / "state.json"
    original_data = {"version": 1, "status": "ok"}
    target.write_text(json.dumps(original_data), encoding="utf-8")

    new_data = {"version": 2, "status": "updating"}

    # Monkeypatch os.replace para lanzar una excepción
    original_replace = os.replace

    def mock_replace_fail(src, dst):
        raise IOError("Simulated disk failure")

    monkeypatch.setattr(os, "replace", mock_replace_fail)

    # Intenta escribir pero falla
    try:
        platform_helper.write_json_atomic(str(target), new_data)
    except IOError:
        pass  # Esperado

    # Verifica que el archivo original no se corrompió
    result = json.loads(target.read_text(encoding="utf-8"))
    assert result == original_data

    # Verifica que no quedan archivos temporales huérfanos
    tmp_files = list(tmp_path.glob("*.tmp*"))
    assert len(tmp_files) == 0, f"Archivos temporales huérfanos encontrados: {tmp_files}"


def test_write_json_atomic_utf8_sin_bom(tmp_path):
    """El archivo escrito no comienza con BOM UTF-8 (0xEF 0xBB 0xBF)."""
    target = tmp_path / "clean.json"
    data = {"text": "hello"}

    platform_helper.write_json_atomic(str(target), data)

    raw_bytes = target.read_bytes()
    bom_utf8 = b'\xef\xbb\xbf'
    assert not raw_bytes.startswith(bom_utf8), "El archivo comienza con BOM UTF-8"
