"""T010 — pytest para scan_models.py con detección MOCKEADA (sin ejecutar CLIs reales).

Solo se ejercitan las funciones puras (build_asignacion, build_inventory,
merge_preserving_user_edits) con dicts en memoria: no se llama a scan_models()
ni se toca .specify/models.json real.
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


# ---------------------------------------------------------------- build_asignacion

def _clis_sample():
    return {
        "clia": {
            "instalado": True,
            "modelos": [
                {"id": "pro", "capacidad": 9, "costo": 3},
                {"id": "mini", "capacidad": 6, "costo": 1},
            ],
        },
        "clib": {
            "instalado": True,
            "modelos": [
                {"id": "max", "capacidad": 8, "costo": 2},
                {"id": "lite", "capacidad": 4, "costo": 0},
            ],
        },
    }


def test_build_asignacion_niveles_y_orden():
    a = scan_models.build_asignacion(_clis_sample())

    # alta: capacidad >= 8, orden (-capacidad, costo)
    assert a["alta"] == ["clia/pro", "clib/max"]
    # media: capacidad >= 6, orden (costo, -capacidad)
    assert a["media"] == ["clia/mini", "clib/max", "clia/pro"]
    # baja: todos, orden (costo, capacidad)
    assert a["baja"] == ["clib/lite", "clia/mini", "clib/max", "clia/pro"]


def test_build_asignacion_excluye_deshabilitado():
    clis = _clis_sample()
    clis["clib"]["deshabilitado"] = True
    a = scan_models.build_asignacion(clis)

    refs = a["alta"] + a["media"] + a["baja"]
    assert all(not r.startswith("clib/") for r in refs)
    assert a["alta"] == ["clia/pro"]
    assert a["baja"] == ["clia/mini", "clia/pro"]


def test_build_asignacion_excluye_no_instalado():
    clis = _clis_sample()
    clis["clib"]["instalado"] = False
    a = scan_models.build_asignacion(clis)

    refs = a["alta"] + a["media"] + a["baja"]
    assert all(not r.startswith("clib/") for r in refs)


# ---------------------------------------------------------------- build_inventory

def test_build_inventory_entradas():
    detections = {
        "clia": {"instalado": True, "version": "1.2.3"},
        "clib": {"instalado": False, "version": "desconocido"},
    }
    auth = {"clia": True, "clib": False}
    catalog = {
        "clis": {
            "clia": {
                "headless": "clia run {prompt}",
                "modelos": [{"id": "pro", "capacidad": 9, "costo": 3}],
            },
            "clib": {
                "headless": "clib exec {prompt}",
                "modelos_semilla": [{"id": "max", "capacidad": 8, "costo": 2}],
            },
        },
    }

    clis = scan_models.build_inventory(detections, auth, catalog, existing=None)

    assert set(clis.keys()) == {"clia", "clib"}

    ea = clis["clia"]
    assert ea["instalado"] is True
    assert ea["autenticado"] is True
    assert ea["version"] == "1.2.3"
    assert ea["headless"] == "clia run {prompt}"
    assert ea["modelos"] == [{"id": "pro", "capacidad": 9, "costo": 3}]
    assert ea["origen"] == "catalogo"

    eb = clis["clib"]
    assert eb["instalado"] is False
    assert eb["autenticado"] is False
    # sin "modelos" en catálogo cae a "modelos_semilla"
    assert eb["modelos"] == [{"id": "max", "capacidad": 8, "costo": 2}]


def test_build_inventory_respeta_deshabilitado_existente():
    detections = {"clia": {"instalado": True, "version": "1.0"}}
    auth = {"clia": True}
    catalog = {"clis": {"clia": {"modelos": []}}}
    existing = {"clis": {"clia": {"deshabilitado": True, "plan": "pago"}}}

    clis = scan_models.build_inventory(detections, auth, catalog, existing)

    assert clis["clia"]["deshabilitado"] is True
    assert clis["clia"]["plan"] == "pago"


# ------------------------------------------------- merge_preserving_user_edits

def test_merge_edicion_usuario_prevalece():
    prev_scan = {"clis": {"clia": {"plan": "desconocido", "cuota": "desconocido"}}}
    existing = {"clis": {"clia": {"plan": "suscripción de pago", "cuota": "desconocido"}}}
    proposed = {"clis": {"clia": {"plan": "desconocido", "cuota": "ok"}}}

    final = scan_models.merge_preserving_user_edits(proposed, existing, prev_scan)

    # el usuario editó "plan" (difiere de prev_scan): prevalece su valor
    assert final["clis"]["clia"]["plan"] == "suscripción de pago"
    # "cuota" no fue editada por el usuario: gana la propuesta nueva
    assert final["clis"]["clia"]["cuota"] == "ok"


def test_merge_force_gana_proposed():
    prev_scan = {"clis": {"clia": {"plan": "desconocido"}}}
    existing = {"clis": {"clia": {"plan": "suscripción de pago"}}}
    proposed = {"clis": {"clia": {"plan": "desconocido"}}}

    final = scan_models.merge_preserving_user_edits(proposed, existing, prev_scan, force=True)

    assert final == proposed
    assert final["clis"]["clia"]["plan"] == "desconocido"


def test_merge_sin_existing_devuelve_proposed():
    proposed = {"clis": {}, "asignacion": {"alta": [], "media": [], "baja": []}}
    assert scan_models.merge_preserving_user_edits(proposed, None, None) == proposed


def test_inventory_has_origen_y_contrato_intacto():
    catalog = {
        "clis": {
            "ficli": {
                "modelos_semilla": [
                    {"id": "m-1", "capacidad": 7, "costo": 2},
                ],
            },
        },
    }
    detections = {"ficli": {"instalado": True, "version": "0.1"}}
    auth = {"ficli": True}

    clis = scan_models.build_inventory(detections, auth, catalog, existing=None, detected_models={})

    modelo = clis["ficli"]["modelos"][0]
    assert modelo["id"] == "m-1"
    assert modelo["capacidad"] == 7
    assert modelo["costo"] == 2

    semillas = catalog["clis"]["ficli"]["modelos_semilla"]
    con_origen = scan_models.apply_detected_models(semillas, {})
    assert con_origen[0]["origen"] == "semilla"


# ------------------------------------------------- merge preserva corrección manual de nivel (T018)

def _modelo_fable(capacidad, rating, nivel_origen="medido"):
    return {
        "id": "fable",
        "capacidad": capacidad,
        "costo": 3,
        "nivel_origen": nivel_origen,
        "clasificacion": {
            "entrada": "claude-fable-5",
            "rating": rating,
            "publicado": "2026-07-19" if rating > 1500 else "2026-07-01",
        },
    }


def test_merge_preserving_user_edits_mantiene_correccion_manual_de_nivel():
    prev_scan = {"clis": {"claude": {"modelos": [_modelo_fable(7, 1507.0)]}}}
    existing = {"clis": {"claude": {"modelos": [_modelo_fable(3, 1507.0, "manual")]}}}
    proposed = {"clis": {"claude": {"modelos": [_modelo_fable(9, 1550.0)]}}}

    final = scan_models.merge_preserving_user_edits(proposed, existing, prev_scan)

    modelo = final["clis"]["claude"]["modelos"][0]
    assert modelo["capacidad"] == 3
    assert modelo["nivel_origen"] == "manual"
    # campos no editados por el usuario siguen la propuesta nueva
    assert modelo["clasificacion"]["rating"] == 1550.0


def test_merge_node_mantiene_correccion_manual_de_nivel():
    prev_scan_modelo = _modelo_fable(7, 1507.0)
    existing_modelo = _modelo_fable(3, 1507.0, "manual")
    proposed_modelo = _modelo_fable(9, 1550.0)

    final = scan_models.merge_node(proposed_modelo, existing_modelo, prev_scan_modelo)

    assert final["capacidad"] == 3
    assert final["nivel_origen"] == "manual"
    assert final["clasificacion"]["rating"] == 1550.0
