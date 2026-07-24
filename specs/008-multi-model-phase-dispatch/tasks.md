---

description: "Task list template for feature implementation"
---

# Tasks: Despacho multi-modelo de todas las fases

**Input**: Design documents from `/specs/008-multi-model-phase-dispatch/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: incluidos — el proyecto tiene suite pytest activa (96 tests) y la Constitución exige validar contra el flujo completo; los cambios a scripts llevan tests primero.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

**Etiquetas multi-CLI (opcionales, aditivas)** — las agrega el asignador multi-CLI al
final de la fase tasks; se ubican después de las etiquetas oficiales y son editables a
mano antes de implementar. No alteran el formato oficial:

- **[C:baja|media|alta]**: complejidad clasificada de la tarea
- **[M:cli/modelo]**: modelo responsable (p. ej. `[M:kimi/k2]`), según `.specify/models.json`

## Path Conventions

- Scripts del orquestador: `.specify/scripts/python/`
- Playbooks: `.specify/orchestrator/`
- Skills: `.claude/skills/<nombre>/SKILL.md`
- Copias empaquetadas del producto: `src/specify_cli/gen_multicli/assets/`
- Tests: `tests/python/`

---

## Phase 1: Setup

**Purpose**: preparación mínima; no hay dependencias nuevas que instalar

- [X] T001 [C:baja] [M:claude/haiku] Verificar línea base: correr `python -m pytest tests/python -q` y registrar que la suite existente pasa completa antes de cualquier cambio (anotar el conteo en specs/008-multi-model-phase-dispatch/orchestration-report.md, sección Eventos)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: `--prompt-file` y la resolución de candidatos son prerequisitos de las tres historias (US1 los usa para despachar, US2 los alimenta, US3 los reporta)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] [C:media] [M:kimi/kimi-for-coding] Test de contrato de `--prompt-file` en tests/python/test_prompt_file.py: mutuamente excluyente con `--prompt` (ambos → exit 2, ninguno → exit 2), archivo inexistente/vacío/fuera del repo → exit 2, prompt puntero < 500 chars sin contenido interpolado, JSON de salida con campo `promptFile` (ruta con --prompt-file, null con --prompt); usar mocks como test_invoke_secondary.py (sin CLIs reales)
- [X] T003 [P] [C:media] [M:kimi/kimi-for-coding] Test de contrato de `resolve_phase_candidates` en tests/python/test_phase_candidates.py: usa `asignacion_por_fase[fase]` si existe, si no `asignacion[nivel]`; excluye CLIs deshabilitados y modelos con `deshabilitado: true`; aplica `preferido` como filtro; excluye cuota agotada no vencida (respetando `cuota_reset` pasado); lista vacía cuando no queda nadie; el principal permanece como candidato válido
- [X] T004 [C:alta] [M:claude/fable] Implementar `--prompt-file` en .specify/scripts/python/invoke_secondary.py según specs/008-multi-model-phase-dispatch/contracts/prompt-file.md: grupo mutuamente excluyente en argparse, validaciones (existe, legible, UTF-8, no vacío, dentro del repo), construcción del prompt puntero corto, campo `promptFile` en el JSON de salida; `--prompt` conserva comportamiento byte-idéntico (T002 en verde, test_invoke_secondary.py intacto)
- [X] T005 [C:media] [M:kimi/kimi-for-coding] Implementar `resolve_phase_candidates(inventory, fase, nivel_minimo, principal)` + CLI (`--fase`, `--models-path`, `--principal`, `--nivel`, salida JSON) en .specify/scripts/python/phase_candidates.py según specs/008-multi-model-phase-dispatch/data-model.md §4 (T003 en verde; stdlib solamente)

**Checkpoint**: despachador con prompts largos + resolución de candidatos listos — las historias pueden empezar

---

## Phase 3: User Story 2 - Inventario multi-modelo y configuración del usuario (Priority: P2) 🎯 se ejecuta primero: US1 consume sus campos

**Goal**: el inventario soporta `deshabilitado` por modelo individual y `preferido` a nivel raíz; el usuario los gestiona a mano o vía skill; los rankings los respetan

**Independent Test**: escenarios 2 y 3 del quickstart — deshabilitar `claude/haiku`, verificar exclusión de rankings y supervivencia al re-scan; fijar `preferido` y verificar el filtro de candidatos

**Nota de orden**: US2 se implementa antes que US1 porque `phase_candidates.py` (Foundational) y el playbook de despacho (US1) leen los campos que US2 introduce; aun así, US2 es independientemente testeable por sí sola.

### Tests for User Story 2

- [X] T006 [P] [US2] [C:media] [M:kimi/kimi-for-coding] Test de filtrado por modelo deshabilitado en tests/python/test_modelo_deshabilitado.py: `build_asignacion` y `build_asignacion_por_fase` excluyen modelos con `deshabilitado: true`; nivel que queda vacío aplica el fallback existente solo sobre habilitados; flag puesto a mano sobrevive a un ciclo scan→merge (reutilizar el patrón de test_merge_campos_nuevos.py)
- [X] T007 [P] [US2] [C:media] [M:kimi/kimi-for-coding] Tests de las acciones nuevas de clis_config en tests/python/test_clis_config.py (ampliar): `modelo-deshabilitar`/`modelo-habilitar` (V-M1: cli y modelo existen; V-M2: advertencia con tareas pendientes etiquetadas `[M:cli/modelo]`, sin bloquear), `preferido-fijar`/`preferido-quitar` (V-M3: advertencia si el CLI está deshabilitado o sin modelos habilitados; valor inexistente rechazado), salida JSON `{ok, cambios, advertencias[]}`

### Implementation for User Story 2

- [X] T008 [US2] [C:media] [M:kimi/kimi-for-coding] Filtrar modelos `deshabilitado: true` en `build_asignacion` y `build_asignacion_por_fase` de .specify/scripts/python/scan_models.py (T006 en verde; `asignacion*` persistidos NO aplican `preferido`, según contracts/inventory-fields.md §2 y §4)
- [X] T009 [US2] [C:media] [M:kimi/kimi-for-coding] Implementar acciones `modelo-deshabilitar`, `modelo-habilitar`, `preferido-fijar`, `preferido-quitar` en .specify/scripts/python/clis_config.py según contracts/inventory-fields.md §3, reutilizando `get_active_cli_task_labels` para V-M2 (T007 en verde)
- [X] T010 [US2] [C:baja] [M:claude/haiku] Documentar la gestión de habilitado por modelo y preferido en la skill .claude/skills/speckit-clis/SKILL.md: nuevas operaciones conversacionales (deshabilitar/habilitar modelo, fijar/quitar preferido), advertencias a mostrar, y regla de que la edición manual prevalece
- [X] T011 [P] [US2] [C:baja] [M:claude/haiku] Documentar el patrón de registro de agentes multi-modelo (OpenCode/Hermes como ejemplos NO incluidos en catálogo) en la skill .claude/skills/speckit-models/SKILL.md: sección breve que remite al flujo `speckit-clis` y a contracts/inventory-fields.md §5, incluyendo el caso de agente sin selección de modelo (FR-008)

**Checkpoint**: inventario con granularidad por modelo y preferencia del usuario funcionando y testeado

---

## Phase 4: User Story 1 - Repartir todas las fases entre modelos (Priority: P1) 🎯 MVP

**Goal**: las fases no interactivas se ejecutan vía headless en el modelo asignado, con verificación del principal, ciclo de recuperación y fallback por cuota; clarify/analyze usan el patrón de dos despachos

**Independent Test**: escenario 4 del quickstart — despachar la fase checklist de una feature de juguete al modelo asignado con `--prompt-file`, verificar artefacto (2 niveles), registrar `Efectivo`; inducir un artefacto inválido y observar reintento → escalada → principal

### Implementation for User Story 1

- [X] T012 [US1] [C:alta] [M:claude/fable] Crear el playbook .specify/orchestrator/dispatch-phase.md según contracts/phase-dispatch.md: entrada (fase, modelo asignado desde la tabla del reporte, candidatos vía phase_candidates.py), empaquetado del prompt de fase en specs/<feature>/.phase-dispatch/<fase>.prompt.md, invocación vía invoke_secondary.py --prompt-file, verificación de 2 niveles (tabla de secciones obligatorias por fase), ciclo de recuperación FR-003 (reintento → escalada → principal en sesión), fallback por cuota (update_quota.py + siguiente candidato), patrón de dos despachos para clarify/analyze (questions.md/answers.md), mapeo explícito fase→nivel mínimo (clarify/analyze/tasks:asignación → `alta`, resto según triage; FR-005a), reglas duras (no auto-invocación, solo el principal escribe estado)
- [X] T013 [US1] [C:media] [M:kimi/kimi-for-coding] Actualizar .specify/orchestrator/triage.md: el "modo decisión-solo" deja de ser el comportamiento por defecto — con inventario válido las fases se ejecutan según dispatch-phase.md (FR-013); decisión-solo queda como fallback documentado (sin inventario o modo clásico pedido); registrar en Eventos cuando se cae al fallback
- [X] T014 [P] [US1] [C:alta] [M:claude/fable] Actualizar .specify/orchestrator/assign.md y .specify/orchestrator/orchestrate.md: los candidatos excluyen modelos deshabilitados y respetan `preferido` (vía la misma semántica que phase_candidates.py); orchestrate.md documenta `--prompt-file` como vía para prompts largos (>7000 chars) en el despacho de tareas; registrar restricciones del usuario en Eventos
- [X] T015 [US1] [C:alta] [M:claude/fable] Actualizar la skill .claude/skills/speckit-specify-auto/SKILL.md: cada fase (specify/clarify/plan/checklist/tasks/analyze) consulta la tabla "Modelos por fase" y ejecuta vía dispatch-phase.md cuando el asignado no es el principal (con inventario válido); fases interactivas con patrón de dos despachos; retomabilidad relee la tabla y despacha solo `pendiente`; sin inventario → comportamiento actual sin cambios
- [X] T016 [P] [US1] [C:media] [M:kimi/kimi-for-coding] Actualizar la skill .claude/skills/speckit-specify-auto-eco/SKILL.md con el mismo cableado de despacho de fases para el ciclo mínimo (specify → plan → tasks → gate → implement)
- [X] T017 [US1] [C:baja] [M:claude/haiku] Agregar `specs/*/.phase-dispatch/` a la limpieza/documentación de artefactos: documentar el directorio en .specify/orchestrator/README.md (qué contiene, que es intermedio y auditable, convención de nombres `<fase>.prompt.md|questions.md|answers.md`, logs `fase-<fase>` en orchestration-logs/)

**Checkpoint**: pipeline con reparto real de fases funcionando de punta a punta con fallbacks

---

## Phase 5: User Story 3 - Reparto visible en el reporte (Priority: P3)

**Goal**: el reporte registra asignado vs. efectivo por fase, eventos de fallback y métricas del pipeline completo

**Independent Test**: escenario 5 del quickstart — al cerrar un pipeline, la tabla muestra `Efectivo` por fase (incluida una reasignación inducida) y Métricas incluye el % económico del trabajo total

### Implementation for User Story 3

- [X] T018 [US3] [C:baja] [M:claude/haiku] Extender .specify/orchestrator/report-template.md: columna `Efectivo` en la tabla "Modelos por fase" (aditiva, al lado de `Modelo asignado`), comentario de compatibilidad (parsers toleran 3 o 4 columnas), y sección Métricas ampliada con desglose fases-por-modelo y % del trabajo total (fases + tareas) en modelos económicos (costo < 3)
- [X] T019 [US3] [C:media] [M:kimi/kimi-for-coding] Actualizar dispatch-phase.md y las skills de pipeline (speckit-specify-auto, speckit-specify-auto-eco) para escribir `Efectivo` + Estado al cerrar cada fase y registrar en Eventos toda reasignación/escalada/caída al principal con causa, marcando explícitamente las restricciones que provienen de configuración del usuario (FR-008b)

**Checkpoint**: transparencia completa del reparto en el reporte

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: sincronización del producto empaquetado y validación final

- [X] T020 [C:media] [M:kimi/kimi-for-coding] Sincronizar las copias empaquetadas del producto en src/specify_cli/gen_multicli/assets/: scripts-python/ (invoke_secondary.py, phase_candidates.py nuevo, scan_models.py, clis_config.py), orchestrator/ (dispatch-phase.md nuevo, triage.md, assign.md, orchestrate.md, README.md, report-template.md) y skills-multicli/ (speckit-specify-auto, speckit-specify-auto-eco, speckit-clis, speckit-models) — byte-idénticas a las fuentes de .specify/ y .claude/skills/
- [X] T021 [C:media] [M:kimi/kimi-for-coding] Verificar que tests/python/test_product_delivery.py y test_no_regression.py cubren los archivos nuevos (phase_candidates.py, dispatch-phase.md): ampliar las listas de entrega si es necesario y correr la suite completa `python -m pytest tests/python -q` en verde
- [X] T022 [C:alta] [M:claude/fable] Ejecutar la validación del quickstart (specs/008-multi-model-phase-dispatch/quickstart.md, escenarios 1–4 y 6; el 5 requiere pipeline real y queda documentado como validación manual) y registrar resultados en la sección Métricas del orchestration-report.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup — BLOQUEA todas las historias
- **US2 (Phase 3)**: depende de Foundational; se ejecuta primero porque introduce los campos que US1 consume
- **US1 (Phase 4)**: depende de Foundational; T014 depende de T008/T009 (campos de US2)
- **US3 (Phase 5)**: depende de US1 (el despacho debe existir para reportarlo)
- **Polish (Phase 6)**: depende de todas las historias

### Task-level

- T004 depende de T002; T005 depende de T003
- T008 depende de T006; T009 depende de T007
- T012 depende de T004 y T005; T013–T017 dependen de T012
- T014 depende además de T008 y T009
- T019 depende de T012 y T018
- T020 depende de todo lo anterior; T021 de T020; T022 de T021

### Parallel Opportunities

- T002 ∥ T003 (tests foundational, archivos distintos)
- T006 ∥ T007 (tests US2, archivos distintos)
- T010 ∥ T011 (skills distintas)
- T014 ∥ T015 ∥ T016 (playbooks vs. skills distintas) una vez T012 hecho
- T016 ∥ T017

---

## Parallel Example: Foundational

```bash
# Lanzar los dos tests de contrato juntos:
Task: "Test de contrato de --prompt-file en tests/python/test_prompt_file.py"
Task: "Test de contrato de resolve_phase_candidates en tests/python/test_phase_candidates.py"
```

---

## Implementation Strategy

### MVP First

1. Phase 1–2 (línea base + prompt-file + candidatos)
2. Phase 3 (US2: campos de inventario — habilitador)
3. Phase 4 (US1: despacho de fases) → **MVP: pipeline con reparto real**
4. Validar con el quickstart escenario 4
5. Phase 5–6 (transparencia + empaquetado)

### Incremental Delivery

- Tras Phase 2: `--prompt-file` ya es útil por sí solo para tareas largas de implement (deuda de la feature 007)
- Tras Phase 3: la configuración del usuario (deshabilitar/preferido) ya funciona para el reparto de tareas existente
- Tras Phase 4: el pedido central del usuario está entregado
- Phase 5–6 cierran transparencia y producto instalable

---

## Notes

- [P] tasks = different files, no dependencies
- Solo el principal marca `[X]`, tras verificación estándar (diff + tests)
- Los cambios a playbooks/skills son Markdown portable: sin features exclusivas de un CLI (Constitución II)
- Todo cambio de esquema del inventario es aditivo (Constitución I)

## Asignación multi-CLI

**Asignador**: claude/fable (primer candidato de `asignacion.alta` con cuota).
**Reparto**: 22 tareas — 5 `alta` → `claude/fable`, 12 `media` → `kimi/kimi-for-coding`,
5 `baja` → `claude/haiku`. **77% del trabajo va a modelos económicos** (costo < 3).

**Justificación (Constitución IV / assign.md Paso 3)**: `codex` está instalado,
autenticado y con cuota `ok` pero quedó con cero tareas — no es exclusión por
preferencia: el playbook toma el PRIMER candidato calificado de cada nivel y en el
ranking vigente codex no encabeza ninguno (`alta` → claude/fable, `media` →
kimi/kimi-for-coding, `baja` → claude/haiku). Codex es el fallback inmediato de los
tres niveles si un titular agota cuota.

**Advertencia**: re-generar `tasks.md` (re-ejecutar `/speckit-tasks`) pierde las
etiquetas `[C:]`/`[M:]` y exige re-asignar (playbook assign.md en modo directo). Las
etiquetas son editables a mano antes de implementar; la edición manual prevalece.
