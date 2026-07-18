# Implementation Plan: Orquestador Multi-CLI para Spec Kit

**Branch**: `001-multi-cli-orchestrator` | **Date**: 2026-07-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-multi-cli-orchestrator/spec.md`

## Summary

Extender spec-kit con un sistema multi-CLI que, a partir de una sola idea, hace triage
de complejidad, elige flujo (ECO/IDEAL) y modelo por fase, clasifica y asigna cada
tarea al modelo más económico que alcance, y orquesta la implementación despachando
tareas a CLIs secundarios en modo headless con fallback por cuota. Enfoque técnico:
skills de Markdown con lógica portable centralizada en `.specify/orchestrator/`,
scripts PowerShell para detección/despacho, y contratos de datos en archivos
(`models.json`, etiquetas en `tasks.md`, reporte por feature). Todo estrictamente
aditivo sobre spec-kit 0.13.x.

## Technical Context

**Language/Version**: Markdown (skills/playbooks — es el "código" que ejecutan los LLM) + PowerShell 5.1/7 (scripts de soporte) + JSON (contratos de datos)

**Primary Dependencies**: spec-kit 0.13.1 (estructura `.specify/`, skills base); CLIs externos: Claude Code (`claude`), Codex CLI (`codex`), Kimi CLI (`kimi`), cada uno con modo headless verificado (ver research.md R1)

**Storage**: Archivos en el repo — `.specify/models.json` (inventario/ranking), `tasks.md` (etiquetas inline), `specs/<feature>/orchestration-report.md` (reporte por feature)

**Testing**: Pester para los scripts PowerShell (detección, parseo de etiquetas, serialización de conflictos) + escenarios de validación end-to-end en quickstart.md (la conducta de skills/LLM no es testeable de forma determinista)

**Target Platform**: Windows 11 + PowerShell (v1); los tres CLIs instalados localmente

**Project Type**: Extensión de tooling — skills + playbooks + scripts sobre un repo spec-kit existente (no hay src/ de aplicación)

**Performance Goals**: No aplica rendimiento clásico de runtime; objetivos del dominio: preparación inicial < 10 min (SC-007), reducción ≥ 50% del consumo del modelo caro (SC-004), cero intervenciones en `-bypass` sin dudas (SC-001)

**Constraints**: Portabilidad total entre los 3 CLIs (ninguna feature exclusiva en la lógica core — Constitución II); compatibilidad aditiva estricta con spec-kit (Constitución I); invocaciones headless sin confirmaciones dentro del repo (Clarificación S2); única escritura automática sobre `models.json` es el campo `cuota` (Clarificación S3)

**Scale/Scope**: 3 CLIs, ~2–6 modelos por CLI, features de decenas de tareas; 3 skills nuevas + 1 extendida + 4 scripts PowerShell + 4 playbooks portables

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento del diseño | Estado |
|---|---|---|
| I. Compatibilidad Total con Spec Kit (Solo Aditiva) | Solo se agregan skills (`speckit-models`, `speckit-specify-auto-eco`, `speckit-orchestrate`), playbooks en `.specify/orchestrator/` y scripts nuevos. Ningún template ni skill base se modifica de forma incompatible; las etiquetas `[C:]`/`[M:]` son aditivas al formato oficial de `tasks.md`. | ✅ PASS |
| II. Portabilidad Multi-CLI | La lógica de triage/asignación/orquestación vive en playbooks Markdown neutrales (`.specify/orchestrator/`); las skills por CLI son adaptadores finos. El despacho usa el comando `headless` declarado en `models.json`, nunca APIs propias de un CLI. | ✅ PASS |
| III. El Más Barato que Alcance | El algoritmo de asignación (contracts/task-labels.md) recorre la lista `asignacion` del nivel de complejidad correspondiente y elige el primer candidato (ya ordenado por preferencia costo/capacidad) con contexto y cuota disponibles. | ✅ PASS |
| IV. Nunca Discriminar un Modelo | `models.json` incluye a todos los CLIs instalados en las listas `asignacion`; el fallback escala por la lista sin excluir; el asignador reparte trabajo a todos los niveles. | ✅ PASS |
| V. Decisiones Caras al Modelo Más Capaz | Triage y asignación se ejecutan con el primer candidato disponible de `asignacion.alta` (los playbooks lo exigen); la autoevaluación del punto de entrada está en el playbook de triage. | ✅ PASS |
| VI. Mínima Intervención, Gates Reales | Pipelines encadenan fases; gates solo en clarificaciones/hallazgos críticos/pre-implement; `-bypass` y `--sin-implementar` definidos; retomabilidad por detección de artefactos. | ✅ PASS |

**Re-check post-Phase 1**: sin cambios — el diseño de datos y contratos no introdujo violaciones. ✅ PASS

## Project Structure

### Documentation (this feature)

```text
specs/001-multi-cli-orchestrator/
├── plan.md              # Este archivo (salida de /speckit-plan)
├── research.md          # Salida de Phase 0 (/speckit-plan)
├── data-model.md        # Salida de Phase 1 (/speckit-plan)
├── quickstart.md        # Salida de Phase 1 (/speckit-plan)
├── contracts/           # Salida de Phase 1 (/speckit-plan)
│   ├── models-schema.md
│   ├── headless-adapters.md
│   └── task-labels.md
└── tasks.md             # Salida de Phase 2 (/speckit-tasks — NO la crea /speckit-plan)
```

### Source Code (repository root)

```text
.claude/skills/                        # Adaptadores para Claude Code (principal por defecto)
├── speckit-models/
│   └── SKILL.md                       # NUEVA: inventario de CLIs/modelos → models.json
├── speckit-specify-auto/
│   └── SKILL.md                       # EXISTENTE: se extiende con triage (pre-fase) y asignador (post-tasks)
├── speckit-specify-auto-eco/
│   └── SKILL.md                       # NUEVA: pipeline ECO (specify → plan → tasks → gate → implement)
└── speckit-orchestrate/
    └── SKILL.md                       # NUEVA: fase implement orquestada multi-CLI

.specify/
├── orchestrator/                      # Lógica portable, neutral respecto del CLI (Constitución II)
│   ├── triage.md                      # Playbook: clasificar idea, elegir flujo y modelos por fase
│   ├── assign.md                      # Playbook: clasificar tareas [C:] y asignar [M:]
│   ├── orchestrate.md                 # Playbook: despacho, paralelo, fallback, verificación, [X]
│   └── report-template.md             # Plantilla del reporte de orquestación
├── scripts/powershell/
│   ├── scan-models.ps1                # NUEVO: detección de CLIs/modelos/headless → models.json
│   ├── invoke-secondary.ps1           # NUEVO: invocación headless con reintento(1) y captura de salida
│   ├── update-quota.ps1               # NUEVO: única escritura automática sobre models.json (campo cuota)
│   └── get-parallel-groups.ps1        # NUEVO: agrupa tareas [P] serializando conflictos de archivo
├── models.json                        # GENERADO por /speckit-models (valores del usuario prevalecen)
└── (memory/, templates/, scripts existentes: sin cambios)

tests/
└── powershell/                        # Pester: tests de los scripts nuevos
    ├── scan-models.Tests.ps1
    ├── invoke-secondary.Tests.ps1
    ├── update-quota.Tests.ps1
    └── get-parallel-groups.Tests.ps1
```

**Structure Decision**: extensión de tooling sobre el repo spec-kit existente. No hay
`src/` de aplicación: el "código" son skills Markdown (adaptadores por CLI) + playbooks
portables en `.specify/orchestrator/` + scripts PowerShell testeables con Pester. Los
adaptadores nativos para Codex/Kimi como principal reutilizan los mismos playbooks y
se crean en US6 (tarea T033: `.codex/prompts/` o `AGENTS.md`, y el equivalente de
Kimi), como adaptadores finos sin lógica duplicada.

## Complexity Tracking

Sin violaciones de la constitución que justificar.
