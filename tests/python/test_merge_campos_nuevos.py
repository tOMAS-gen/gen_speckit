"""T008 (SC-003) — las ediciones manuales de campos nuevos (esfuerzos, origen)
sobreviven un re-escaneo.

Se ejercita merge_preserving_user_edits de scan_models.py con dicts en memoria:
no se llama a scan_models() ni se toca .specify/models.json real.
"""

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".specify" / "scripts" / "python" / "scan_models.py"


def _load():
    spec = importlib.util.spec_from_file_location("scan_models", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


scan_models = _load()


def _modelo(esfuerzos, origen):
    return {"id": "m-1", "esfuerzos": esfuerzos, "origen": origen}


def _wrap(modelo):
    return {"clis": {"clix": {"modelos": [modelo]}}}


def test_ediciones_usuario_en_campos_nuevos_sobreviven_rescaneo():
    # prev_scan = propuesta VIEJA tal como la dejó el escaneo anterior
    prev_scan = _wrap(_modelo(["low", "high"], "detectado-local"))
    # existing = el usuario editó esfuerzos y origen a mano
    existing = _wrap(_modelo(["max"], "semilla"))
    # proposed = el re-escaneo vuelve a proponer los valores detectados
    proposed = _wrap(_modelo(["low", "high"], "detectado-local"))

    final = scan_models.merge_preserving_user_edits(proposed, existing, prev_scan)

    modelo = final["clis"]["clix"]["modelos"][0]
    # difieren de prev_scan -> edición manual, prevalecen los valores del usuario
    assert modelo["esfuerzos"] == ["max"]
    assert modelo["origen"] == "semilla"


def test_sin_edicion_usuario_gana_proposed_nuevo():
    prev_scan = _wrap(_modelo(["low", "high"], "detectado-local"))
    # el usuario no tocó nada: existing coincide con prev_scan
    existing = _wrap(_modelo(["low", "high"], "detectado-local"))
    # el re-escaneo trae valores nuevos
    proposed = _wrap(_modelo(["low", "medium", "high"], "detectado-local"))

    final = scan_models.merge_preserving_user_edits(proposed, existing, prev_scan)

    modelo = final["clis"]["clix"]["modelos"][0]
    assert modelo["esfuerzos"] == ["low", "medium", "high"]
    assert modelo["origen"] == "detectado-local"


def test_force_siempre_gana_proposed():
    prev_scan = _wrap(_modelo(["low", "high"], "detectado-local"))
    # incluso con ediciones manuales del usuario...
    existing = _wrap(_modelo(["max"], "semilla"))
    proposed = _wrap(_modelo(["low", "high"], "detectado-local"))

    final = scan_models.merge_preserving_user_edits(proposed, existing, prev_scan, force=True)

    assert final == proposed
    modelo = final["clis"]["clix"]["modelos"][0]
    assert modelo["esfuerzos"] == ["low", "high"]
    assert modelo["origen"] == "detectado-local"
