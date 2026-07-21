"""T030 — pytest para build_asignacion_por_fase en scan_models.py.

Solo se ejercita la función pura con dicts en memoria: no se ejecutan CLIs reales
ni se toca .specify/models.json.
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


def _clis_base():
    return {
        "clia": {
            "instalado": True,
            "modelos": [
                {"id": "pro", "capacidad": 5, "costo": 3,
                 "fortalezas": {"coding": 9, "math": 6}},
                {"id": "mathwiz", "capacidad": 5, "costo": 3,
                 "fortalezas": {"coding": 6, "math": 9}},
                {"id": "basic", "capacidad": 5, "costo": 1,
                 "fortalezas": {"coding": 5, "math": 5}},
            ],
        },
    }


def test_build_asignacion_por_fase_ordena_por_fortalezas_por_fase():
    clis = _clis_base()
    catalogo = _catalogo_clasificacion()

    asignacion = scan_models.build_asignacion_por_fase(clis, catalogo)

    assert set(asignacion.keys()) == {"implement", "plan"}
    # "coding" determina implement: pro (9) > mathwiz (6) > basic (5)
    assert asignacion["implement"] == ["clia/pro", "clia/mathwiz", "clia/basic"]
    # "math" determina plan: mathwiz (9) > pro (6) > basic (5)
    assert asignacion["plan"] == ["clia/mathwiz", "clia/pro", "clia/basic"]


def test_build_asignacion_por_fase_incluye_modelo_sin_fortalezas():
    clis = _clis_base()
    clis["clia"]["modelos"].append(
        {"id": "nofort", "capacidad": 7, "costo": 2}
    )
    catalogo = _catalogo_clasificacion()

    asignacion = scan_models.build_asignacion_por_fase(clis, catalogo)

    for fase in ("implement", "plan"):
        refs = asignacion[fase]
        assert "clia/nofort" in refs
        # El puntaje de respaldo es la capacidad (7), por encima de mathwiz/pro en
        # sus categorías débiles y por debajo de sus categorías fuertes.
        assert refs.index("clia/nofort") == 1

    # implement: pro(9) > nofort(7) > mathwiz(6) > basic(5)
    assert asignacion["implement"] == [
        "clia/pro", "clia/nofort", "clia/mathwiz", "clia/basic",
    ]
    # plan: mathwiz(9) > nofort(7) > pro(6) > basic(5)
    assert asignacion["plan"] == [
        "clia/mathwiz", "clia/nofort", "clia/pro", "clia/basic",
    ]


def test_build_asignacion_por_fase_excluye_deshabilitado():
    clis = _clis_base()
    clis["clib"] = {
        "instalado": True,
        "deshabilitado": True,
        "modelos": [
            {"id": "ghost", "capacidad": 10, "costo": 0,
             "fortalezas": {"coding": 10, "math": 10}},
        ],
    }
    catalogo = _catalogo_clasificacion()

    asignacion = scan_models.build_asignacion_por_fase(clis, catalogo)

    for refs in asignacion.values():
        assert all(not r.startswith("clib/") for r in refs)


def test_build_asignacion_por_fase_excluye_no_instalado():
    clis = _clis_base()
    clis["clib"] = {
        "instalado": False,
        "modelos": [
            {"id": "absent", "capacidad": 10, "costo": 0,
             "fortalezas": {"coding": 10, "math": 10}},
        ],
    }
    catalogo = _catalogo_clasificacion()

    asignacion = scan_models.build_asignacion_por_fase(clis, catalogo)

    for refs in asignacion.values():
        assert all(not r.startswith("clib/") for r in refs)


def test_build_asignacion_por_fase_no_mutacion_ni_efecto_secundario():
    import copy

    clis = _clis_base()
    clis_original = copy.deepcopy(clis)
    catalogo = _catalogo_clasificacion()

    asignacion_antes = scan_models.build_asignacion(clis)
    asignacion_por_fase = scan_models.build_asignacion_por_fase(clis, catalogo)
    asignacion_despues = scan_models.build_asignacion(clis)

    # build_asignacion_por_fase no debe mutar el dict de entrada.
    assert clis == clis_original
    # build_asignacion debe producir el mismo resultado antes y después.
    assert asignacion_antes == asignacion_despues
    # Las dos funciones son independientes: el resultado por fases no afecta
    # el ranking general y viceversa.
    assert asignacion_por_fase is not None


def test_build_asignacion_por_fase_determinista():
    clis = _clis_base()
    catalogo = _catalogo_clasificacion()

    primera = scan_models.build_asignacion_por_fase(clis, catalogo)
    segunda = scan_models.build_asignacion_por_fase(clis, catalogo)

    assert primera == segunda


def test_build_asignacion_por_fase_sin_categorias_devuelve_vacio():
    clis = _clis_base()

    assert scan_models.build_asignacion_por_fase(clis, {}) == {}
    assert scan_models.build_asignacion_por_fase(clis, {"escala": {}}) == {}
