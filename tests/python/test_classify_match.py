"""T017 — pytest para classify_models.py: match_models con casos reales del research."""

import importlib.util
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


# Conjunto de entradas_leaderboard basado en la sección R1.2 de research.md.
ENTRADAS_LEADERBOARD = [
    {"model_name": "claude-fable-5", "rating": 1507.48},
    {"model_name": "kimi-k3", "rating": 1400.0},
    {"model_name": "gpt-5.6-sol-xhigh", "rating": 1450.0},
    # Familia claude-opus: ambigua para "claude/opus".
    {"model_name": "claude-opus-4-6", "rating": 1300.0},
    {"model_name": "claude-opus-4-6-thinking", "rating": 1310.0},
    {"model_name": "claude-opus-4-7", "rating": 1320.0},
    # Familia claude-sonnet: ambigua para "claude/sonnet".
    {"model_name": "claude-sonnet-4-6", "rating": 1250.0},
    {"model_name": "claude-sonnet-5-high", "rating": 1260.0},
    # Familia gpt-5.5: ambigua para "codex/gpt-5.5" (no está en el inventario de estos tests).
    {"model_name": "gpt-5.5", "rating": 1200.0},
    {"model_name": "gpt-5.5-high", "rating": 1210.0},
    {"model_name": "gpt-5.5-instant", "rating": 1190.0},
    # Modelo cercano pero DISTINTO a "kimi/kimi-for-coding".
    {"model_name": "kimi-k2.7-code", "rating": 1350.0},
]

# Inventario fijo para forzar la heurística de contención (sin alias sembrado).
MODELOS_INVENTARIO = [
    "claude/fable",
    "claude/opus",
    "claude/sonnet",
    "codex/gpt-5.6-sol",
    "codex/gpt-5.6-terra",
    "kimi/k3",
    "kimi/kimi-for-coding",
]


def _buscar_ambiguo(ambiguos, ref):
    for caso in ambiguos:
        if caso.get("ref") == ref:
            return caso
    return None


# ---------------------------------------------------------------- match_models: resueltos


def test_match_models_claude_fable_resuelto_sin_alias():
    """claude/fable matchea inequívocamente contra claude-fable-5 sin alias."""
    resueltos, ambiguos, sin_dato = classify_models.match_models(
        MODELOS_INVENTARIO, ENTRADAS_LEADERBOARD, alias={}
    )

    assert "claude/fable" in resueltos
    assert resueltos["claude/fable"]["model_name"] == "claude-fable-5"
    assert _buscar_ambiguo(ambiguos, "claude/fable") is None
    assert "claude/fable" not in sin_dato


def test_match_models_kimi_k3_resuelto_sin_alias():
    """kimi/k3 matchea inequívocamente contra kimi-k3 sin alias."""
    resueltos, ambiguos, sin_dato = classify_models.match_models(
        MODELOS_INVENTARIO, ENTRADAS_LEADERBOARD, alias={}
    )

    assert "kimi/k3" in resueltos
    assert resueltos["kimi/k3"]["model_name"] == "kimi-k3"
    assert _buscar_ambiguo(ambiguos, "kimi/k3") is None
    assert "kimi/k3" not in sin_dato


def test_match_models_codex_gpt56sol_resuelto_unica_variante():
    """codex/gpt-5.6-sol matchea contra gpt-5.6-sol-xhigh (única variante existente)."""
    resueltos, ambiguos, sin_dato = classify_models.match_models(
        MODELOS_INVENTARIO, ENTRADAS_LEADERBOARD, alias={}
    )

    assert "codex/gpt-5.6-sol" in resueltos
    assert resueltos["codex/gpt-5.6-sol"]["model_name"] == "gpt-5.6-sol-xhigh"
    assert _buscar_ambiguo(ambiguos, "codex/gpt-5.6-sol") is None
    assert "codex/gpt-5.6-sol" not in sin_dato


# ---------------------------------------------------------------- match_models: ambiguos


def test_match_models_claude_opus_ambiguo_sin_alias():
    """claude/opus es ambiguo porque hay varias variantes claude-opus-4-*."""
    resueltos, ambiguos, sin_dato = classify_models.match_models(
        MODELOS_INVENTARIO, ENTRADAS_LEADERBOARD, alias={}
    )

    assert "claude/opus" not in resueltos
    caso = _buscar_ambiguo(ambiguos, "claude/opus")
    assert caso is not None
    assert len(caso["candidatos"]) > 1
    assert "claude-opus-4-6" in caso["candidatos"]
    assert "claude/opus" not in sin_dato


def test_match_models_claude_sonnet_ambiguo_sin_alias():
    """claude/sonnet es ambiguo porque hay varias variantes claude-sonnet-*."""
    resueltos, ambiguos, sin_dato = classify_models.match_models(
        MODELOS_INVENTARIO, ENTRADAS_LEADERBOARD, alias={}
    )

    assert "claude/sonnet" not in resueltos
    caso = _buscar_ambiguo(ambiguos, "claude/sonnet")
    assert caso is not None
    assert len(caso["candidatos"]) > 1
    assert "claude-sonnet-4-6" in caso["candidatos"]
    assert "claude/sonnet" not in sin_dato


# ---------------------------------------------------------------- match_models: sin dato


def test_match_models_codex_gpt56terra_sin_dato():
    """codex/gpt-5.6-terra no existe en el leaderboard: queda sin dato."""
    resueltos, ambiguos, sin_dato = classify_models.match_models(
        MODELOS_INVENTARIO, ENTRADAS_LEADERBOARD, alias={}
    )

    assert "codex/gpt-5.6-terra" not in resueltos
    assert _buscar_ambiguo(ambiguos, "codex/gpt-5.6-terra") is None
    assert "codex/gpt-5.6-terra" in sin_dato


def test_match_models_kimi_for_coding_sin_dato_no_asocia_por_parecido():
    """kimi/kimi-for-coding no existe; NO debe asociarse por parecido a kimi-k2.7-code.

    Este test protege contra el bug más caro: heredar el puntaje de un modelo distinto.
    """
    resueltos, ambiguos, sin_dato = classify_models.match_models(
        MODELOS_INVENTARIO, ENTRADAS_LEADERBOARD, alias={}
    )

    assert "kimi/kimi-for-coding" not in resueltos
    # En particular, no debe resolverse contra el modelo parecido pero distinto.
    if "kimi/kimi-for-coding" in resueltos:
        assert resueltos["kimi/kimi-for-coding"]["model_name"] != "kimi-k2.7-code"
    assert _buscar_ambiguo(ambiguos, "kimi/kimi-for-coding") is None
    assert "kimi/kimi-for-coding" in sin_dato


# ---------------------------------------------------------------- match_models: alias override


def test_match_models_claude_opus_resuelto_con_alias_override():
    """Con alias declarado, claude/opus resuelve directo sin ambigüedad."""
    alias = {"claude/opus": "claude-opus-4-6"}
    resueltos, ambiguos, sin_dato = classify_models.match_models(
        MODELOS_INVENTARIO, ENTRADAS_LEADERBOARD, alias=alias
    )

    assert "claude/opus" in resueltos
    assert resueltos["claude/opus"]["model_name"] == "claude-opus-4-6"
    assert _buscar_ambiguo(ambiguos, "claude/opus") is None
    assert "claude/opus" not in sin_dato
