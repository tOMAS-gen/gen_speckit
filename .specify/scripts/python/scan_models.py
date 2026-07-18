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


def build_inventory(detections, auth, catalog, existing):
    clis = {}
    for cli in sorted(detections.keys()):
        det = detections[cli]
        headless = get_catalog_cli_value(existing, catalog, cli, "headless", "")
        modelos = get_catalog_cli_value(existing, catalog, cli, "modelos", None)
        if modelos is None:
            modelos = get_catalog_cli_value(None, catalog, cli, "modelos_semilla", [])
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


def _canonical(value):
    """JSON comparable (mismo criterio que ConvertTo-CanonicalJson: compacto ordenado)."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


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
    # Hojas/arrays: si el existente difiere de la propuesta previa -> edición manual, prevalece.
    exis_json = _canonical(exis)
    prev_json = _canonical(prev) if prev is not None else None
    return exis if (prev_json is None or exis_json != prev_json) else prop


def merge_preserving_user_edits(proposed, existing, prev_scan, force=False):
    if force or existing is None:
        return proposed
    return merge_node(proposed, existing, prev_scan)


def write_json2(path, obj):
    _platform.write_utf8_nobom(str(path), json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def scan_models(repo_root=None, force=False, probe_auth=False):
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

    clis = build_inventory(detections, auth, catalog, existing)
    proposed = {"clis": clis, "asignacion": build_asignacion(clis)}
    final = merge_preserving_user_edits(proposed, existing, prev_scan, force)

    write_json2(scan_path, proposed)
    write_json2(models_path, final)
    return {"models_path": str(models_path), "scan_path": str(scan_path),
            "detections": detections, "auth": auth, "names": names}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Escanea CLIs y genera models.json")
    ap.add_argument("--repo-root", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--probe-auth", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    r = scan_models(args.repo_root, args.force, args.probe_auth)
    if args.json:
        summary = {"MODELS_JSON": r["models_path"], "SCAN_JSON": r["scan_path"],
                   "CLIS": {c: {"instalado": r["detections"][c]["instalado"],
                                "version": r["detections"][c]["version"],
                                "autenticado": r["auth"][c]} for c in r["names"]}}
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
