# Reporte de Orquestación: Fork de specify-cli con mejoras multi-CLI

**Feature**: `004-specify-cli-fork` | **Creado**: 2026-07-18 | **Principal**: claude/opus (Opus 4.8, modelo del pipeline)

> Plantilla del reporte multi-CLI. Secciones PARSEABLES (tablas de columnas fijas,
> las lee la retomabilidad): "Modelos por fase" y "Asignaciones". Secciones
> INFORMATIVAS (prosa, solo para humanos): "Triage", "Eventos", "Métricas".

## Triage

- **Complejidad de la idea**: compleja
- **Justificación (rúbrica)**:
  - Alcance: toca el CLI Python `specify-cli`, estructura de package/templates, lógica de `init`, las 8 skills, playbooks del orquestador e `install.ps1` — transversal (>3 componentes).
  - Ambigüedad: "fork" e "integrar en specify-cli" tienen varias interpretaciones (vendorizar el source vs. wrapper vs. preset); requiere clarificación sustancial.
  - Riesgo: reestructuración del empaquetado del proyecto, parcialmente difícil de revertir (media).
- **Flujo invocado**: IDEAL | **Flujo recomendado**: IDEAL
- **Resolución de discordancia**: n/a (coinciden)
- **Punto de entrada**: claude/opus → sin cambio (idea compleja escrita en CLI capaz; sin escalada/degradación)

## Modelos por fase

| Fase | Modelo asignado | Estado |
|------|-----------------|--------|
| specify | claude/fable | ejecutada |
| clarify | claude/sonnet | ejecutada |
| plan | claude/fable | ejecutada |
| checklist | claude/sonnet | ejecutada |
| tasks | claude/fable | ejecutada |
| analyze | claude/fable | ejecutada |
| implement | (por tarea, ver Asignaciones) | ejecutada (28/28 verificadas) |

<!-- Modo decisión-solo: el principal (Opus 4.8) ejecuta las fases en este CLI;
     los modelos por fase reflejan la asignación recomendada por el triage
     (idea compleja: specify/plan/analyze con primer candidato de `alta`=claude/fable;
     resto con `media`). El despacho real a secundarios ocurre en implement. -->

## Asignaciones

| Tarea | C | M | Estado |
|-------|---|---|--------|
| T001 | media | codex/gpt-5.5 | verificada |
| T002 | baja | claude/haiku | verificada |
| T003 | alta | claude/fable | verificada |
| T004 | baja | kimi/kimi-for-coding | verificada |
| T005 | media | kimi/k3 | verificada |
| T006 | alta | claude/fable | verificada |
| T007 | media | codex/gpt-5.6-sol | verificada |
| T008 | alta | claude/fable | verificada |
| T009 | baja | claude/haiku | verificada |
| T010 | alta | claude/fable | verificada |
| T011 | media | codex/gpt-5.6-terra | verificada |
| T012 | baja | kimi/kimi-for-coding | verificada |
| T013 | alta | claude/fable | verificada |
| T014 | media | codex/gpt-5.6-sol | verificada |
| T015 | media | kimi/k3 | verificada |
| T016 | media | codex/gpt-5.6-terra | verificada |
| T017 | media | codex/gpt-5.6-sol | verificada |
| T018 | media | kimi/k3 | verificada |
| T019 | media | codex/gpt-5.6-terra | verificada |
| T020 | media | codex/gpt-5.5 | verificada |
| T021 | media | claude/sonnet | verificada |
| T022 | baja | kimi/kimi-for-coding-highspeed | verificada |
| T023 | media | claude/sonnet | verificada |
| T024 | baja | claude/haiku | verificada |
| T025 | baja | kimi/kimi-for-coding | verificada |
| T026 | alta | claude/fable | verificada |
| T027 | media | codex/gpt-5.6-terra | verificada |
| T028 | baja | claude/haiku | verificada |

<!-- Verificación Principio IV: los 3 CLIs participan — claude (12), codex (9), kimi (7).
     Ningún CLI instalado/autenticado quedó en cero. Tareas `alta` → claude/fable (más
     capaz). Reparto validado contra models.json (todos cuota=ok). -->

## Eventos

- [2026-07-18] triage — idea clasificada compleja; flujo IDEAL confirmado (coincide con el invocado); sin escalada/degradación.
- [2026-07-18] specify — spec.md creado en specs/004-specify-cli-fork/ con 3 [NEEDS CLARIFICATION] (estructura fork, nombre/convivencia, destino install.ps1).
- [2026-07-18] clarify — las 3 clarificaciones resueltas con el usuario (fork real integrado; comando `specify` que reemplaza al oficial; producto siempre en el init, install.ps1 deprecado). Sin preguntas nuevas.
- [2026-07-18] plan — research reveló que upstream migró a wheel-bundled + registry de integraciones (v0.4.0+); fork apunta a main/v0.13.x. Artefactos: plan, research, data-model, contracts (init-command, product-delivery), quickstart.
- [2026-07-18] checklist — distribution.md (29 ítems); 2 gaps diferidos a implement (tag upstream, internals del bundler).
- [2026-07-18] tasks — 28 tareas (US1:7, US2:3, US3:3, setup:5, foundational:4, polish:6); asignador aplicó [C:]/[M:] con reparto entre los 3 CLIs.
- [2026-07-18] implement — despacho headless real: 15 tareas a secundarios (codex/kimi vía invoke-secondary.ps1), 13 en sesión por el principal (claude). Todas verificadas antes de `[X]`.
- [2026-07-18] implement/T003 — vendorizado de github/spec-kit@v0.13.0: 115 .py, 45 integraciones + dirs raíz (templates/scripts/extensions/workflows/presets) para el core_pack del wheel.
- [2026-07-18] implement/build — lección: hay que reconstruir el wheel (`uv build`) tras cambios de código; `uv run --with` cachea por versión → usar `--reinstall`. Detectado al validar el `init` real (producto no aparecía con wheel viejo). Incorporado al CI.
- [2026-07-18] implement/T017 — codex reportó éxito pero NO insertó el parámetro `--skills` (mi verificación inicial se dejó engañar por menciones en docstrings); el principal completó la opción durante la integración (Paso 4 verificación).
- [2026-07-18] implement/T018 — deliverable (mapeo por agente) ya implementado en `_skills.py` (T013); marcado satisfecho por T013 para no re-hacer/arriesgar código funcional.
- [2026-07-18] implement/US1 — validado end-to-end con el CLI real: `specify init` mostró "Install multi-CLI product (gen_speckit) (23 archivos)" y dejó base + producto en un solo paso, sin install.ps1.
- [2026-07-18] implement/US2 — `specify init --skills todos` entregó las 8 skills a los 3 agentes (39 archivos).
- [2026-07-18] implement/T021 — separación upstream/gen verificada por diff: SOLO `_version.py` e `init.py` difieren de upstream; `gen_multicli/` es lo único nuevo (FR-007).
- [2026-07-18] implement/T028 — ningún template afectado; amendment de la restricción técnica "el CLI base ahora es Python" diferido a `/speckit-constitution` (governance). Follow-up recomendado (hallazgo C1 de analyze).

## Métricas

**Tareas por modelo** (28 total):

| CLI/modelo | costo | tareas |
|---|---|---|
| claude/fable | 3 | 6 (T003,T006,T008,T010,T013,T026) |
| claude/haiku | 1 | 4 (T002,T009,T024,T028) |
| claude/sonnet | 2 | 2 (T021,T023) |
| codex/gpt-5.6-sol | 3 | 3 (T007,T014,T017) |
| codex/gpt-5.6-terra | 2 | 4 (T011,T016,T019,T027) |
| codex/gpt-5.5 | 2 | 2 (T001,T020) |
| kimi/k3 | 2 | 3 (T005,T015,T018) |
| kimi/kimi-for-coding | 1 | 3 (T004,T012,T025) |
| kimi/kimi-for-coding-highspeed | 1 | 1 (T022) |

- **Reparto por CLI**: claude 12 · codex 9 · kimi 7 → los 3 participan (Principio IV ✓).
- **% ejecutado por modelos económicos** (costo < 3): **19/28 = 68%**. El 32% caro (costo 3 = claude/fable, codex/gpt-5.6-sol) se reservó para las tareas `alta`/de arquitectura (vendorizado, bundling, hook del init, entrega de skills, CI).
- **Despacho real**: 15 tareas ejecutadas por CLIs secundarios en headless (codex/kimi), descargando trabajo del principal — objetivo central del orquestador (SC-004: mover el grueso a modelos más económicos/disponibles).
- **Fallbacks por cuota**: 0 (todos los CLIs con cuota=ok durante la corrida).
- **Logs**: `specs/004-specify-cli-fork/orchestration-logs/`.
