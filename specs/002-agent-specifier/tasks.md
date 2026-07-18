---

description: "Task list for feature implementation"
---

# Tasks: Especificador de Agentes y README del Proyecto

**Input**: Design documents from `/specs/002-agent-specifier/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Sin scripts nuevos → sin tests Pester; la validación es por escenarios de quickstart.md.

**Organization**: Tasks agrupadas por historia de usuario, independientemente testeables.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story a la que pertenece (US1, US2, US3)
- Etiquetas multi-CLI `[C:...]` `[M:...]`: agregadas por el asignador; editables a mano.

## Phase 1: Setup

- [x] T001 [C:baja] [M:claude/haiku] Crear directorio `.specify/agents/` con `.gitkeep`

*(Sin fase Foundational: los contratos ya existen como documentos de diseño y no hay prerequisitos bloqueantes.)*

---

## Phase 2: User Story 1 - Especificar los agentes que el proyecto necesita (Priority: P1) 🎯 MVP

**Goal**: `/speckit-agents` analiza el objetivo, propone cobertura por dominios y genera definiciones aprobadas

**Independent Test**: quickstart escenarios 1–3 (cobertura completa, idempotencia, sin fuente de objetivo)

- [x] T002 [US1] [C:alta] [M:claude/fable] Crear `.claude/skills/speckit-agents/SKILL.md`: derivación del objetivo (orden FR-001, nunca inventar), análisis de cobertura con taxonomía base + extras (FR-002, data-model §3), tabla de propuesta con confirmación total/parcial/rechazo (FR-003), generación portable en `.specify/agents/<nombre>.md` + derivación nativa `.claude/agents/` según `contracts/agent-definition.md` (FR-004), idempotencia sin sobrescribir existentes y detección por dominio (FR-005), reporte de huérfanos con sugerencia de archivo (FR-006), colisión de nombres → nombre alternativo (edge case), ejecución recomendada con el modelo más capaz disponible (Constitución V)
- [x] T003 [US1] [C:media] [M:kimi/kimi-for-coding] Validar los escenarios 1, 2 y 3 de `specs/002-agent-specifier/quickstart.md` (cobertura 8 dominios evaluados, idempotencia en 4 pasos, pedido de objetivo sin fuente) y documentar resultados en la sección "Resultados de validación" de `specs/002-agent-specifier/quickstart.md`

**Checkpoint**: US1 funcional — el proyecto puede especificar su equipo de agentes

---

## Phase 3: User Story 2 - README que preserva la idea del proyecto (Priority: P2)

**Goal**: `/speckit-readme` crea/actualiza secciones gestionadas delimitadas preservando lo manual

**Independent Test**: quickstart escenario 4 (creación, preservación byte a byte, README preexistente, delimitador roto)

- [x] T004 [P] [US2] [C:media] [M:kimi/kimi-for-coding] Crear `.claude/skills/speckit-readme/SKILL.md`: crear README con secciones objetivo/alcance/estado delimitadas y fechadas, actualizar solo interiores de delimitadores (FR-008, contrato `contracts/readme-sections.md`), README preexistente sin delimitadores → diff propuesto + confirmación (FR-009), delimitadores rotos → reportar sin escribir (regla 5), fuentes del contenido en orden FR-001
- [x] T005 [US2] [C:media] [M:kimi/kimi-for-coding] Validar el escenario 4 de `specs/002-agent-specifier/quickstart.md` (4 pasos, incluida la corrida sobre el README real del repo con confirmación) y documentar resultados en `specs/002-agent-specifier/quickstart.md`

**Checkpoint**: US1 y US2 independientes y funcionales

---

## Phase 4: User Story 3 - Integración con el flujo spec-kit (Priority: P3)

**Goal**: envoltorio `constitution-plus` + ofrecimiento post-specify en pipelines + portabilidad

**Independent Test**: quickstart escenarios 5–6 (envoltorio, ofrecimiento solo con idea compleja, declinar sin efectos)

- [x] T006 [P] [US3] [C:baja] [M:codex/gpt-5.6-luna] Crear `.claude/skills/speckit-constitution-plus/SKILL.md`: envoltorio fino que ejecuta la skill base `speckit-constitution` completa sin modificarla y al terminar ofrece correr el especificador de agentes (opcional, no bloqueante, declinar sin efectos — FR-012)
- [x] T007 [US3] [C:media] [M:kimi/kimi-for-coding] Agregar a `.claude/skills/speckit-specify-auto/SKILL.md` y `.claude/skills/speckit-specify-auto-eco/SKILL.md` el ofrecimiento post-specify del especificador cuando el triage clasificó la idea compleja (FR-012: análisis a nivel proyecto; declinar continúa el pipeline)
- [x] T008 [P] [US3] [C:baja] [M:claude/haiku] Actualizar `AGENTS.md` con los punteros a las tres skills nuevas (speckit-agents, speckit-readme, speckit-constitution-plus) para Codex/Kimi como principal (Constitución II)
- [ ] T009 [US3] [C:media] [M:kimi/kimi-for-coding] Validar los escenarios 5 y 6 de `specs/002-agent-specifier/quickstart.md` y documentar resultados en `specs/002-agent-specifier/quickstart.md`

**Checkpoint**: integración completa sin tocar skills base

---

## Phase 5: Polish & Cross-Cutting

- [x] T010 [P] [C:baja] [M:codex/gpt-5.6-luna] Actualizar `README.md` del repo: documentar los comandos nuevos (/speckit-agents, /speckit-readme, /speckit-constitution-plus) en la sección de mejoras
- [x] T011 [C:media] [M:kimi/kimi-for-coding] Auditoría de compatibilidad (escenario 7 del quickstart): verificar que las skills base de spec-kit no cambiaron (timestamps/diff) y documentar el resultado en `specs/002-agent-specifier/quickstart.md`

---

## Dependencies & Execution Order

- Setup (T001) → primero (crea el directorio que usa T002).
- US1: T002 → T003 (validación tras la skill).
- US2: T004 ∥ con US1 (archivo distinto); T005 tras T004.
- US3: T006 ∥ T008 ∥ (T004…); T007 tras T006 (el ofrecimiento referencia la skill creada); T009 tras T006+T007.
- Polish: T010 en cualquier momento tras US3 (documenta lo creado); T011 al final.
- T007 toca los mismos archivos que ediciones previas de pipelines: no paralelizar con otras tareas que editen esas skills.

## Parallel Opportunities

- T004, T006, T008, T010 son [P] entre sí (archivos distintos) respetando sus dependencias.

## Implementation Strategy

**MVP**: T001 + T002 + T003 (US1 sola ya entrega el valor central).
Luego US2 → US3 → Polish, validando el checkpoint de cada historia.

## Asignación multi-CLI

Etiquetas agregadas por el asignador (playbook `.specify/orchestrator/assign.md`) el
2026-07-18, ejecutado por `claude/fable` (primer candidato de `asignacion.alta`).
Reparto: kimi 6 tareas (media), claude 3 (1 alta + 2 baja), codex 2 (baja).
Justificación del reparto en `orchestration-report.md`. Editables a mano antes de
implementar; re-generar `tasks.md` pierde las etiquetas y exige re-asignar.
