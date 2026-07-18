"""T006 — pytest para update_quota.py (paridad de comportamiento)."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".specify" / "scripts" / "python" / "update_quota.py"


def _load():
    spec = importlib.util.spec_from_file_location("update_quota", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _sample_models(tmp_path):
    data = {
        "clis": {
            "kimi": {"instalado": True, "plan": "suscripción de pago", "cuota": "ok",
                     "modelos": [{"id": "k3", "capacidad": 8, "costo": 2}]},
        },
        "asignacion": {"alta": ["kimi/k3"], "media": [], "baja": []},
    }
    p = tmp_path / "models.json"
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def test_set_agotada(tmp_path):
    p = _sample_models(tmp_path)
    subprocess.run([sys.executable, str(SCRIPT), "--cli", "kimi", "--estado", "agotada",
                    "--models-path", str(p)], check=True, cwd=str(REPO))
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["clis"]["kimi"]["cuota"] == "agotada"


def test_set_ok(tmp_path):
    p = _sample_models(tmp_path)
    subprocess.run([sys.executable, str(SCRIPT), "--cli", "kimi", "--estado", "ok",
                    "--models-path", str(p)], check=True, cwd=str(REPO))
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["clis"]["kimi"]["cuota"] == "ok"


def test_format_preserved(tmp_path):
    """El resto del inventario no se corrompe."""
    p = _sample_models(tmp_path)
    subprocess.run([sys.executable, str(SCRIPT), "--cli", "kimi", "--estado", "agotada",
                    "--models-path", str(p)], check=True, cwd=str(REPO))
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["clis"]["kimi"]["modelos"][0]["id"] == "k3"
    assert "asignacion" in d
