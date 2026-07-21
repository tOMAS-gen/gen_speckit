# Reporte de Orquestación: Descubrimiento y verificación real de modelos por CLI

**Feature**: `006-model-discovery` | **Creado**: 2026-07-18 | **Principal**: claude/fable (modelo del pipeline)

## Triage

- **Complejidad de la idea**: media
- **Justificación (rúbrica)**:
  - Alcance: 2–3 componentes — `scan_models.py`, esquema del catálogo, skill `speckit-models` (+ tests).
  - Ambigüedad: media — definir mecanismo de listado por CLI, fallback sin listado, verificación web, campo de esfuerzo.
  - Riesgo: media — extiende el contrato `models.json`/catálogo, pero de forma aditiva; merge manual debe prevalecer.
- **Flujo invocado**: IDEAL | **Flujo recomendado**: IDEAL
- **Resolución de discordancia**: n/a (coinciden)
- **Punto de entrada**: claude/fable → sin cambio

## Modelos por fase

| Fase | Modelo asignado | Estado |
|------|-----------------|--------|
| specify | claude/fable | ejecutada |
| clarify | claude/sonnet | ejecutada |
| plan | claude/fable | ejecutada |
| checklist | claude/sonnet | ejecutada |
| tasks | claude/fable | ejecutada |
| analyze | claude/fable | ejecutada |
| implement | (por tarea, ver Asignaciones) | ejecutada (11/11 verificadas) |

## Asignaciones

| Tarea | C | M | Estado |
|-------|---|---|--------|
| T001 | media | codex/gpt-5.6-sol | verificada |
| T002 | alta | claude/fable | verificada |
| T003 | media | codex/gpt-5.6-sol | verificada |
| T004 | media | kimi/k3 | verificada |
| T005 | baja | kimi/kimi-for-coding | verificada |
| T006 | media | claude/sonnet | verificada |
| T007 | media | codex/gpt-5.6-terra | verificada |
| T008 | media | kimi/k3 | verificada |
| T009 | media | codex/gpt-5.5 | verificada |
| T010 | baja | claude/haiku | verificada |
| T011 | alta | claude/fable | verificada |

<!-- Principio IV: claude 4, codex 4, kimi 3 — los 3 participan. alta→claude/fable. -->

## Eventos

- [2026-07-18] triage — idea clasificada media; flujo IDEAL confirmado (coincide con el invocado); sin escalada/degradación.
- [2026-07-18] specify — spec.md creado en specs/006-model-discovery/ sin [NEEDS CLARIFICATION] (defaults documentados en Assumptions).
- [2026-07-18] clarify — 1 pregunta: modelos oficial-sin-confirmar SÍ entran al ranking (opción B del usuario; el fallback del orquestador absorbe indisponibles).
- [2026-07-18] plan — research: ningún CLI actual expone listado headless de modelos → cadena modelos_cmd → config_hints → semillas + verificación oficial por el agente. Contrato aditivo (origen/esfuerzos/verificacion_web).
- [2026-07-18] checklist — discovery.md (19 ítems); 1 gap con default documentado (CHK017 modelo retirado: no se borra automático).
- [2026-07-18] tasks — 11 tareas (US1:4, US2:2, US3:1, setup:1, polish:3); asignador aplicó [C:]/[M:].

- [2026-07-18] implement — despacho real: 7 tareas a secundarios (codex 4, kimi 3), 4 en sesión (claude). Todas verificadas antes de [X].
- [2026-07-18] implement/T002-T003 — 2 bugs de calidad detectados en verificación y corregidos por el principal: heurística golosa (claves internas como modelos) y matching substring que duplicaba; regla anti-ruido (dígito o guion) + matching exacto-primero.
- [2026-07-18] implement/E2E — detección real en esta máquina: kimi 3/3 modelos + esfuerzos de k3 [low,high,max] desde config.toml; claude 6 modelos del cache local (en root fresco); codex 1. Escaneo sobre el inventario real preservó plan/cuota del usuario (merge OK); en inventarios pre-006 editados a mano, `origen` no aparece hasta --force (el usuario prevalece — comportamiento por diseño).

## Métricas

**Tareas por modelo** (11): claude/fable 3 · claude/sonnet 1 · claude/haiku 1 · codex/gpt-5.6-sol 2 · codex/gpt-5.6-terra 1 · codex/gpt-5.5 1 · kimi/k3 2 · kimi/kimi-for-coding 1.

- **Reparto por CLI**: claude 5 · codex 4 · kimi 3 → los 3 participan (Principio IV ✓; la corrección de bugs sumó trabajo del principal en T002/T003).
- **% modelos económicos** (costo < 3): 6/11 = 55% (feature corta con 3 tareas alta de detección/E2E).
- **Fallbacks por cuota**: 0. **Suite**: 45/45. **Logs**: specs/006-model-discovery/orchestration-logs/.
