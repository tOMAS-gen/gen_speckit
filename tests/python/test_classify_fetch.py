"""T016 — pytest para classify_models.py: fetch_dataset y normalize_rows con red mockeada."""

import importlib.util
import urllib.error
import urllib.parse
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


def _make_catalog():
    return {
        "dataset_url": "https://datasets-server.huggingface.co/rows",
        "dataset": "open-llm-leaderboard/contents",
        "config": "text_style_control",
        "split": "train",
        "timeout_s": 17,
    }


def _fake_response(body: bytes, status: int = 200):
    class _Response:
        def __init__(self, body, status):
            self._body = body
            self.status = status

        def read(self):
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    return _Response(body, status)


# ---------------------------------------------------------------- fetch_dataset


def test_fetch_dataset_usa_config_del_catalogo(monkeypatch):
    """La URL construida usa exactamente catalogo_clasificacion['config'] y nunca 'config=text' a secas."""
    captured = {"url": None, "timeout": None}

    def fake_urlopen(url, timeout=None):
        captured["url"] = url
        captured["timeout"] = timeout
        return _fake_response(b'{"rows": []}')

    monkeypatch.setattr(classify_models.urllib.request, "urlopen", fake_urlopen)

    result = classify_models.fetch_dataset("chat", _make_catalog())

    assert result == {"rows": []}
    url = captured["url"]
    assert url is not None
    query = urllib.parse.urlparse(url).query
    params = urllib.parse.parse_qs(query)
    assert params.get("config") == ["text_style_control"]
    assert "config=text_style_control" in url
    # Nunca el config hardcodeado "text" a secas.
    assert "config=text&" not in url
    assert not url.endswith("config=text")


def test_fetch_dataset_respeta_timeout(monkeypatch):
    """urlopen recibe el timeout definido en catalogo_clasificacion['timeout_s']."""
    captured = {"timeout": None}

    def fake_urlopen(url, timeout=None):
        captured["timeout"] = timeout
        return _fake_response(b'{"rows": []}')

    monkeypatch.setattr(classify_models.urllib.request, "urlopen", fake_urlopen)

    classify_models.fetch_dataset("chat", _make_catalog())

    assert captured["timeout"] == 17


def test_fetch_dataset_status_no_200_devuelve_none(monkeypatch):
    """Ante HTTP != 200 fetch_dataset devuelve None sin lanzar excepción."""
    def fake_urlopen(url, timeout=None):
        return _fake_response(b'{"rows": []}', status=500)

    monkeypatch.setattr(classify_models.urllib.request, "urlopen", fake_urlopen)

    result = classify_models.fetch_dataset("chat", _make_catalog())

    assert result is None


def test_fetch_dataset_urlerror_devuelve_none(monkeypatch):
    """Ante error de red (URLError) fetch_dataset devuelve None sin propagar."""
    def fake_urlopen(url, timeout=None):
        raise urllib.error.URLError("red caída")

    monkeypatch.setattr(classify_models.urllib.request, "urlopen", fake_urlopen)

    result = classify_models.fetch_dataset("chat", _make_catalog())

    assert result is None


def test_fetch_dataset_json_invalido_devuelve_none(monkeypatch):
    """Ante cuerpo que no es JSON válido fetch_dataset devuelve None."""
    def fake_urlopen(url, timeout=None):
        return _fake_response(b"esto no es json")

    monkeypatch.setattr(classify_models.urllib.request, "urlopen", fake_urlopen)

    result = classify_models.fetch_dataset("chat", _make_catalog())

    assert result is None


# ---------------------------------------------------------------- normalize_rows


def test_normalize_rows_descarta_fila_sin_rating():
    """Descarta filas que faltan algún campo obligatorio; conserva las completas."""
    response = {
        "rows": [
            {
                "row": {
                    "model_name": "modelo-completo",
                    "organization": "org-a",
                    "rating": 1150.0,
                    "leaderboard_publish_date": "2024-01-01",
                    "vote_count": 100,
                }
            },
            {
                "row": {
                    "model_name": "modelo-sin-rating",
                    "organization": "org-b",
                    # falta rating
                    "leaderboard_publish_date": "2024-01-02",
                    "vote_count": 200,
                }
            },
        ]
    }

    result = classify_models.normalize_rows(response, votos_minimos=10)

    assert len(result) == 1
    assert result[0]["model_name"] == "modelo-completo"


def test_normalize_rows_ordenado_por_rating_descendente_no_por_rank():
    """El orden se define por rating descendente, ignorando completamente el rank del dataset."""
    response = {
        "rows": [
            {
                "row": {
                    "model_name": "modelo-rating-bajo-rank-alto",
                    "organization": "org-a",
                    "rating": 1100.0,
                    "rank": 5,
                    "leaderboard_publish_date": "2024-01-01",
                    "vote_count": 50,
                }
            },
            {
                "row": {
                    "model_name": "modelo-rating-alto-rank-bajo",
                    "organization": "org-b",
                    "rating": 1200.0,
                    "rank": 1,
                    "leaderboard_publish_date": "2024-01-02",
                    "vote_count": 60,
                }
            },
        ]
    }

    result = classify_models.normalize_rows(response, votos_minimos=10)

    assert [r["rating"] for r in result] == [1200.0, 1100.0]
    assert result[0]["model_name"] == "modelo-rating-alto-rank-bajo"
    assert result[0]["rank_dataset"] == 1
    assert result[1]["rank_dataset"] == 5
