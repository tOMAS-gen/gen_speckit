"""T003 — pytest para resolve_phase_candidates en phase_candidates.py.

Los tests definen el contrato del módulo `.specify/scripts/python/phase_candidates.py`,
que aún no existe. Solo se usan dicts en memoria: no se ejecutan CLIs reales ni se
toca `.specify/models.json`.
"""

import copy
import datetime
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".specify" / "scripts" / "python" / "phase_candidates.py"


def _load():
    spec = importlib.util.spec_from_file_location("phase_candidates", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


phase_candidates = _load()
resolve_phase_candidates = phase_candidates.resolve_phase_candidates


def _iso(hours_offset=None):
    """Devuelve un timestamp ISO con zona horaria; opcionalmente desplazado en horas."""
    dt = datetime.datetime.now(datetime.timezone.utc)
    if hours_offset is not None:
        dt += datetime.timedelta(hours=hours_offset)
    return dt.isoformat()


def _inventory():
    """Inventario mínimo de referencia para los casos de test."""
    return {
        "clis": {
            "clia": {
                "instalado": True,
                "modelos": [
                    {"id": "pro"},
                    {"id": "basic"},
                ],
            },
            "clib": {
                "instalado": True,
                "modelos": [
                    {"id": "pro"},
                    {"id": "basic"},
                ],
            },
            "clic": {
                "instalado": True,
                "modelos": [
                    {"id": "fast"},
                ],
            },
        },
        "asignacion": {
            "alta": ["clia/pro", "clib/pro", "clic/fast", "clia/basic", "clib/basic"],
            "media": ["clia/basic", "clib/basic"],
        },
        "asignacion_por_fase": {
            "specify": ["clia/pro", "clib/basic"],
            "plan": ["clib/pro", "clia/basic"],
        },
    }


def test_usa_asignacion_por_fase_cuando_existe():
    inv = copy.deepcopy(_inventory())
    assert resolve_phase_candidates(inv, "specify", "alta", "clia/pro") == [
        "clia/pro",
        "clib/basic",
    ]


def test_falla_a_asignacion_nivel_si_fase_no_esta_en_por_fase():
    inv = copy.deepcopy(_inventory())
    assert (
        resolve_phase_candidates(inv, "implement", "alta", "clia/pro")
        == inv["asignacion"]["alta"]
    )


def test_falla_a_asignacion_nivel_si_por_fase_esta_vacia():
    inv = copy.deepcopy(_inventory())
    inv["asignacion_por_fase"]["specify"] = []
    assert (
        resolve_phase_candidates(inv, "specify", "alta", "clia/pro")
        == inv["asignacion"]["alta"]
    )


def test_falla_al_nivel_solicitado_no_siempre_alta():
    inv = copy.deepcopy(_inventory())
    assert (
        resolve_phase_candidates(inv, "implement", "media", "clia/basic")
        == inv["asignacion"]["media"]
    )


def test_excluye_cli_deshabilitado():
    inv = copy.deepcopy(_inventory())
    inv["clis"]["clia"]["deshabilitado"] = True
    assert resolve_phase_candidates(inv, "implement", "alta", "clib/pro") == [
        "clib/pro",
        "clic/fast",
        "clib/basic",
    ]


def test_excluye_modelo_deshabilitado():
    inv = copy.deepcopy(_inventory())
    inv["clis"]["clia"]["modelos"][0]["deshabilitado"] = True
    assert resolve_phase_candidates(inv, "implement", "alta", "clib/pro") == [
        "clib/pro",
        "clic/fast",
        "clia/basic",
        "clib/basic",
    ]


def test_aplica_preferido():
    inv = copy.deepcopy(_inventory())
    inv["preferido"] = "clib"
    assert resolve_phase_candidates(inv, "implement", "alta", "clib/pro") == [
        "clib/pro",
        "clib/basic",
    ]


def test_preferido_inexistente_se_ignora():
    inv = copy.deepcopy(_inventory())
    inv["preferido"] = "ghost"
    assert (
        resolve_phase_candidates(inv, "implement", "alta", "clia/pro")
        == inv["asignacion"]["alta"]
    )


def test_excluye_cuota_agotada_sin_reset():
    inv = copy.deepcopy(_inventory())
    inv["clis"]["clia"]["cuota"] = "agotada"
    assert resolve_phase_candidates(inv, "implement", "alta", "clib/pro") == [
        "clib/pro",
        "clic/fast",
        "clib/basic",
    ]


def test_cuota_agotada_con_reset_vencido_vuelve_a_ser_elegible():
    inv = copy.deepcopy(_inventory())
    inv["clis"]["clia"]["cuota"] = "agotada"
    inv["clis"]["clia"]["cuota_reset"] = _iso(-25)
    assert (
        resolve_phase_candidates(inv, "implement", "alta", "clib/pro")
        == inv["asignacion"]["alta"]
    )


def test_devuelve_lista_vacia_si_no_queda_ningun_candidato():
    inv = copy.deepcopy(_inventory())
    inv["clis"]["clia"]["deshabilitado"] = True
    inv["clis"]["clib"]["deshabilitado"] = True
    inv["clis"]["clic"]["deshabilitado"] = True
    assert resolve_phase_candidates(inv, "implement", "alta", "clia/pro") == []


def test_principal_no_se_excluye_por_cli_deshabilitado():
    inv = copy.deepcopy(_inventory())
    inv["clis"]["clia"]["deshabilitado"] = True
    assert resolve_phase_candidates(inv, "implement", "alta", "clia/pro") == [
        "clia/pro",
        "clib/pro",
        "clic/fast",
        "clib/basic",
    ]


def test_principal_no_se_excluye_por_modelo_deshabilitado():
    inv = copy.deepcopy(_inventory())
    inv["clis"]["clia"]["modelos"][0]["deshabilitado"] = True
    assert resolve_phase_candidates(inv, "implement", "alta", "clia/pro") == [
        "clia/pro",
        "clib/pro",
        "clic/fast",
        "clia/basic",
        "clib/basic",
    ]


def test_principal_no_se_excluye_por_cuota_agotada():
    inv = copy.deepcopy(_inventory())
    inv["clis"]["clia"]["cuota"] = "agotada"
    assert resolve_phase_candidates(inv, "implement", "alta", "clia/pro") == [
        "clia/pro",
        "clib/pro",
        "clic/fast",
        "clib/basic",
    ]
