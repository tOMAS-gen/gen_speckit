#!/usr/bin/env python3
"""Despacho headless de una tarea a un CLI secundario (port de invoke-secondary.ps1, T007).

Genérico: sin nombres de CLI hardcodeados. El comando sale de la plantilla ``headless`` del
inventario (`models.json`); los patrones de cuota y los hints de ejecutable se resuelven
inventario > catálogo > defaults genéricos. Portable (Windows/Linux/macOS) vía platform.py.

Salida: JSON {clasificacion, intentos, exitCode, stdoutPath, stderrPath, comando}.
clasificacion ∈ {exito, cuota_agotada, indisponible}. Exit 0 solo si 'exito'.

Seguridad (FR-006): ejecuta dentro de --working-directory (repo), no vuelca env/credenciales
a los logs, timeout acotado y 1 solo reintento ante fallo transitorio.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

# Importar el helper (mismo dir) por ruta. Se llama platform_helper.py para NO tapar el
# módulo `platform` de stdlib cuando este dir queda en sys.path[0] al correr un script.
_HELPER = Path(__file__).resolve().parent / "platform_helper.py"
_spec = importlib.util.spec_from_file_location("_gen_platform", _HELPER)
_platform = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_platform)

DEFAULT_QUOTA_PATTERNS = ["rate limit", "quota", r"\b429\b", "usage limit"]


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def get_catalog(models_path):
    """Catálogo versionado junto al inventario. Ausente/corrupto NO es fatal."""
    catalog_path = Path(models_path).resolve().parent / "clis-catalog.json"
    if not catalog_path.is_file():
        return {"version": 0, "patrones_cuota_genericos": list(DEFAULT_QUOTA_PATTERNS), "clis": {}}
    try:
        return load_json(catalog_path)
    except (OSError, json.JSONDecodeError):
        return {"version": 0, "patrones_cuota_genericos": list(DEFAULT_QUOTA_PATTERNS), "clis": {}}


def get_cli_data_value(inventory, catalog, cli, key, default=None):
    """Resolución genérica inventario > catálogo para un campo de un CLI."""
    for source in (inventory, catalog):
        if not isinstance(source, dict):
            continue
        clis = source.get("clis") or {}
        entry = clis.get(cli)
        if isinstance(entry, dict) and entry.get(key) is not None:
            return entry[key]
    return default


def get_quota_patterns(inventory, catalog, cli):
    """Patrones de cuota agotada: inventario > catálogo del CLI > genéricos > respaldo."""
    patterns = get_cli_data_value(inventory, catalog, cli, "patrones_cuota")
    if patterns:
        return list(patterns)
    if isinstance(catalog, dict):
        gen = catalog.get("patrones_cuota_genericos")
        if gen:
            return list(gen)
    return list(DEFAULT_QUOTA_PATTERNS)


def get_headless_command(inventory, cli, model, prompt):
    """Construye el comando concreto desde la plantilla del inventario."""
    clis = (inventory or {}).get("clis") or {}
    if cli not in clis:
        raise ValueError(f"CLI '{cli}' no existe en el inventario")
    template = str(clis[cli].get("headless") or "")
    if not template.strip():
        raise ValueError(f"CLI '{cli}' no tiene plantilla headless")
    # Colapsar whitespace (un newline final partiría el comando en dos) y escapar comillas.
    sanitized = re.sub(r"\s+", " ", prompt).strip()
    escaped = sanitized.replace('"', '\\"')
    command = template.replace("{prompt}", escaped)
    if "{modelo}" in command:
        command = command.replace("{modelo}", model or "")
    elif model:
        command = f"{command} --model {model}"
    return command


def test_quota_pattern(patterns, text):
    if not text:
        return False
    for p in patterns:
        try:
            if re.search(p, text, re.IGNORECASE):
                return True
        except re.error:
            if p.lower() in text.lower():
                return True
    return False


def invoke_secondary_task(cli, model, prompt, inventory, catalog, log_dir,
                          log_base_name="tarea", timeout_seconds=900,
                          working_directory=None):
    working_directory = working_directory or str(Path.cwd())
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    command = get_headless_command(inventory, cli, model, prompt)

    # Resolver el ejecutable a ruta completa (el PATH de los hijos no es confiable).
    exe_hints = get_cli_data_value(inventory, catalog, cli, "exe_hints", []) or []
    exe = _platform.resolve_executable(cli, exe_hints)
    if exe:
        # repl como función: evita que los backslashes de la ruta (Windows) se
        # interpreten como escapes en el string de reemplazo de re.sub.
        command = re.sub(r"^\s*" + re.escape(cli) + r"(?=\s)", lambda _m: f'"{exe}"', command)

    patterns = get_quota_patterns(inventory, catalog, cli)
    intentos = 0
    clasificacion = None
    last_exit = None
    out_file = err_file = None

    while intentos < 2:
        intentos += 1
        out_file = str(Path(log_dir) / f"{log_base_name}.intento{intentos}.out.log")
        err_file = str(Path(log_dir) / f"{log_base_name}.intento{intentos}.err.log")
        r = _platform.run_process(command, timeout_seconds, out_file, err_file, working_directory)
        last_exit = r.get("exitCode")
        texto = ""
        if Path(out_file).exists():
            texto += Path(out_file).read_text(encoding="utf-8", errors="replace")
        if Path(err_file).exists():
            texto += "\n" + Path(err_file).read_text(encoding="utf-8", errors="replace")

        if not r.get("timedOut") and r.get("exitCode") == 0:
            clasificacion = "exito"
            break
        if test_quota_pattern(patterns, texto):
            clasificacion = "cuota_agotada"
            break
        if intentos >= 2:
            clasificacion = "indisponible"

    return {
        "clasificacion": clasificacion,
        "intentos": intentos,
        "exitCode": last_exit,
        "stdoutPath": out_file,
        "stderrPath": err_file,
        "comando": command,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Despacho headless a un CLI secundario")
    ap.add_argument("--cli", required=True)
    ap.add_argument("--model", default="")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--models-path", required=True)
    ap.add_argument("--log-dir", required=True)
    ap.add_argument("--log-base-name", default="tarea")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--working-directory", default=None)
    args = ap.parse_args(argv)

    inventory = load_json(args.models_path)
    catalog = get_catalog(args.models_path)
    result = invoke_secondary_task(
        args.cli, args.model, args.prompt, inventory, catalog,
        args.log_dir, args.log_base_name, args.timeout, args.working_directory,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["clasificacion"] == "exito" else 1


if __name__ == "__main__":
    sys.exit(main())
