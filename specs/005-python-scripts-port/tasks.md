---
description: "Task list for feature 005-python-scripts-port"
---

# Tasks: Scripts de soporte del orquestador en Python (multiplataforma)

**Input**: Design documents from `/specs/005-python-scripts-port/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Se incluyen tareas de tests (pytest de paridad por script) porque SC-002/003 lo
exigen. Los Pester heredados se conservan durante la transición.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: paralelizable (archivos distintos) · **[Story]**: US1/US2/US3
- **[C:...]** / **[M:cli/modelo]**: etiquetas multi-CLI (asignador)

## Path Conventions

Scripts nuevos en `.specify/scripts/python/`; bundling en
`src/specify_cli/gen_multicli/assets/scripts-python/`; tests en `tests/python/`.

---

## Phase 1: Setup

- [X] T001 [C:baja] [M:claude/haiku] Crear el directorio `.specify/scripts/python/` (con `__init__.py` si hace falta para imports de tests) y `tests/python/` ya existe

## Phase 2: Foundational (BLOQUEA los demás scripts)

- [X] T002 [C:media] [M:codex/gpt-5.6-sol] Portar `platform.ps1` → `.specify/scripts/python/platform.py` (os family, expand path portable, resolve executable con exe_hints, run_process con timeout, write utf-8 sin BOM) — helper importado por los otros scripts

## Phase 3: User Stories 1+2 — Port de los 6 scripts con paridad (Priority: P1)

**Goal**: los scripts corren sin pwsh (US1) y preservan contratos/comportamiento (US2).

**Independent Test**: correr cada script en un entorno sin PowerShell y comparar su salida
contra el contrato vigente.

- [X] T003 [P] [US2] [C:media] [M:kimi/k3] Portar `get-parallel-groups.ps1` → `get_parallel_groups.py` (parseo de `tasks.md`, etiquetas `[P]`/`[C:]`/`[M:]`, agrupamiento por conflicto de rutas, JSON idéntico) en `.specify/scripts/python/`
- [X] T004 [P] [US2] [C:baja] [M:kimi/kimi-for-coding] pytest de paridad para `get_parallel_groups.py` en `tests/python/test_get_parallel_groups.py` (campos y agrupamiento equivalentes)
- [X] T005 [P] [US2] [C:baja] [M:codex/gpt-5.6-luna] Portar `update-quota.ps1` → `update_quota.py` (set de `cuota` + `cuota_reset` según plan) en `.specify/scripts/python/`
- [X] T006 [P] [US2] [C:baja] [M:claude/haiku] pytest para `update_quota.py` en `tests/python/test_update_quota.py`
- [X] T007 [US1] [C:alta] [M:claude/fable] Portar `invoke-secondary.ps1` → `invoke_secondary.py` (comando desde plantilla headless, sanitizado del prompt, resolución de ejecutable, timeout 900s, 1 retry, clasificación `exito`/`cuota_agotada`/`indisponible`; preservar garantías de seguridad FR-006) usando `platform.py`
- [X] T008 [US2] [C:media] [M:codex/gpt-5.6-terra] pytest para `invoke_secondary.py` en `tests/python/test_invoke_secondary.py` (clasificación, timeout/retry, no filtra credenciales)
- [X] T009 [US1] [C:alta] [M:claude/fable] Portar `scan-models.ps1` → `scan_models.py` (detección de CLIs/versión/auth/headless/modelos, catálogo, armado de `models.json` + ranking; respeta corrección manual) en `.specify/scripts/python/`
- [X] T010 [US2] [C:media] [M:kimi/k3] pytest para `scan_models.py` en `tests/python/test_scan_models.py` (detección mockeada, formato de `models.json`)
- [X] T011 [US1] [C:alta] [M:claude/fable] Portar `clis-config.ps1` → `clis_config.py` (CRUD `agregar/editar/eliminar/verificar` sobre `models.json`/catálogo, con validaciones) en `.specify/scripts/python/`
- [X] T012 [US2] [C:media] [M:codex/gpt-5.6-terra] pytest para `clis_config.py` en `tests/python/test_clis_config.py` (validaciones y formato)

## Phase 4: User Story 3 — Reconectar invocadores y bundling (Priority: P2)

**Goal**: playbooks, skills y el producto instalado usan la vía Python.

- [X] T013 [US3] [C:media] [M:codex/gpt-5.6-sol] Reconectar los playbooks `assets/orchestrator/{orchestrate,assign,triage}.md` para invocar `python .specify/scripts/python/*.py` (en vez de `.ps1`)
- [X] T014 [US3] [C:media] [M:claude/sonnet] Reconectar las skills `speckit-models`, `speckit-orchestrate`, `speckit-clis` (sus referencias a scripts → versión Python)
- [X] T015 [US3] [C:media] [M:kimi/k3] Bundlear los 6 scripts en `src/specify_cli/gen_multicli/assets/scripts-python/` y actualizar `gen_multicli/_scripts.py` para depositar `.specify/scripts/python/` (conservando `powershell/` en transición, FR-008)
- [X] T016 [US3] [C:media] [M:codex/gpt-5.6-terra] pytest: `install_product` deposita los scripts Python en `.specify/scripts/python/` (actualizar `tests/python/test_product_delivery.py`)

## Phase 5: Polish & Cross-Cutting

- [X] T017 [C:alta] [M:claude/fable] Verificar no-regresión en Windows (SC-005): correr la suite pytest + un despacho real y confirmar comportamiento correcto
- [X] T018 [P] [C:baja] [M:claude/haiku] Actualizar README/Requisitos: el orquestador corre con solo Python; PowerShell pasa a opcional/heredado (FR-002)
- [X] T019 [C:media] [M:codex/gpt-5.5] Actualizar `.github/workflows/gen-validate.yml` para correr los pytest de los scripts en ubuntu/windows/macos (SC-005)
- [X] T020 [P] [C:baja] [M:kimi/kimi-for-coding] Marcar en la doc (README/UPSTREAM) los scripts `.specify/scripts/powershell/` como heredados/transición

---

## Dependencies

- Setup (T001) → Foundational (T002) → scripts. `platform.py` (T002) bloquea T007/T009 (lo importan).
- Cada port `[P]` con su test corren tras T002; T003/T005 son independientes entre sí.
- US3 (T013–T016) tras tener los scripts Python. Polish (T017–T020) al final.

## Parallel Execution Examples
- T003+T004, T005+T006 en paralelo (archivos distintos) tras T002.
- T013, T014 en paralelo (playbooks vs skills). T018, T020 en paralelo.

## Implementation Strategy
- **MVP = US1+US2** (T001–T012): los 6 scripts en Python con paridad → ya corre sin pwsh.
- **Incremento = US3** (T013–T016): reconexión + bundling → el producto instalado usa Python.
- **Polish** (T017–T020): no-regresión Windows, docs, CI.

## Total: 20 tareas — Setup:1 · Foundational:1 · US1+US2:10 · US3:4 · Polish:4
