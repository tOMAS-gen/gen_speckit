#!/usr/bin/env python3
"""Administra definiciones genéricas de CLI en .specify/models.json (port de clis-config.ps1, T011).

Operaciones: agregar | editar | eliminar | verificar. Reutiliza scan_models (ranking + merge
+ escritura canónica), invoke_secondary (comando headless + patrones de cuota) y
platform_helper (resolver ejecutable, auth por hints). Solo stdlib.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import tempfile
import time
from pathlib import Path

_DIR = Path(__file__).resolve().parent


def _load_mod(name, filename):
    spec = importlib.util.spec_from_file_location(name, _DIR / filename)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_pf = _load_mod("_gen_platform", "platform_helper.py")
_scan = _load_mod("_gen_scan", "scan_models.py")
_inv = _load_mod("_gen_invoke", "invoke_secondary.py")


def read_cli_inventory(models_path):
    if not models_path or not str(models_path).strip():
        raise ValueError("Falta --models-path")
    p = Path(models_path)
    if not p.is_file():
        raise FileNotFoundError(f"No existe el inventario: {models_path}")
    with open(p, "r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or "clis" not in data:
        raise ValueError("Inventario inválido: falta la sección 'clis'")
    return data


def get_catalog_data(models_path):
    catalog_path = Path(models_path).resolve().parent / "clis-catalog.json"
    if not catalog_path.is_file():
        return None
    with open(catalog_path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def get_cli_validation_problems(nombre, headless, modelos, patrones_cuota,
                                existing_clis, check_duplicate=False):
    problems = []
    if not nombre or not re.match(r"^[a-z][a-z0-9-]*$", nombre):
        problems.append("V1: formato de nombre invalido (kebab-case)")
    if check_duplicate and isinstance(existing_clis, dict) and nombre in existing_clis:
        problems.append("V2: duplicado: ofrecer editar el existente")
    if not headless or "{prompt}" not in headless:
        problems.append("V3: plantilla sin placeholder de prompt")

    model_list = list(modelos) if modelos else []
    if len(model_list) > 1 and (
        not headless or ("{modelo}" not in headless
                         and not re.search(r"(?i)(?:^|\s)--model(?:\s|=)", headless))):
        problems.append("V4: no se puede seleccionar modelo")
    if len(model_list) < 1:
        problems.append("V5: modelo invalido (se requiere al menos uno)")
    else:
        ids = {}
        for i, m in enumerate(model_list):
            pos = i + 1
            if not isinstance(m, dict):
                problems.append(f"V5: modelo {pos} invalido (debe ser una tabla)")
                continue
            mid = str(m.get("id", ""))
            if not mid.strip():
                problems.append(f"V5: modelo {pos} invalido (id vacio)")
            elif mid in ids:
                problems.append(f"V5: modelo {pos} invalido (id duplicado '{mid}')")
            else:
                ids[mid] = True
            for field, lo, hi in (("capacidad", 1, 10), ("costo", 1, 3)):
                try:
                    n = int(m.get(field))
                except (TypeError, ValueError):
                    n = None
                if n is None or n < lo or n > hi:
                    problems.append(f"V5: modelo {pos} invalido ({field} debe estar entre {lo} y {hi})")

    for i, pat in enumerate(patrones_cuota or []):
        try:
            re.compile(str(pat))
        except re.error:
            problems.append(f"V6: patron {i + 1} no es una regex valida")
    return problems


def assert_cli_definition(nombre, headless, modelos, patrones_cuota,
                          existing_clis, check_duplicate=False):
    problems = get_cli_validation_problems(nombre, headless, modelos, patrones_cuota,
                                           existing_clis, check_duplicate)
    if problems:
        raise ValueError("Definicion rechazada:\n - " + "\n - ".join(problems))


def get_authentication_status(nombre, catalog, installed):
    if not installed:
        return False
    clis = (catalog or {}).get("clis") if isinstance(catalog, dict) else None
    if not clis or nombre not in clis:
        return "desconocido"
    definition = clis[nombre]
    auth_hints = definition.get("auth_hints") if isinstance(definition, dict) else None
    if not isinstance(auth_hints, dict):
        return "desconocido"
    os_fam = _pf.os_family()
    if os_fam not in auth_hints:
        return "desconocido"
    vals = auth_hints[os_fam]
    for hint in (vals if isinstance(vals, list) else [vals]):
        if Path(_pf.expand_portable_path(str(hint))).exists():
            return True
    return False


def update_cli_assignment(data, models_path):
    enabled = {k: v for k, v in data["clis"].items() if not v.get("deshabilitado")}
    proposed = _scan.build_asignacion(enabled)
    scan_path = Path(models_path).resolve().parent / "models.scan.json"
    previous = None
    scan = None
    if scan_path.is_file():
        try:
            with open(scan_path, "r", encoding="utf-8-sig") as fh:
                scan = json.load(fh)
            previous = scan.get("asignacion")
        except (OSError, json.JSONDecodeError):
            pass
    if previous is None:
        data["asignacion"] = proposed
    else:
        data["asignacion"] = _scan.merge_preserving_user_edits(
            proposed, data.get("asignacion"), previous)
    if scan is not None:
        scan["asignacion"] = proposed
        _scan.write_json2(scan_path, scan)


def save_cli_inventory(data, models_path):
    update_cli_assignment(data, models_path)
    _scan.write_json2(models_path, data)


def add_cli_definition(models_path, nombre, headless, modelos,
                       patrones_cuota=None, version_cmd=None):
    data = read_cli_inventory(models_path)
    assert_cli_definition(nombre, headless, modelos, patrones_cuota,
                          data["clis"], check_duplicate=True)
    catalog = get_catalog_data(models_path)
    executable = _pf.resolve_executable(nombre)
    installed = executable is not None
    entry = {
        "instalado": installed,
        "autenticado": get_authentication_status(nombre, catalog, installed),
        "version": "desconocido",
        "headless": headless,
        "plan": "desconocido",
        "cuota": "desconocido",
        "origen": "registrado",
        "modelos": list(modelos or []),
    }
    if patrones_cuota is not None:
        entry["patrones_cuota"] = list(patrones_cuota)
    if version_cmd is not None:
        entry["version_cmd"] = version_cmd
    data["clis"][nombre] = entry
    save_cli_inventory(data, models_path)
    return {"operacion": "agregar", "cli": nombre, "instalado": installed,
            "autenticado": entry["autenticado"]}


def edit_cli_definition(models_path, nombre, headless=None, modelos=None,
                        patrones_cuota=None, version_cmd=None):
    data = read_cli_inventory(models_path)
    if nombre not in data["clis"]:
        raise ValueError(f"CLI '{nombre}' no existe en el inventario")
    candidate = dict(data["clis"][nombre])
    if headless is not None:
        candidate["headless"] = headless
    if modelos is not None:
        candidate["modelos"] = list(modelos)
    if patrones_cuota is not None:
        candidate["patrones_cuota"] = list(patrones_cuota)
    if version_cmd is not None:
        candidate["version_cmd"] = version_cmd
    patterns = candidate.get("patrones_cuota", [])
    assert_cli_definition(nombre, str(candidate.get("headless", "")),
                          candidate.get("modelos", []), patterns, data["clis"])
    data["clis"][nombre] = candidate
    save_cli_inventory(data, models_path)
    return {"operacion": "editar", "cli": nombre}


def get_active_cli_task_labels(models_path, nombre):
    specs_dir = Path(models_path).resolve().parent.parent / "specs"
    if not specs_dir.is_dir():
        return []
    escaped = re.escape(nombre)
    warnings = []
    for sub in specs_dir.iterdir():
        tasks = sub / "tasks.md"
        if not tasks.is_file():
            continue
        for ln, line in enumerate(tasks.read_text(encoding="utf-8").splitlines(), 1):
            if re.match(r"^\s*-\s*\[\s\]", line) and re.search(rf"\[M:{escaped}(?:/|\])", line):
                warnings.append({"archivo": str(tasks), "linea": ln, "tarea": line.strip()})
    return warnings


def remove_cli_definition(models_path, nombre, confirmado=False):
    if not confirmado:
        raise ValueError(f"Se requiere confirmacion explicita: repita con --confirmado para dar de baja '{nombre}'")
    data = read_cli_inventory(models_path)
    if nombre not in data["clis"]:
        raise ValueError(f"CLI '{nombre}' no existe en el inventario")
    warnings = get_active_cli_task_labels(models_path, nombre)
    catalog = get_catalog_data(models_path)
    is_catalog = isinstance(catalog, dict) and nombre in (catalog.get("clis") or {})
    if is_catalog:
        data["clis"][nombre]["deshabilitado"] = True
        change = "deshabilitado"
    else:
        del data["clis"][nombre]
        change = "eliminado"
    save_cli_inventory(data, models_path)
    return {"operacion": "eliminar", "cli": nombre, "cambio": change, "advertencias": warnings}


def invoke_cli_verification(models_path, nombre, aprobar_prueba=False, timeout_seconds=120):
    data = read_cli_inventory(models_path)
    if nombre not in data["clis"]:
        raise ValueError(f"CLI '{nombre}' no existe en el inventario")
    catalog = get_catalog_data(models_path)
    diagnostics = []

    exe_hints = _inv.get_cli_data_value(data, catalog, nombre, "exe_hints", []) or []
    exe = _pf.resolve_executable(nombre, exe_hints)
    installed = exe is not None
    diagnostics.append({"nivel": "a", "resultado": "ok" if installed else "fallo",
                        "detalle": f"ejecutable resuelto: {exe}" if installed else "no se resolvio el ejecutable",
                        "correccion": "" if installed else "instalar el CLI o corregir el PATH"})

    auth = False
    if not installed:
        diagnostics.append({"nivel": "b", "resultado": "omitido", "detalle": "pendiente de nivel a",
                            "correccion": "resolver el nivel a primero"})
    else:
        auth = get_authentication_status(nombre, catalog, True)
        if auth is True:
            diagnostics.append({"nivel": "b", "resultado": "ok", "detalle": "autenticado", "correccion": ""})
        elif auth is False:
            diagnostics.append({"nivel": "b", "resultado": "fallo", "detalle": "no autenticado",
                                "correccion": "ejecutar el login del CLI"})
        else:
            diagnostics.append({"nivel": "b", "resultado": "ok", "detalle": "no verificable sin prueba", "correccion": ""})

    if not installed:
        diagnostics.append({"nivel": "c", "resultado": "omitido", "detalle": "pendiente de nivel a",
                            "correccion": "resolver el nivel a primero"})
    elif not aprobar_prueba:
        diagnostics.append({"nivel": "c", "resultado": "omitido", "detalle": "prueba real no solicitada",
                            "correccion": "repetir con --aprobar-prueba (consume una llamada)"})
    else:
        entry = data["clis"][nombre]
        primer_modelo = str(entry["modelos"][0]["id"]) if entry.get("modelos") else ""
        command = _inv.get_headless_command(data, nombre, primer_modelo, "responde solo: ok")
        base = tempfile.mktemp()
        out_file, err_file = base + ".out.log", base + ".err.log"
        start = time.monotonic()
        r = _pf.run_process(command, timeout_seconds, out_file, err_file, str(Path.cwd()))
        latency = round(time.monotonic() - start, 3)
        texto = ""
        for f in (out_file, err_file):
            if Path(f).exists():
                texto += Path(f).read_text(encoding="utf-8", errors="replace") + "\n"
        patterns = _inv.get_quota_patterns(data, catalog, nombre)
        clasificacion = "fallo"
        if not r.get("timedOut") and r.get("exitCode") == 0:
            clasificacion = "exito"
        elif _inv.test_quota_pattern(patterns, texto):
            clasificacion = "cuota"
        detalle = f"comando: {command} | clasificacion: {clasificacion} | exit: {r.get('exitCode')} | latencia: {latency}s"
        if clasificacion == "exito":
            diagnostics.append({"nivel": "c", "resultado": "ok", "detalle": detalle, "correccion": ""})
        elif clasificacion == "cuota":
            diagnostics.append({"nivel": "c", "resultado": "fallo", "detalle": detalle,
                                "correccion": "cuota agotada: esperar o revisar limites"})
        else:
            diagnostics.append({"nivel": "c", "resultado": "fallo", "detalle": detalle,
                                "correccion": "revisar plantilla o configuracion del CLI"})

    # Actualiza SOLO los campos detectables.
    version = "desconocido"
    if installed:
        import subprocess
        version_cmd = str(_inv.get_cli_data_value(data, catalog, nombre, "version_cmd", "--version"))
        try:
            out = subprocess.run([exe] + version_cmd.split(), capture_output=True, text=True, timeout=30)
            line = (out.stdout or out.stderr or "").strip().splitlines()
            if line:
                version = line[0].strip()
        except (OSError, subprocess.SubprocessError):
            pass
    data["clis"][nombre]["instalado"] = installed
    data["clis"][nombre]["autenticado"] = auth if installed else False
    data["clis"][nombre]["version"] = version
    _scan.write_json2(models_path, data)
    return diagnostics


def _parse_modelos(raw):
    """--modelos acepta un JSON (lista de objetos) o None."""
    if raw is None:
        return None
    return json.loads(raw)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Administra CLIs en models.json")
    ap.add_argument("--accion", required=True, choices=["agregar", "editar", "eliminar", "verificar"])
    ap.add_argument("--models-path", required=True)
    ap.add_argument("--cli", required=True, dest="nombre")
    ap.add_argument("--headless", default=None)
    ap.add_argument("--modelos", default=None, help="JSON: lista de objetos modelo")
    ap.add_argument("--patrones-cuota", nargs="*", default=None)
    ap.add_argument("--version-cmd", default=None)
    ap.add_argument("--confirmado", action="store_true")
    ap.add_argument("--aprobar-prueba", action="store_true")
    args = ap.parse_args(argv)

    modelos = _parse_modelos(args.modelos)
    if args.accion == "agregar":
        if args.headless is None or modelos is None:
            ap.error("agregar requiere --headless y --modelos")
        result = add_cli_definition(args.models_path, args.nombre, args.headless, modelos,
                                    args.patrones_cuota, args.version_cmd)
    elif args.accion == "editar":
        result = edit_cli_definition(args.models_path, args.nombre, args.headless, modelos,
                                     args.patrones_cuota, args.version_cmd)
    elif args.accion == "eliminar":
        result = remove_cli_definition(args.models_path, args.nombre, args.confirmado)
    else:
        result = invoke_cli_verification(args.models_path, args.nombre, args.aprobar_prueba)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
