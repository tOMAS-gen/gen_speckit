"""T006 (SC-003) — filtrado de modelos deshabilitados en los rankings.

Se ejercitan build_asignacion y build_asignacion_por_fase con dicts en memoria:
no se ejecutan CLIs reales ni se toca .specify/models.json.

Estos tests son TDD: el filtrado por modelo deshabilitado aún no existe en
scan_models.py, por lo que los casos 1-4 fallan contra el código actual.
El caso 5 (merge) ya puede pasar porque merge_node trabaja por id de forma
 genérica.
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


def _catalogo_clasificacion():
    return {
        "categorias_por_fase": {
            "implement": ["coding"],
            "plan": ["math"],
        },
    }


def _clis_con_modelo_deshabilitado():
    return {
        "clia": {
            "instalado": True,
            "modelos": [
                {"id": "pro", "capacidad": 9, "costo": 3,
                 "fortalezas": {"coding": 9, "math": 6}},
                {"id": "basic", "capacidad": 5, "costo": 1,
                 "fortalezas": {"coding": 5, "math": 5}},
                {"id": "retirado", "capacidad": 10, "costo": 0, "deshabilitado": True,
                 "fortalezas": {"coding": 10, "math": 10}},
            ],
        },
    }


def test_build_asignacion_excluye_modelo_deshabilitado_mantiene_resto():
    clis = _clis_con_modelo_deshabilitado()

    asignacion = scan_models.build_asignacion(clis)

    # El modelo deshabilitado no debe aparecer en ningún nivel.
    for refs in asignacion.values():
        assert "clia/retirado" not in refs

    # clia/pro (capacidad 9) debe seguir presente en todos los niveles.
    assert "clia/pro" in asignacion["alta"]
    assert "clia/pro" in asignacion["media"]
    assert "clia/pro" in asignacion["baja"]

    # clia/basic (capacidad 5) solo califica para el nivel baja.
    assert "clia/basic" in asignacion["baja"]


def test_build_asignacion_por_fase_excluye_modelo_deshabilitado_mantiene_resto():
    clis = _clis_con_modelo_deshabilitado()
    catalogo = _catalogo_clasificacion()

    asignacion = scan_models.build_asignacion_por_fase(clis, catalogo)

    # El modelo deshabilitado no debe aparecer en ninguna fase.
    for refs in asignacion.values():
        assert "clia/retirado" not in refs

    # clia/pro debe seguir presente en todas las fases del catálogo.
    assert "clia/pro" in asignacion["implement"]
    assert "clia/pro" in asignacion["plan"]

    # clia/basic debe aparecer al menos en una fase, sin exigir presencia en todas.
    assert any("clia/basic" in refs for refs in asignacion.values())


def test_build_asignacion_fallback_sobre_habilitados_cuando_nivel_queda_vacio():
    # El único modelo de alta capacidad está deshabilitado, por lo que el nivel
    # "alta" queda vacío tras el filtrado. El fallback debe usar solo modelos
    # habilitados, ordenados por capacidad descendente.
    clis = {
        "clia": {
            "instalado": True,
            "modelos": [
                {"id": "retirado", "capacidad": 10, "costo": 0, "deshabilitado": True},
                {"id": "media", "capacidad": 6, "costo": 2},
                {"id": "baja", "capacidad": 4, "costo": 1},
            ],
        },
    }

    asignacion = scan_models.build_asignacion(clis)

    assert "clia/retirado" not in asignacion["alta"]
    assert asignacion["alta"] == ["clia/media", "clia/baja"]
    assert "clia/retirado" not in asignacion["media"]
    assert "clia/retirado" not in asignacion["baja"]


def test_build_asignacion_todos_deshabilitados_deja_listas_vacias():
    clis = {
        "clia": {
            "instalado": True,
            "modelos": [
                {"id": "m1", "capacidad": 10, "costo": 0, "deshabilitado": True},
                {"id": "m2", "capacidad": 7, "costo": 1, "deshabilitado": True},
            ],
        },
    }

    asignacion = scan_models.build_asignacion(clis)

    assert asignacion["alta"] == []
    assert asignacion["media"] == []
    assert asignacion["baja"] == []


def test_merge_preserva_modelo_deshabilitado_agregado_a_mano():
    # prev_scan = propuesta anterior sin el flag
    prev_scan = {"clis": {"clix": {"modelos": [
        {"id": "m-1", "capacidad": 7, "costo": 2},
    ]}}}
    # existing = usuario agregó a mano deshabilitado: true
    existing = {"clis": {"clix": {"modelos": [
        {"id": "m-1", "capacidad": 7, "costo": 2, "deshabilitado": True},
    ]}}}
    # proposed = re-escaneo vuelve a proponer sin el flag
    proposed = {"clis": {"clix": {"modelos": [
        {"id": "m-1", "capacidad": 7, "costo": 2},
    ]}}}

    final = scan_models.merge_preserving_user_edits(proposed, existing, prev_scan)

    modelo = final["clis"]["clix"]["modelos"][0]
    assert modelo["deshabilitado"] is True
