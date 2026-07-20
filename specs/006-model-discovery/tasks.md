---
description: "Task list for feature 006-model-discovery"
---

# Tasks: Descubrimiento y verificación real de modelos por CLI

**Input**: Design documents from `/specs/006-model-discovery/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: incluidos (SC-001/003/005 exigen verificación objetiva; se extiende la suite
pytest existente).

## Format: `[ID] [P?] [Story] Description`

- **[P]** paralelizable · **[Story]** US1/US2/US3 · **[C:...]**/**[M:cli/modelo]** etiquetas multi-CLI

## Path Conventions

Script en `.specify/scripts/python/scan_models.py`; catálogo `.specify/clis-catalog.json`;
skill `.claude/skills/speckit-models/SKILL.md`; espejos shippeables en
`src/specify_cli/gen_multicli/assets/`; tests en `tests/python/`.

---

## Phase 1: Setup (esquema del catálogo — BLOQUEA el resto)

- [X] T001 [C:media] [M:codex/gpt-5.6-sol] Extender `.specify/clis-catalog.json`: campos aditivos `modelos_cmd`, `modelos_cmd_consume`, `config_hints` (por SO) y `fuentes_oficiales` para los 3 CLIs conocidos (confirmando las rutas reales de config de kimi/codex/claude en esta máquina; parseo tolerante si no existen)

## Phase 2: User Story 1 — Detección local real (Priority: P1) 🎯 MVP

**Goal**: el escaneo extrae modelos reales (y esfuerzos) por CLI, con `origen`.

**Independent Test**: correr el escaneo y comparar contra lo que cada CLI declara localmente.

- [X] T002 [US1] [C:alta] [M:claude/fable] Implementar `detect_models(cli)` en `.specify/scripts/python/scan_models.py`: cadena `modelos_cmd` (si no consume o aprobado) → `config_hints` (TOML/JSON tolerante, `tomllib`) → semillas; salida con `origen` y `esfuerzos`; lo detectado pisa la semilla del mismo `id`; modelo retirado NO se borra (conserva origen previo — CHK017)
- [X] T003 [US1] [C:media] [M:codex/gpt-5.6-sol] Integrar `detect_models` en `build_inventory`/`scan_models` + flag `--probe-models` (opt-in para mecanismos que consumen) — contracts/model-discovery.md
- [X] T004 [P] [US1] [C:media] [M:kimi/k3] pytest `tests/python/test_model_discovery.py`: cadena de detección con configs mock (TOML/JSON), origen correcto, tolerancia a config corrupta/ausente, detectado pisa semilla, retirado se conserva
- [X] T005 [P] [US1] [C:baja] [M:kimi/kimi-for-coding] pytest: `origen`/`esfuerzos` presentes en el inventario resultante y contrato previo intacto (extender `tests/python/test_scan_models.py`)

## Phase 3: User Story 2 — Verificación oficial (Priority: P2)

**Goal**: la skill cruza fuentes oficiales (agente, best-effort) y registra estados.

- [X] T006 [US2] [C:media] [M:claude/sonnet] Actualizar `.claude/skills/speckit-models/SKILL.md`: paso de verificación oficial por el agente (consultar `fuentes_oficiales`, proponer altas `oficial-sin-confirmar` con capacidad/costo sugeridos corregibles, registrar `verificacion_web` hecha/omitida) y presentación de la tabla con origen/esfuerzos
- [X] T007 [US2] [C:media] [M:codex/gpt-5.6-terra] Soporte en `scan_models.py` para persistir `verificacion_web` por CLI (estado/fecha/fuentes) vía el merge (aplicable por la skill) + pytest del campo

## Phase 4: User Story 3 — Esfuerzos y merge (Priority: P3)

- [X] T008 [US3] [C:media] [M:kimi/k3] pytest: edición manual de `esfuerzos`/`origen` sobrevive re-escaneo (merge_preserving_user_edits sobre campos nuevos) — SC-003

## Phase 5: Polish & Cross-Cutting

- [X] T009 [C:media] [M:codex/gpt-5.5] Sincronizar espejos shippeables: `assets/clis-catalog.json`, `assets/scripts-python/scan_models.py`, `assets/skills-multicli/speckit-models/SKILL.md` (copiar desde las versiones dev)
- [X] T010 [P] [C:baja] [M:claude/haiku] Documentar los campos nuevos del contrato en `specs/006-model-discovery/contracts/model-discovery.md` si implement ajustó algo, y nota breve en README solo si cambia el uso (probablemente no)
- [X] T011 [C:alta] [M:claude/fable] Validación E2E: correr el escaneo real en esta máquina + los escenarios del quickstart (E1, E2, E4, E5); suite pytest completa verde

---

## Dependencies

- T001 → todo lo demás (esquema del catálogo primero).
- US1: T002 → T003; T004/T005 tras T003. US2 (T006, T007) tras US1. US3 (T008) tras T003.
- Polish: T009 tras US1+US2; T011 al final.

## Parallel Execution Examples

- T004 + T005 en paralelo tras T003. T006 (skill) y T007 (script) en paralelo. T010 con T009.

## Implementation Strategy

- **MVP = US1** (T001–T005): detección local real con origen/esfuerzos.
- **Incremento 2 = US2** (T006–T007): verificación oficial por el agente.
- **Incremento 3 = US3 + Polish** (T008–T011): merge, espejos, E2E.

## Total: 11 tareas — US1: 4 · US2: 2 · US3: 1 · Setup: 1 · Polish: 3
