# Reporte de Orquestación: Scripts de soporte en Python (multiplataforma)

**Feature**: `005-python-scripts-port` | **Creado**: 2026-07-18 | **Principal**: claude/opus (Opus 4.8, modelo del pipeline)

## Triage

- **Complejidad de la idea**: compleja
- **Justificación (rúbrica)**:
  - Alcance: transversal — 6 scripts + playbooks (triage/assign/orchestrate) + skills (models/orchestrate/clis) + tests Pester→pytest + bundling del producto (>3 componentes).
  - Ambigüedad: baja — requisito claro (portar ps→py conservando comportamiento).
  - Riesgo: media — sistema en producción; toca despacho headless y manejo de credenciales.
- **Flujo invocado**: ECO | **Flujo recomendado**: IDEAL
- **Resolución de discordancia**: preguntado al usuario → eligió **IDEAL** (7 fases).
- **Punto de entrada**: claude/opus → sin cambio (idea compleja en CLI capaz).

## Modelos por fase

| Fase | Modelo asignado | Estado |
|------|-----------------|--------|
| specify | claude/fable | ejecutada |
| clarify | claude/sonnet | ejecutada |
| plan | claude/fable | ejecutada |
| checklist | claude/sonnet | ejecutada |
| tasks | claude/fable | ejecutada |
| analyze | claude/fable | ejecutada |
| implement | (por tarea, ver Asignaciones) | ejecutada (20/20 verificadas) |

## Asignaciones

| Tarea | C | M | Estado |
|-------|---|---|--------|
| T001 | baja | claude/haiku | verificada |
| T002 | media | codex/gpt-5.6-sol | verificada |
| T003 | media | kimi/k3 | verificada |
| T004 | baja | kimi/kimi-for-coding | verificada |
| T005 | baja | codex/gpt-5.6-luna | verificada |
| T006 | baja | claude/haiku | verificada |
| T007 | alta | claude/fable | verificada |
| T008 | media | codex/gpt-5.6-terra | verificada |
| T009 | alta | claude/fable | verificada |
| T010 | media | kimi/k3 | verificada |
| T011 | alta | claude/fable | verificada |
| T012 | media | codex/gpt-5.6-terra | verificada |
| T013 | media | codex/gpt-5.6-sol | verificada |
| T014 | media | claude/sonnet | verificada |
| T015 | media | kimi/k3 | verificada |
| T016 | media | codex/gpt-5.6-terra | verificada |
| T017 | alta | claude/fable | verificada |
| T018 | baja | claude/haiku | verificada |
| T019 | media | codex/gpt-5.5 | verificada |
| T020 | baja | kimi/kimi-for-coding | verificada |

<!-- Principio IV: claude 8, codex 7, kimi 5 — los 3 participan. alta→claude/fable. -->

- [2026-07-18] tasks — 20 tareas; asignador aplicó [C:]/[M:] con reparto entre los 3 CLIs.

## Eventos

- [2026-07-18] constitución — amendada a v1.1.0 (MINOR): restricción técnica pasa de PowerShell a Python (scripts de soporte en el lenguaje del CLI del fork), sin dependencia de pwsh. Desbloquea esta feature.
- [2026-07-18] triage — idea compleja; discordancia ECO(invocado)/IDEAL(recomendado) resuelta por el usuario → IDEAL.
- [2026-07-18] specify — spec.md creado en specs/005-python-scripts-port/ sin clarificaciones (requisito claro).
- [2026-07-18] implement — despacho real: 11 tareas a secundarios (codex/kimi headless), 9 en sesión (claude). Todas verificadas antes de `[X]`.
- [2026-07-18] implement — bug propio corregido en `invoke_secondary.py`: `re.sub` interpretaba backslashes de rutas Windows como escapes (`\U`); resuelto con repl como función.
- [2026-07-18] implement — corrección de integración: `platform.py` renombrado a `platform_helper.py` para no tapar el módulo `platform` de stdlib cuando `.specify/scripts/python/` queda en sys.path[0]. `_version`/loaders actualizados.
- [2026-07-18] implement/T007 — `invoke_secondary.py` validado con un **despacho real** a codex → `exito` (el orquestador despachando a un secundario en Python, sin PowerShell).
- [2026-07-18] implement/T009 — `scan_models.py` validado con **detección real** de los 3 CLIs (versiones + auth) y ranking `asignacion` correcto.
- [2026-07-18] implement — validación final: `specify init` real deposita 30 archivos (incluidos los 7 scripts Python); `get_parallel_groups.py` corre desde el proyecto instalado sin pwsh; suite pytest 31/31 en Windows.

## Métricas

**Tareas por modelo** (20 total): claude/fable 4 · claude/haiku 3 · claude/sonnet 1 ·
codex/gpt-5.6-terra 4 · codex/gpt-5.6-sol 2 · codex/gpt-5.5 1 · codex/gpt-5.6-luna 1 ·
kimi/k3 3 · kimi/kimi-for-coding 2.

- **Reparto por CLI**: claude 8 · codex 8 · kimi 4 → los 3 participan (Principio IV ✓).
- **% ejecutado por modelos económicos** (costo < 3): **14/20 = 70%**. El 30% caro
  (claude/fable, codex/gpt-5.6-sol) se reservó para los ports `alta` (invoke_secondary,
  scan_models, clis_config, no-regresión) y platform/seam.
- **Despacho real**: 11 tareas ejecutadas por secundarios (codex/kimi) en headless —
  descargando trabajo del principal (SC-004 del sistema).
- **Fallbacks por cuota**: 0. **Logs**: `specs/005-python-scripts-port/orchestration-logs/`.
