#!/usr/bin/env python3
"""Detecta CLIs de IA y genera .specify/models.json con inventario y ranking (port de
scan-models.ps1, T009).

Genérico: ningún nombre de CLI vive en el código. Los CLIs conocidos salen del catálogo
`.specify/clis-catalog.json`; los registrados por el usuario, del propio inventario.
Resolución: inventario > catálogo > defaults. Preserva ediciones manuales comparando
contra `.specify/models.scan.json`. Respeta `deshabilitado`. Salida UTF-8, indent 2.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_HELPER = Path(__file__).resolve().parent / "platform_helper.py"
_spec = importlib.util.spec_from_file_location("_gen_platform", _HELPER)
_platform = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_platform)

# Clasificación de niveles desde fuente externa (feature 007). Import por ruta,
# igual que platform_helper; si el archivo no existe (proyecto sin la feature),
# el paso de clasificación se saltea y el escaneo funciona como siempre.
_CLASSIFY_PATH = Path(__file__).resolve().parent / "classify_models.py"
_classify_module = None
if _CLASSIFY_PATH.is_file():
    _cspec = importlib.util.spec_from_file_location("_gen_classify", _CLASSIFY_PATH)
    _classify_module = importlib.util.module_from_spec(_cspec)
    _cspec.loader.exec_module(_classify_module)

DEFAULT_QUOTA_PATTERNS = ["rate limit", "quota", r"\b429\b", "usage limit"]


def _load(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def get_catalog(repo_root):
    path = Path(repo_root) / ".specify" / "clis-catalog.json"
    fallback = {"version": 0, "patrones_cuota_genericos": list(DEFAULT_QUOTA_PATTERNS), "clis": {}}
    if not path.is_file():
        return fallback
    try:
        return _load(path)
    except (OSError, json.JSONDecodeError):
        return fallback


def get_catalog_cli_value(existing, catalog, cli, key, default=None):
    for source in (existing, catalog):
        if isinstance(source, dict):
            entry = (source.get("clis") or {}).get(cli)
            if isinstance(entry, dict) and key in entry:
                return entry[key]
    return default


def get_cli_names(catalog, existing):
    names = []
    for source in (catalog, existing):
        if isinstance(source, dict):
            for n in (source.get("clis") or {}).keys():
                if n not in names:
                    names.append(n)
    return names


def detect_cli(name, version_cmd="--version", exe_hints=None):
    result = {"instalado": False, "version": "desconocido"}
    exe = _platform.resolve_executable(name, exe_hints or [])
    if exe:
        result["instalado"] = True
        try:
            out = subprocess.run([exe] + version_cmd.split(), capture_output=True,
                                 text=True, timeout=30)
            line = (out.stdout or out.stderr or "").strip().splitlines()
            if line:
                result["version"] = line[0].strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return result


def get_auth_hints_for_os(auth_hints):
    if not isinstance(auth_hints, dict):
        return []
    os_fam = _platform.os_family()
    val = auth_hints.get(os_fam)
    if val is None:
        return []
    return val if isinstance(val, list) else [val]


def get_auth_status(name, auth_hints=None, headless="", probe=False):
    for hint in (auth_hints or []):
        if Path(_platform.expand_portable_path(hint)).exists():
            return True
    if probe and headless:
        try:
            import re as _re
            cmd = _re.sub(r"\s*--model\s+\S*\{modelo\}\S*", "", headless)
            cmd = cmd.replace("{prompt}", "responde solo: ok")
            r = _platform.run_process(cmd, 120, subprocess.DEVNULL if False else str(Path("_authprobe.out")),
                                      str(Path("_authprobe.err")), str(Path.cwd()))
            return r.get("exitCode") == 0
        except Exception:
            return False
    return "desconocido"


# --------------------------------------------------------------------------- #
# Descubrimiento real de modelos por CLI (feature 006).
# Cadena: modelos_cmd (si no consume o aprobado) -> config_hints -> semillas.
# Nunca inventa: todo modelo queda con `origen` in {detectado-local, semilla,
# oficial-sin-confirmar}. Parseo tolerante: cualquier eslabón que falle se salta.
# --------------------------------------------------------------------------- #

_MODEL_ID_RE = None  # compilado perezoso


def _plausible_model_id(value):
    """Filtra strings que parecen ids de modelo (evita ruido de los configs).

    Regla anti-ruido: además del shape, el id debe contener un dígito o un guion
    (todos los ids reales los tienen: k3, gpt-5.6-sol, claude-opus-4-8,
    kimi-for-coding); campos como 'lastusedat'/'usagecount' quedan afuera.
    """
    global _MODEL_ID_RE
    import re as _re
    if _MODEL_ID_RE is None:
        _MODEL_ID_RE = _re.compile(r"^[a-z0-9][a-z0-9._/\-\[\]]{1,48}$")
    if not (isinstance(value, str) and _MODEL_ID_RE.match(value.strip().lower())):
        return False
    v = value.strip().lower()
    return any(ch.isdigit() for ch in v) or "-" in v


def _normalize_model_id(value):
    """'kimi-code/k3' -> 'k3'; 'claude-fable-5[1m]' -> 'claude-fable-5'."""
    v = value.strip().lower()
    if "/" in v:
        v = v.rsplit("/", 1)[-1]
    if "[" in v:
        v = v.split("[", 1)[0]
    return v


def _efforts_from_entry(entry):
    """Si la entrada del modelo declara niveles de esfuerzo, extraerlos."""
    if not isinstance(entry, dict):
        return None
    for k, v in entry.items():
        if isinstance(k, str) and "effort" in k.lower():
            if isinstance(v, list) and all(isinstance(x, str) for x in v):
                return list(v)
            if isinstance(v, str):
                return [v]
    return None


def _extract_models(node, found=None):
    """Recorre una estructura parseada (TOML/JSON) juntando modelos: {id: {esfuerzos?}}.

    Heurística genérica (sin nombres de CLI): bajo una clave cuyo nombre contiene
    'model' y cuyo valor es un dict, las claves INMEDIATAS plausibles son ids de
    modelo (un solo nivel — las claves internas son campos, no modelos). Si la
    entrada del modelo declara esfuerzos (clave con 'effort'), se capturan.
    """
    if found is None:
        found = {}
    if isinstance(node, dict):
        for k, v in node.items():
            k_is_modelish = isinstance(k, str) and "model" in k.lower()
            if k_is_modelish and isinstance(v, dict):
                for mk, mv in v.items():
                    if _plausible_model_id(str(mk)):
                        mid = _normalize_model_id(str(mk))
                        meta = found.setdefault(mid, {})
                        efforts = _efforts_from_entry(mv)
                        if efforts:
                            meta["esfuerzos"] = efforts
            elif k_is_modelish and isinstance(v, str) and _plausible_model_id(v):
                found.setdefault(_normalize_model_id(v), {})
            else:
                _extract_models(v, found)
    elif isinstance(node, list):
        for item in node:
            _extract_models(item, found)
    return found


def _load_config_file(path):
    """Parsea un config local (TOML o JSON). Devuelve None si no se puede (tolerante)."""
    p = Path(path)
    if not p.is_file():
        return None
    try:
        raw = p.read_bytes()
        if p.suffix.lower() == ".toml":
            import tomllib
            return tomllib.loads(raw.decode("utf-8", errors="replace"))
        return json.loads(raw.decode("utf-8-sig", errors="replace"))
    except Exception:
        return None


def _get_config_hints_for_os(existing, catalog, cli):
    hints = get_catalog_cli_value(existing, catalog, cli, "config_hints", None)
    if not isinstance(hints, dict):
        return []
    val = hints.get(_platform.os_family())
    if val is None:
        return []
    return val if isinstance(val, list) else [val]


def detect_models(cli, existing, catalog, probe=False):
    """Devuelve dict {id: {esfuerzos?}} de modelos detectados localmente para un CLI.

    1. `modelos_cmd` del catálogo (solo si no consume cuota, o `probe=True`).
    2. `config_hints`: archivos de config locales del CLI.
    Cualquier eslabón ausente/fallido se salta sin abortar (contrato: tolerante).
    """
    detected = {}

    cmd = get_catalog_cli_value(existing, catalog, cli, "modelos_cmd", None)
    consume = bool(get_catalog_cli_value(existing, catalog, cli, "modelos_cmd_consume", False))
    if cmd and (probe or not consume):
        try:
            out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            for line in (out.stdout or "").splitlines():
                token = line.strip()
                if _plausible_model_id(token):
                    detected.setdefault(_normalize_model_id(token), {})
        except (OSError, subprocess.SubprocessError):
            pass

    for hint in _get_config_hints_for_os(existing, catalog, cli):
        data = _load_config_file(_platform.expand_portable_path(str(hint)))
        if data is None:
            continue
        for mid, meta in _extract_models(data).items():
            detected.setdefault(mid, {}).update(meta)

    return detected


def apply_detected_models(modelos, detected):
    """Marca `origen`/`esfuerzos` en los modelos según la evidencia local (CHK017: no borra).

    - Semilla cuyo id matchea un detectado (igual o substring) -> `detectado-local`
      (+ esfuerzos si el config los declara y el usuario no los fijó).
    - Detectado sin semilla equivalente -> se agrega con capacidad/costo medios
      (propuesta corregible por el usuario).
    - Semilla sin evidencia -> conserva `origen` previo o queda `semilla`.
    """
    result = []
    matched = set()
    for m in modelos:
        m = dict(m)
        mid = str(m.get("id", "")).strip().lower()
        # Matching exacto-primero; substring solo como respaldo y sobre candidatos
        # aún libres (evita que 'kimi-for-coding' capture '...-highspeed').
        hit = mid if mid in detected else None
        if hit is None:
            for d in sorted(set(detected) - matched, key=len):
                if mid in d or d in mid:
                    hit = d
                    break
        if hit:
            m["origen"] = "detectado-local"
            matched.add(hit)
            efforts = (detected.get(hit) or {}).get("esfuerzos")
            if efforts and "esfuerzos" not in m:
                m["esfuerzos"] = efforts
        else:
            m.setdefault("origen", "semilla")
        result.append(m)
    for d in sorted(set(detected) - matched):
        entry = {
            "id": d, "capacidad": 5, "costo": 2, "contexto_k": "desconocido",
            "origen": "detectado-local",
        }
        efforts = (detected.get(d) or {}).get("esfuerzos")
        if efforts:
            entry["esfuerzos"] = efforts
        result.append(entry)
    return result


def build_inventory(detections, auth, catalog, existing, detected_models=None):
    clis = {}
    for cli in sorted(detections.keys()):
        det = detections[cli]
        headless = get_catalog_cli_value(existing, catalog, cli, "headless", "")
        modelos = get_catalog_cli_value(existing, catalog, cli, "modelos", None)
        if modelos is None:
            modelos = get_catalog_cli_value(None, catalog, cli, "modelos_semilla", [])
        if detected_models and cli in detected_models:
            modelos = apply_detected_models(list(modelos or []), detected_models[cli])
        origen = "registrado"
        if isinstance(catalog, dict) and cli in (catalog.get("clis") or {}):
            origen = "catalogo"
        entry = {
            "instalado": bool(det["instalado"]),
            "autenticado": auth[cli],
            "version": det["version"],
            "headless": headless,
            "origen": origen,
            "plan": get_catalog_cli_value(existing, None, cli, "plan", "desconocido"),
            "cuota": get_catalog_cli_value(existing, None, cli, "cuota", "desconocido"),
            "verificacion_web": get_catalog_cli_value(existing, None, cli, "verificacion_web", {"estado": "omitida"}),
            "modelos": list(modelos or []),
        }
        deshabilitado = get_catalog_cli_value(existing, None, cli, "deshabilitado", False)
        if deshabilitado:
            entry["deshabilitado"] = True
        patrones = get_catalog_cli_value(existing, catalog, cli, "patrones_cuota", None)
        if patrones is not None:
            entry["patrones_cuota"] = list(patrones)
        clis[cli] = entry
    return clis


def build_asignacion(clis):
    """Ranking por nivel. Nunca excluye un CLI instalado y habilitado (Constitución IV)."""
    available = []
    for cli, entry in clis.items():
        if not entry.get("instalado"):
            continue
        if entry.get("deshabilitado"):
            continue
        for m in entry.get("modelos", []):
            if m.get("deshabilitado"):
                continue
            available.append({"ref": f"{cli}/{m.get('id')}",
                              "capacidad": m.get("capacidad", 0),
                              "costo": m.get("costo", 0)})

    def by_cap_costo(x):
        return (-x["capacidad"], x["costo"])

    def by_costo_cap(x):
        return (x["costo"], -x["capacidad"])

    levels = {
        "alta": sorted([a for a in available if a["capacidad"] >= 8], key=by_cap_costo),
        "media": sorted([a for a in available if a["capacidad"] >= 6], key=by_costo_cap),
        "baja": sorted(available, key=lambda x: (x["costo"], x["capacidad"])),
    }
    asignacion = {}
    for name in ("alta", "media", "baja"):
        lst = levels[name]
        if not lst:
            lst = sorted(available, key=by_cap_costo)
        asignacion[name] = [a["ref"] for a in lst]
    return asignacion


def build_asignacion_por_fase(clis, catalogo_clasificacion):
    """Ranking por fase según fortalezas por categoría (T028, feature 007).

    Mismo criterio de elegibilidad que build_asignacion(): solo CLIs instalados
    y no deshabilitados, y ningún modelo elegible queda excluido (Constitución IV).
    Puntaje: promedio de las fortalezas presentes en las categorías de la fase;
    sin fortalezas aplicables, la capacidad general. Orden: puntaje descendente,
    empate por costo ascendente (sorted() estable conserva el orden de aparición).
    """
    categorias_por_fase = catalogo_clasificacion.get("categorias_por_fase", {})
    if not categorias_por_fase:
        return {}

    available = []
    for cli, entry in clis.items():
        if not entry.get("instalado"):
            continue
        if entry.get("deshabilitado"):
            continue
        for m in entry.get("modelos", []):
            if m.get("deshabilitado"):
                continue
            available.append({"ref": f"{cli}/{m.get('id')}",
                              "capacidad": m.get("capacidad", 0),
                              "costo": m.get("costo", 0),
                              "fortalezas": m.get("fortalezas") or {}})

    asignacion = {}
    for fase, categorias in categorias_por_fase.items():
        def puntaje(a, _categorias=categorias):
            presentes = [a["fortalezas"][c] for c in _categorias if c in a["fortalezas"]]
            if presentes:
                return sum(presentes) / len(presentes)
            return a["capacidad"]

        ordenados = sorted(available, key=lambda a: (-puntaje(a), a["costo"]))
        asignacion[fase] = [a["ref"] for a in ordenados]
    return asignacion


def classify_inventory(clis, repo_root):
    """Aplica la clasificación del leaderboard sobre el inventario (feature 007).

    Se ejecuta ANTES de build_asignacion() para que el ranking ya refleje los
    niveles medidos, y ANTES del merge para que merge_preserving_user_edits()
    haga valer las correcciones manuales del usuario sin código nuevo (R7).
    Best-effort (FR-018): sin bloque "clasificacion" en el catálogo, sin
    classify_models.py o con la fuente externa caída, devuelve `clis` intacto.

    Devuelve (clis_actualizado, ambiguos): `ambiguos` es la lista de
    {"ref": cli_modelo, "candidatos": [model_name, ...]} sin resolver, para que
    quien llame (la skill) se la pueda ofrecer al usuario. Lista vacía si no
    hubo clasificación o no quedó ningún caso dudoso.
    """
    if _classify_module is None:
        return clis, []
    catalogo_clasificacion = _classify_module.get_catalog_classification(repo_root)
    if not catalogo_clasificacion or "escala" not in catalogo_clasificacion:
        return clis, []
    # FR-018: único punto del proyecto donde se captura Exception a secas —
    # ninguna falla de red/parseo de la fuente externa puede interrumpir el
    # escaneo completo; se degrada a "sin clasificación" y se sigue.
    try:
        datos = _classify_module.fetch_dataset("overall", catalogo_clasificacion)
        if datos is None:
            print("Aviso: clasificación omitida (fuente externa no disponible).",
                  file=sys.stderr)
            return clis, []
        entradas = _classify_module.normalize_rows(
            datos, catalogo_clasificacion.get("votos_minimos", 500))
        actualizado, ambiguos = _classify_module.aplicar_clasificacion_al_inventario(
            {"clis": clis}, catalogo_clasificacion, entradas)
        # Fortalezas por categoría (T028): para cada modelo con clasificación
        # resuelta, capacidad medida en las categorías que usan las fases.
        categorias_por_fase = catalogo_clasificacion.get("categorias_por_fase", {})
        categorias_unicas = list(dict.fromkeys(
            c for cats in categorias_por_fase.values() for c in cats))
        entradas_por_categoria = _classify_module.fetch_categorias(
            categorias_unicas, catalogo_clasificacion)
        for info in actualizado["clis"].values():
            for modelo in info.get("modelos", []):
                clasificacion = modelo.get("clasificacion") if isinstance(modelo, dict) else None
                if not isinstance(clasificacion, dict):
                    continue
                fortalezas = _classify_module.calcular_fortalezas(
                    clasificacion["entrada"], entradas_por_categoria,
                    catalogo_clasificacion["escala"])
                if fortalezas:
                    modelo["fortalezas"] = fortalezas
        if ambiguos:
            refs = ", ".join(str(a.get("ref")) for a in ambiguos)
            print(f"Aviso: clasificación ambigua para: {refs} "
                  "(se resuelve con el usuario desde la skill).", file=sys.stderr)
        return actualizado["clis"], ambiguos
    except Exception as exc:
        print(f"Aviso: clasificación omitida ({exc}); el escaneo continúa.",
              file=sys.stderr)
        return clis, []


def _canonical(value):
    """JSON comparable (mismo criterio que ConvertTo-CanonicalJson: compacto ordenado)."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _is_keyed_list(value):
    """Lista de dicts con clave "id" estable en todos sus elementos (p.ej. modelos[])."""
    return (
        isinstance(value, list)
        and len(value) > 0
        and all(isinstance(x, dict) and "id" in x for x in value)
    )


def merge_node(prop, exis, prev):
    if isinstance(exis, dict) and isinstance(prop, dict):
        out = {}
        keys = list(prop.keys()) + [k for k in exis.keys() if k not in prop]
        for k in keys:
            prev_child = prev[k] if isinstance(prev, dict) and k in prev else None
            if k not in prop:
                out[k] = exis[k]
            elif k not in exis:
                out[k] = prop[k]
            else:
                out[k] = merge_node(prop[k], exis[k], prev_child)
        return out

    # Listas de dicts con "id" estable (p.ej. modelos[]): mergear por elemento en
    # vez de tratar la lista entera como un bloque atómico. Sin esto, un campo
    # nuevo (p.ej. la clasificación de la feature 007) se pierde apenas la lista
    # difiere de la propuesta previa en CUALQUIER otro punto — que en un
    # proyecto con historia es casi siempre. La corrección manual de un campo
    # sigue prevaleciendo, pero campo a campo, no lista completa contra lista completa.
    if _is_keyed_list(prop) and _is_keyed_list(exis):
        prev_by_id = {}
        if isinstance(prev, list):
            for item in prev:
                if isinstance(item, dict) and "id" in item:
                    prev_by_id[item["id"]] = item
        exis_by_id = {item["id"]: item for item in exis}
        out = []
        seen = set()
        for item in prop:
            mid = item["id"]
            seen.add(mid)
            if mid in exis_by_id:
                out.append(merge_node(item, exis_by_id[mid], prev_by_id.get(mid)))
            else:
                out.append(item)
        # Preservar entradas existentes que el usuario agregó a mano y no
        # vinieron en la propuesta nueva (p.ej. un modelo declarado manualmente).
        for item in exis:
            if item["id"] not in seen:
                out.append(item)
        return out

    # Hojas/arrays sin "id" estable: si el existente difiere de la propuesta previa -> edición manual, prevalece.
    exis_json = _canonical(exis)
    prev_json = _canonical(prev) if prev is not None else None
    return exis if (prev_json is None or exis_json != prev_json) else prop


def merge_preserving_user_edits(proposed, existing, prev_scan, force=False):
    if force or existing is None:
        return proposed
    return merge_node(proposed, existing, prev_scan)


def write_json2(path, obj):
    _platform.write_utf8_nobom(str(path), json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def scan_models(repo_root=None, force=False, probe_auth=False, probe_models=False):
    if not repo_root:
        repo_root = str(Path(__file__).resolve().parents[3])
    models_path = Path(repo_root) / ".specify" / "models.json"
    scan_path = Path(repo_root) / ".specify" / "models.scan.json"

    catalog = get_catalog(repo_root)
    existing = None
    prev_scan = None
    if models_path.is_file():
        try:
            existing = _load(models_path)
        except (OSError, json.JSONDecodeError):
            pass
    if scan_path.is_file():
        try:
            prev_scan = _load(scan_path)
        except (OSError, json.JSONDecodeError):
            pass

    names = get_cli_names(catalog, existing)
    detections, auth = {}, {}
    for cli in names:
        version_cmd = get_catalog_cli_value(existing, catalog, cli, "version_cmd", "--version")
        exe_hints = get_catalog_cli_value(existing, catalog, cli, "exe_hints", []) or []
        detections[cli] = detect_cli(cli, version_cmd, exe_hints)
        if detections[cli]["instalado"]:
            hints = get_auth_hints_for_os(get_catalog_cli_value(existing, catalog, cli, "auth_hints", None))
            headless = get_catalog_cli_value(existing, catalog, cli, "headless", "")
            auth[cli] = get_auth_status(cli, hints, headless, probe_auth)
        else:
            auth[cli] = False

    detected_models = {c: detect_models(c, existing, catalog, probe_models) for c in names if detections[c]["instalado"]}
    clis = build_inventory(detections, auth, catalog, existing, detected_models=detected_models)
    clis, ambiguos = classify_inventory(clis, repo_root)
    proposed = {"clis": clis, "asignacion": build_asignacion(clis)}
    if _classify_module is not None:
        catalogo_clasificacion = _classify_module.get_catalog_classification(repo_root)
        asignacion_por_fase = build_asignacion_por_fase(clis, catalogo_clasificacion)
        if asignacion_por_fase:
            proposed["asignacion_por_fase"] = asignacion_por_fase
    final = merge_preserving_user_edits(proposed, existing, prev_scan, force)

    write_json2(scan_path, proposed)
    write_json2(models_path, final)
    return {"models_path": str(models_path), "scan_path": str(scan_path),
            "detections": detections, "auth": auth, "names": names,
            "ambiguos": ambiguos}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Escanea CLIs y genera models.json")
    ap.add_argument("--repo-root", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--probe-auth", action="store_true")
    ap.add_argument("--probe-models", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    r = scan_models(args.repo_root, args.force, args.probe_auth, args.probe_models)
    if args.json:
        summary = {"MODELS_JSON": r["models_path"], "SCAN_JSON": r["scan_path"],
                   "CLIS": {c: {"instalado": r["detections"][c]["instalado"],
                                "version": r["detections"][c]["version"],
                                "autenticado": r["auth"][c]} for c in r["names"]}}
        if r.get("ambiguos"):
            summary["AMBIGUOS"] = r["ambiguos"]
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(f"Inventario escrito en {r['models_path']}")
        for c in r["names"]:
            det = r["detections"][c]
            st = f"instalado ({det['version']})" if det["instalado"] else "AUSENTE"
            print(f"  {c:<12} {st}")
        print("Revisá y corregí a mano: plan, cuota, capacidad/costo. Tus ediciones prevalecen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
