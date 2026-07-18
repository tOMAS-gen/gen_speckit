---
description: "Task list for feature 004-specify-cli-fork"
---

# Tasks: Fork de specify-cli con mejoras multi-CLI integradas

**Input**: Design documents from `/specs/004-specify-cli-fork/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Se incluyen tareas de validación (pytest del wiring del `init` + escenarios del
quickstart) porque los SC-002/003/004/005 exigen verificación objetiva. La suite Pester de
los scripts ya existe y se preserva.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede correr en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: US1/US2/US3 (mapea a las historias del spec)
- **[C:baja|media|alta]** y **[M:cli/modelo]**: etiquetas multi-CLI aditivas (asignador)

## Path Conventions

Estructura destino del fork (ver plan.md §Project Structure): raíz con `pyproject.toml` +
`src/specify_cli/` vendorizado; capa propia en `src/specify_cli/gen_multicli/` y assets del
producto; tests en `tests/python/` (nuevo) y `tests/powershell/` (existente).

---

## Phase 1: Setup (esqueleto del fork)

**Purpose**: convertir el repo en el paquete instalable del fork.

- [X] T001 [C:media] [M:codex/gpt-5.5] Crear `pyproject.toml` en la raíz (paquete `specify-cli`, entry-point `specify` → `specify_cli:main`, backend hatchling, deps de upstream, Python ≥3.11)
- [X] T002 [P] [C:baja] [M:claude/haiku] Crear `UPSTREAM.md` con la versión/tag pineada del upstream elegido y el esqueleto del procedimiento de sync
- [X] T003 [C:alta] [M:claude/fable] Vendorizar el source de `github/spec-kit` (tag pineado) en `src/specify_cli/`, preservando `integrations/`, `bundler/`, `presets/`, `commands/init.py`
- [X] T004 [P] [C:baja] [M:kimi/kimi-for-coding] Crear scaffold de `tests/python/` con configuración de pytest
- [X] T005 [P] [C:media] [M:kimi/k3] Copiar los assets del producto a `src/specify_cli/gen_multicli/assets/` (skills-multicli/ con las 8 skills, orchestrator/, scripts-powershell/ con los 6 scripts, clis-catalog.json) desde el repo actual

**Checkpoint**: el repo instala como paquete Python (`uv tool install` desde el clon) y
`specify --help` responde.

---

## Phase 2: Foundational (bundling — BLOQUEA todas las historias)

**Purpose**: cablear el producto dentro del wheel y el punto de enganche del `init`.

- [X] T006 [C:alta] [M:claude/fable] Leer y documentar el mapeo interno de `src/specify_cli/bundler/` (qué carpeta va a qué en el wheel); registrar el resultado en `UPSTREAM.md` (resuelve riesgo CHK027)
- [X] T007 [C:media] [M:codex/gpt-5.6-sol] Crear el paquete `src/specify_cli/gen_multicli/__init__.py` como seam de la capa propia (bundling/preset del producto)
- [X] T008 [C:alta] [M:claude/fable] Incluir los assets del producto en el empaquetado hatchling (`pyproject.toml` include) para que viajen dentro del wheel
- [X] T009 [P] [C:baja] [M:claude/haiku] Redirigir `src/specify_cli/_version.py` (`GITHUB_API_LATEST`, `_GITHUB_SOURCE_URL`) al fork `tOMAS-gen/gen_speckit`

**Checkpoint**: el wheel construido contiene los assets del producto; hay un módulo `gen_multicli` donde engancha el `init`.

---

## Phase 3: User Story 1 — Init de un solo paso (Priority: P1) 🎯 MVP

**Goal**: un único `specify init` deja base + producto completo, sin segundo instalador.

**Independent Test**: en carpeta vacía, `specify init . --integration claude --script ps`
y verificar base + los ítems del producto presentes (contracts/product-delivery.md).

- [X] T010 [US1] [C:alta] [M:claude/fable] Implementar el hook de entrega del producto en el flujo de `init` (`src/specify_cli/gen_multicli/`): tras el scaffolding base, depositar `orchestrator/` en `.specify/orchestrator/`
- [X] T011 [P] [US1] [C:media] [M:codex/gpt-5.6-terra] Depositar los 6 scripts en `.specify/scripts/powershell/` (`platform.ps1`, `scan-models.ps1`, `invoke-secondary.ps1`, `update-quota.ps1`, `get-parallel-groups.ps1`, `clis-config.ps1`)
- [X] T012 [P] [US1] [C:baja] [M:kimi/kimi-for-coding] Depositar `clis-catalog.json` en `.specify/clis-catalog.json`
- [X] T013 [US1] [C:alta] [M:claude/fable] Entregar las 8 skills para el agente de `--integration` (ruta por defecto), respetando el formato del agente (SkillsIntegration para claude/kimi; prompt sin frontmatter para codex)
- [X] T014 [US1] [C:media] [M:codex/gpt-5.6-sol] Implementar la contribución no destructiva a `AGENTS.md` (o `AGENTS.gen-speckit.md` si existe) y el append idempotente al `.gitignore` (3 exclusiones) — FR-005
- [X] T015 [P] [US1] [C:media] [M:kimi/k3] pytest: un solo `specify init` produce base + el 100% de los ítems del producto (SC-002) verificando contra `contracts/product-delivery.md`
- [X] T016 [P] [US1] [C:media] [M:codex/gpt-5.6-terra] pytest: los artefactos base de spec-kit quedan sin modificación (no regresión, SC-003)

**Checkpoint**: US1 entregable y testeable de forma independiente (MVP).

---

## Phase 4: User Story 2 — Elección de agente en el init (Priority: P2)

**Goal**: `--skills claude|codex|kimi|todos` decide a qué agente(s) van las 8 skills.

**Independent Test**: `specify init . --integration claude --skills todos` deja las 8
skills en `.claude/skills/`, `.codex/prompts/` y `.kimi/skills/`.

- [X] T017 [US2] [C:media] [M:codex/gpt-5.6-sol] Agregar la opción `--skills claude|codex|kimi|todos|<lista>` al comando `init` (default = valor de `--integration`) — contracts/init-command.md
- [X] T018 [US2] [C:media] [M:kimi/k3] Implementar el mapeo de entrega por agente (claude/kimi: `SKILL.md` literal; codex: cuerpo sin frontmatter prefijado con `# /<skill>`) reutilizando el mecanismo de integración de upstream
- [X] T019 [P] [US2] [C:media] [M:codex/gpt-5.6-terra] pytest: `--skills todos` entrega las 8 skills a los 3 agentes en formato/ubicación correctos

**Checkpoint**: US2 sumada sin romper US1 (default sigue igual).

---

## Phase 5: User Story 3 — Mantenibilidad contra upstream (Priority: P3)

**Goal**: incorporar updates del upstream sin rehacer la capa multi-CLI.

**Independent Test**: simular un cambio en un archivo base del upstream e incorporarlo
verificando que la capa multi-CLI queda intacta y el `init` sigue entregando ambos.

- [X] T020 [US3] [C:media] [M:codex/gpt-5.5] Finalizar el procedimiento de sync en `UPSTREAM.md` y listar el diff mínimo sobre upstream (idealmente solo `_version.py` + el seam del preset)
- [X] T021 [US3] [C:media] [M:claude/sonnet] Aislar todos los cambios de gen fuera de los archivos de upstream (verificar que la separación producto/upstream se sostiene) — FR-007
- [X] T022 [P] [US3] [C:baja] [M:kimi/kimi-for-coding-highspeed] Documentar/simular un "sync dry-run": cambio en un archivo base del upstream sin romper la capa del producto

**Checkpoint**: US3 sumada; el fork es mantenible.

---

## Phase 6: Polish & Cross-Cutting

- [X] T023 [P] [C:media] [M:claude/sonnet] Actualizar `README.md`: gesto de instalación de un solo paso; quitar/ajustar las instrucciones del flujo de dos pasos (FR-010) — usar `/speckit-readme`
- [X] T024 [P] [C:baja] [M:claude/haiku] Deprecar `install.ps1`: aviso de deprecación apuntando a `specify init`; quitarlo como camino recomendado de la documentación (FR-009)
- [X] T025 [P] [C:baja] [M:kimi/kimi-for-coding] Revisar/actualizar los punteros de portabilidad en `AGENTS.md`
- [X] T026 [C:alta] [M:claude/fable] CI: correr la validación del `init` (base + producto) en Windows/Linux/macOS (SC-005) según quickstart
- [X] T027 [P] [C:media] [M:codex/gpt-5.6-terra] Ejecutar los 7 escenarios del `quickstart.md` y registrar resultados
- [X] T028 [P] [C:baja] [M:claude/haiku] Actualizar la nota de sync de `.specify/memory/constitution.md` (ningún template afectado; amendment de la restricción técnica "Python CLI base" diferido a `/speckit-constitution` — governance) si algún template quedó afectado

---

## Dependencies (orden de completado)

- **Setup (T001–T005)** → **Foundational (T006–T009)** → historias.
- **US1 (T010–T016)**: depende de Foundational. Es el MVP; entregable solo.
- **US2 (T017–T019)**: depende de US1 (extiende la entrega de skills). 
- **US3 (T020–T022)**: depende de Setup/Foundational (estructura del fork); independiente de US2.
- **Polish (T023–T028)**: después de las historias que audita (T026/T027 tras US1/US2).

Dentro de una historia, las tareas `[P]` (archivos distintos) corren en paralelo; las que
tocan `init`/mecanismo compartido son secuenciales.

## Parallel Execution Examples

- **Setup**: T002, T004, T005 en paralelo (archivos distintos) mientras T001→T003 van en serie.
- **US1**: T011, T012 en paralelo; T015, T016 (tests) en paralelo una vez lista la entrega.
- **Polish**: T023, T024, T025, T027, T028 en paralelo.

## Implementation Strategy

- **MVP = US1** (T001–T016): fork instalable + `init` de un solo paso con producto completo
  para el agente por defecto. Ya entrega el valor central (SC-001/002/003).
- **Incremento 2 = US2**: elección de agente (paridad con `-Skills`).
- **Incremento 3 = US3 + Polish**: mantenibilidad, docs, deprecación de install.ps1, CI
  multiplataforma.

## Total: 28 tareas — US1: 7 · US2: 3 · US3: 3 · Setup: 5 · Foundational: 4 · Polish: 6
