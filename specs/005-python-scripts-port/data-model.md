# Data Model: Scripts de soporte en Python

**Feature**: 005-python-scripts-port | **Fecha**: 2026-07-18

> Feature de migración de lenguaje: las "entidades" son los **contratos de datos
> invariantes** que la versión Python debe preservar byte a byte (FR-003), más los
> artefactos de código.

## Contratos invariantes (NO cambian)

### `models.json`
Estructura `clis.<cli>` con `instalado`, `autenticado`, `version`, `headless`, `plan`,
`cuota`, `modelos[]` (`id`, `capacidad` 1–10, `costo` 1–3, `contexto_k`); y `asignacion`
con listas ordenadas `alta`/`media`/`baja`. La corrección manual del usuario prevalece.

### Etiquetas de `tasks.md`
`[C:baja|media|alta]` y `[M:cli/modelo]` inline, después de las oficiales. El formato
oficial de spec-kit (checkbox, `T###`, `[P]`, `[US#]`, ruta) no se toca.

### JSON de tandas paralelas (salida de get_parallel_groups)
`total_tareas`, `pendientes`, `sin_asignar`, `max_concurrencia`, `grupos[]` con
`paralelo` (bool) y `tareas[]` (`id`, `complejidad`, `cli`, `modelo`, `rutas[]`,
`descripcion`).

### Clasificación de resultado del despacho
`exito` | `cuota_agotada` | `indisponible` (invoke_secondary), más `intentos`,
`exitCode`, `stdoutPath`, `stderrPath`, `comando`.

### Catálogo de CLIs (`clis-catalog.json`)
Plantillas headless, `patrones_cuota`, `exe_hints`, quirks por versión — claves dinámicas
por CLI, con genéricos de respaldo.

## Entidad: Scripts Python (6)

| Script | Entrada | Salida |
|---|---|---|
| `platform.py` | (módulo helper) | funciones: os family, expand path, resolve exe, run+timeout, write utf-8 |
| `scan_models.py` | flags de salida/paths | `models.json` (+ `models.scan.json`) |
| `invoke_secondary.py` | `--cli --model --prompt --models-path --log-dir --log-base-name [--timeout]` | JSON de clasificación + logs |
| `update_quota.py` | `--cli --estado {ok,agotada} --models-path` | `models.json` actualizado |
| `get_parallel_groups.py` | `--tasks-path` | JSON de tandas |
| `clis_config.py` | `--accion {agregar,editar,eliminar,verificar} ...` | `models.json`/catálogo actualizado o reporte |

**Regla**: las interfaces CLI espejan los parámetros de los `.ps1` actuales (mismos
nombres semánticos), para que la reconexión de playbooks sea directa.

## Entidad: Invocadores

- Playbooks: `assets/orchestrator/{triage,assign,orchestrate}.md`.
- Skills: `speckit-models`, `speckit-orchestrate`, `speckit-clis`.
- Instalador/bundling: `gen_multicli/_scripts.py` + `assets/scripts-python/`.

## Entidad: Suite de tests

`tests/python/test_<script>.py` por cada uno de los 6; cubren los casos de los Pester
actuales (`tests/powershell/`). Sin dependencia de PowerShell.

## Relaciones

```
playbooks/skills ── invocan ──> python .specify/scripts/python/<script>.py
scripts python ── leen/escriben ──> contratos invariantes (models.json, tasks.md, catálogo, reportes)
platform.py ── importado por ──> los otros 5 scripts
specify init (_scripts.py) ── deposita ──> .specify/scripts/python/ (+ powershell/ transición)
tests/python ── fijan paridad de ──> contratos invariantes
```
