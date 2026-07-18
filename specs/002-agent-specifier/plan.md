# Implementation Plan: Especificador de Agentes y README del Proyecto

**Branch**: `002-agent-specifier` | **Date**: 2026-07-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-agent-specifier/spec.md`

## Summary

Tres skills nuevas, estrictamente aditivas: (1) `speckit-agents` — analiza el objetivo
del proyecto contra una taxonomía base de dominios, propone los agentes necesarios y,
con confirmación, genera definiciones portables en `.specify/agents/<nombre>.md` más
la versión nativa del CLI; (2) `speckit-readme` — crea/actualiza el `README.md` con
secciones gestionadas delimitadas (objetivo, alcance, estado, fecha) preservando el
contenido manual; (3) `speckit-constitution-plus` — envoltorio que corre la fase
constitution base y al terminar ofrece el especificador. Los pipelines auto ofrecen el
especificador tras specify cuando el triage clasificó la idea compleja.

## Technical Context

**Language/Version**: Markdown (skills — el "código" que ejecutan los LLM); sin scripts nuevos de PowerShell (las operaciones son lectura/escritura de archivos que cualquier CLI hace nativamente)

**Primary Dependencies**: spec-kit 0.13.1 (skills base intactas); infraestructura ya existente de este repo: `AGENTS.md` (portabilidad), pipelines `speckit-specify-auto(-eco)`, triage multi-CLI (clasificación compleja)

**Storage**: Archivos en el repo — `.specify/agents/<nombre>.md` (definiciones portables), `.claude/agents/<nombre>.md` (derivación nativa Claude), `README.md` (secciones gestionadas delimitadas con comentarios HTML)

**Testing**: Escenarios de validación end-to-end en quickstart.md (conducta de skills; no hay scripts que testear con Pester)

**Target Platform**: Windows 11 + PowerShell (v1); skills legibles por los tres CLIs

**Project Type**: Extensión de tooling — 3 skills + 2 contratos de formato; sin src/

**Performance Goals**: SC-002: conjunto de agentes aprobado en < 10 min; sin metas de runtime clásicas

**Constraints**: Aditividad estricta (Constitución I — la skill base constitution NO se toca; envoltorio por Clarificación S1); portabilidad (Constitución II — lógica en Markdown neutral, `AGENTS.md` actualizado); confirmación previa a toda escritura (FR-003, gates reales — Constitución VI)

**Scale/Scope**: 3 skills nuevas, 2 contratos, ~8 dominios base de taxonomía, 1 edición menor a cada pipeline auto (ofrecimiento post-specify)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento del diseño | Estado |
|---|---|---|
| I. Compatibilidad Aditiva | Solo skills nuevas + archivos nuevos; `speckit-constitution` base intacta (envoltorio `constitution-plus` por Clarificación S1); README solo toca secciones delimitadas propias | ✅ PASS |
| II. Portabilidad Multi-CLI | Skills en Markdown neutral; definiciones portables en `.specify/agents/`; derivación nativa opcional por CLI; `AGENTS.md` gana punteros a las skills nuevas | ✅ PASS |
| III. El Más Barato que Alcance | Sin impacto directo (la asignación por tarea la hace el asignador en la fase tasks); el análisis de cobertura es corto y de única vez | ✅ PASS |
| IV. Nunca Discriminar | N/a (esta feature no reparte trabajo entre modelos) | ✅ PASS |
| V. Decisiones Caras al Más Capaz | El análisis de cobertura (decisión estructural del proyecto) se ejecuta con el modelo más capaz disponible — la skill lo exige, igual que triage/assign | ✅ PASS |
| VI. Mínima Intervención, Gates Reales | Confirmación ANTES de escribir agentes (gate real); ofrecimientos opcionales no bloqueantes; declinar no tiene efectos | ✅ PASS |

**Re-check post-Phase 1**: sin cambios — el diseño de datos y contratos no introdujo violaciones. ✅ PASS

## Project Structure

### Documentation (this feature)

```text
specs/002-agent-specifier/
├── plan.md              # Este archivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── agent-definition.md   # Formato de .specify/agents/<nombre>.md y derivación nativa
│   └── readme-sections.md    # Delimitadores y secciones gestionadas del README
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
.claude/skills/
├── speckit-agents/
│   └── SKILL.md                 # NUEVA: especificador (análisis → propuesta → confirmación → generación)
├── speckit-readme/
│   └── SKILL.md                 # NUEVA: README gestionado (crear/actualizar secciones delimitadas)
├── speckit-constitution-plus/
│   └── SKILL.md                 # NUEVA: envoltorio constitution base + ofrecimiento del especificador
├── speckit-specify-auto/
│   └── SKILL.md                 # EXISTENTE: + ofrecimiento post-specify si idea compleja (edición mínima)
└── speckit-specify-auto-eco/
    └── SKILL.md                 # EXISTENTE: ídem

.specify/
└── agents/                      # GENERADO por speckit-agents (definiciones portables, 1 archivo por agente)

.claude/agents/                  # GENERADO: derivación nativa Claude de los agentes aprobados

AGENTS.md                        # EXISTENTE: + punteros a las skills nuevas (portabilidad)
README.md                        # Gestionado parcialmente por speckit-readme (secciones delimitadas)
```

**Structure Decision**: misma arquitectura de la feature 001 — skills Markdown como
lógica ejecutable por LLM, sin scripts nuevos (las operaciones son de archivos y de
razonamiento, no de sistema). La portabilidad se resuelve con Markdown neutral +
punteros en `AGENTS.md`, igual que el orquestador multi-CLI.

## Complexity Tracking

Sin violaciones de la constitución que justificar.
