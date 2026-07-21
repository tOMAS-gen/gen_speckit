"""T035 — pytest para classify_models.py: degradacion controlada sin red real."""

import importlib.util
import json
import socket
from datetime import datetime, timezone
from pathlib import Path

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


def _assert_global_json_valido(tmp_path):
    global_json = tmp_path / "global.json"
    if global_json.exists():
        json.load(global_json.open(encoding="utf-8"))


class _FakeResponse:
    def __init__(self, body, status=200):
        self._body = body
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _snapshot_global():
    return {
        "version": 1,
        "clasificacion": {
            "entradas": [{"model_name": "x", "rating": 1500}],
            "obtenido": datetime.now(timezone.utc).isoformat(),
            "publicado": "2026-07-01",
            "escala": {"piso": 950, "paso": 56},
        },
    }


# --------------------------------------------------------------------------- 1


def test_main_timeout_simulado_degrada_a_omitida_fuente_invalida(
    tmp_path, monkeypatch, capsys
):
    """Timeout de urlopen en almacen vacio: omitida/fuente-invalida, sin abortar."""
    monkeypatch.setenv("GEN_SPECKIT_GLOBAL_DIR", str(tmp_path))

    def fake_urlopen(url, timeout=None):
        raise socket.timeout("timeout simulado")

    monkeypatch.setattr(classify_models.urllib.request, "urlopen", fake_urlopen)

    code = classify_models.main(["--refrescar", "--json"])

    assert code == 0
    summary = _parse_stdout(capsys)
    assert summary["estado"] == "omitida"
    assert summary["motivo"] == "fuente-invalida"
    _assert_global_json_valido(tmp_path)


# --------------------------------------------------------------------------- 2


def test_main_http_500_simulado_degrada_a_omitida_fuente_invalida(
    tmp_path, monkeypatch, capsys
):
    """HTTP 500 simulado: omitida/fuente-invalida, sin abortar."""
    monkeypatch.setenv("GEN_SPECKIT_GLOBAL_DIR", str(tmp_path))

    def fake_urlopen(url, timeout=None):
        return _FakeResponse(b'{"rows": []}', status=500)

    monkeypatch.setattr(classify_models.urllib.request, "urlopen", fake_urlopen)

    code = classify_models.main(["--refrescar", "--json"])

    assert code == 0
    summary = _parse_stdout(capsys)
    assert summary["estado"] == "omitida"
    assert summary["motivo"] == "fuente-invalida"
    _assert_global_json_valido(tmp_path)


# --------------------------------------------------------------------------- 3


def test_main_json_invalido_simulado_degrada_a_omitida_fuente_invalida(
    tmp_path, monkeypatch, capsys
):
    """Respuesta HTTP 200 con cuerpo no-JSON: omitida/fuente-invalida, sin abortar."""
    monkeypatch.setenv("GEN_SPECKIT_GLOBAL_DIR", str(tmp_path))

    def fake_urlopen(url, timeout=None):
        return _FakeResponse(b"esto no es json valido", status=200)

    monkeypatch.setattr(classify_models.urllib.request, "urlopen", fake_urlopen)

    code = classify_models.main(["--refrescar", "--json"])

    assert code == 0
    summary = _parse_stdout(capsys)
    assert summary["estado"] == "omitida"
    assert summary["motivo"] == "fuente-invalida"
    _assert_global_json_valido(tmp_path)


# --------------------------------------------------------------------------- 4


def test_main_sin_red_sin_clasificacion_previa_omitida_sin_red(
    tmp_path, monkeypatch, capsys
):
    """--sin-red con almacen vacio: omitida/sin-red."""
    monkeypatch.setenv("GEN_SPECKIT_GLOBAL_DIR", str(tmp_path))

    code = classify_models.main(["--sin-red", "--json"])

    assert code == 0
    summary = _parse_stdout(capsys)
    assert summary["estado"] == "omitida"
    assert summary["motivo"] == "sin-red"
    _assert_global_json_valido(tmp_path)


# --------------------------------------------------------------------------- 5


def test_main_sin_red_con_clasificacion_previa_reutilizada(
    tmp_path, monkeypatch, capsys
):
    """--sin-red con snapshot previo valido: reutilizada."""
    monkeypatch.setenv("GEN_SPECKIT_GLOBAL_DIR", str(tmp_path))

    path = classify_models._global_path()
    classify_models.save_global_store(path, _snapshot_global())

    code = classify_models.main(["--sin-red", "--json"])

    assert code == 0
    summary = _parse_stdout(capsys)
    assert summary["estado"] == "reutilizada"
    _assert_global_json_valido(tmp_path)
