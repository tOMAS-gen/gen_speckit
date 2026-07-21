"""T007 — conservación del estado de verificación web en el inventario."""

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".specify" / "scripts" / "python" / "scan_models.py"


def _load():
    spec = importlib.util.spec_from_file_location("scan_models_verificacion_web", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scan_models = _load()


def _build(existing=None):
    detections = {"testcli": {"instalado": True, "version": "1.0"}}
    auth = {"testcli": True}
    catalog = {"clis": {"testcli": {"modelos": []}}}
    return scan_models.build_inventory(detections, auth, catalog, existing)


def test_build_inventory_verificacion_web_omitida_sin_valor_previo():
    clis = _build()

    assert clis["testcli"]["verificacion_web"] == {"estado": "omitida"}


def test_build_inventory_conserva_verificacion_web_existente():
    verificacion = {"estado": "hecha", "fecha": "2026-07-18"}
    existing = {"clis": {"testcli": {"verificacion_web": verificacion}}}

    clis = _build(existing)

    assert clis["testcli"]["verificacion_web"] == verificacion
