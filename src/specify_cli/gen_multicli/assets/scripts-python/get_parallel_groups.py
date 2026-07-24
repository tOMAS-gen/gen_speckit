"""Agrupa las tareas pendientes de un tasks.md en tandas de ejecucion.

Port a Python (solo stdlib) de get-parallel-groups.ps1: las tareas [P] sin
rutas compartidas corren en paralelo (con limite de concurrencia); los
conflictos de archivo y las tareas sin rutas declaradas se serializan (FR-017).

Salida: JSON por stdout con la lista ordenada de grupos, con las mismas claves
que produce el script PowerShell (total_tareas, pendientes, sin_asignar,
max_concurrencia, grupos).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Regex del contrato task-labels.md (grupos: id, P, US, complejidad, cli, modelo, descripcion)
# El modelo admite "/" para agentes multi-modelo cuyo id incluye proveedor
# (ej. [M:opencode/cc/claude-fable-5]): el CLI es el primer segmento, el resto es el id.
TASK_LINE_REGEX = re.compile(
    r"^\s*- \[( |x|X)\] +(T\d{3,}) +"
    r"(?:(\[P\]) +)?"
    r"(?:(\[US\d+\]) +)?"
    r"(?:\[C:(baja|media|alta)\] +)?"
    r"(?:\[M:([a-z][a-z0-9-]*)/([A-Za-z0-9._/-]+)\] +)?"
    r"(.+)$"
)

# Tokens con separador de directorios y nombres sueltos con extension.
# Falsos positivos solo serializan de mas (seguro).
PATH_WITH_SEP_REGEX = re.compile(r"(?:[A-Za-z0-9_.\-]+[\\/])+[A-Za-z0-9_.\-]+")
BARE_NAME_REGEX = re.compile(r"(?<![\\/\w.])[A-Za-z0-9_\-]+\.[A-Za-z]{1,6}(?![\\/\w])")


def get_task_paths(descripcion: str) -> list[str]:
    """Extrae rutas de archivo de la descripcion, en minusculas y sin duplicados."""
    paths: list[str] = []
    for match in PATH_WITH_SEP_REGEX.finditer(descripcion):
        paths.append(match.group(0).replace("\\", "/").lower())
    for match in BARE_NAME_REGEX.finditer(descripcion):
        value = match.group(0).lower()
        if not any(p.endswith("/" + value) or p == value for p in paths):
            paths.append(value)
    return list(dict.fromkeys(paths))


def convert_from_task_line(line: str) -> dict | None:
    """Parsea una linea de tasks.md; devuelve None si no es una linea de tarea."""
    match = TASK_LINE_REGEX.match(line)
    if match is None:
        return None
    descripcion = match.group(8).strip()
    return {
        "completada": match.group(1) != " ",
        "id": match.group(2),
        "paralela": match.group(3) is not None,
        "historia": match.group(4).strip("[]") if match.group(4) is not None else None,
        "complejidad": match.group(5),
        "cli": match.group(6),
        "modelo": match.group(7),
        "descripcion": descripcion,
        "rutas": get_task_paths(descripcion),
    }


def get_parallel_groups(tareas: list[dict], max_concurrency: int = 4) -> list[dict]:
    """Tandas ordenadas: cada grupo paralelo junta tareas [P] consecutivas sin
    rutas compartidas, hasta max_concurrency. Todo lo demas va en grupos de a una."""
    grupos: list[dict] = []
    actual: list[dict] = []
    rutas_en_uso: list[str] = []

    for tarea in tareas:
        es_paralelizable = tarea["paralela"] and len(tarea["rutas"]) > 0
        conflicto = es_paralelizable and any(r in rutas_en_uso for r in tarea["rutas"])
        # Cerrar el grupo en curso si esta tarea no puede sumarse.
        if (not es_paralelizable or conflicto or len(actual) >= max_concurrency) and actual:
            grupos.append({"paralelo": len(actual) > 1, "tareas": list(actual)})
            actual = []
            rutas_en_uso = []
        if es_paralelizable:
            actual.append(tarea)
            rutas_en_uso.extend(tarea["rutas"])
        else:
            # No-[P] o sin rutas declaradas (conflicto potencial): serializar (FR-017).
            grupos.append({"paralelo": False, "tareas": [tarea]})

    if actual:
        grupos.append({"paralelo": len(actual) > 1, "tareas": list(actual)})
    return grupos


def invoke_get_parallel_groups(tasks_path: str, max_concurrency: int) -> dict:
    """Lee tasks.md, agrupa las pendientes y devuelve el resumen serializable."""
    path = Path(tasks_path)
    if not path.is_file():
        raise FileNotFoundError(f"No existe tasks.md en: {tasks_path}")

    with path.open(encoding="utf-8-sig") as handle:
        todas = [
            tarea
            for tarea in (convert_from_task_line(line.rstrip("\r\n")) for line in handle)
            if tarea is not None
        ]
    pendientes = [t for t in todas if not t["completada"]]
    grupos = get_parallel_groups(pendientes, max_concurrency)

    return {
        "total_tareas": len(todas),
        "pendientes": len(pendientes),
        "sin_asignar": sum(1 for t in pendientes if t["modelo"] is None),
        "max_concurrencia": max_concurrency,
        "grupos": [
            {
                "paralelo": grupo["paralelo"],
                "tareas": [
                    {
                        "id": t["id"],
                        "complejidad": t["complejidad"],
                        "cli": t["cli"],
                        "modelo": t["modelo"],
                        "rutas": t["rutas"],
                        "descripcion": t["descripcion"],
                    }
                    for t in grupo["tareas"]
                ],
            }
            for grupo in grupos
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Agrupa las tareas pendientes de un tasks.md en tandas de ejecucion."
    )
    parser.add_argument("--tasks-path", required=True, help="Ruta al archivo tasks.md")
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=4,
        help="Limite de tareas por grupo paralelo (default: 4)",
    )
    args = parser.parse_args()

    try:
        resumen = invoke_get_parallel_groups(args.tasks_path, args.max_concurrency)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(resumen, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
