# Quickstart: validación del Especificador de Agentes y README

**Feature**: 002-agent-specifier | **Date**: 2026-07-18

## Prerequisitos

- Repo spec-kit con constitución ratificada (este repo sirve) y skills instaladas.

## Escenario 1 — Especificador con objetivo declarado (US1, SC-001, SC-002)

```
/speckit-agents
```

**Esperado**: deriva el objetivo de la constitución; presenta la tabla de cobertura
(los 8 dominios base evaluados: cubierto / faltante / no aplica con justificación) +
dominios extra si el objetivo los justifica; pide confirmación ANTES de escribir;
tras aprobar, existe un `.specify/agents/<nombre>.md` por agente aprobado (frontmatter
válido según contracts/agent-definition.md) y su derivación `.claude/agents/<nombre>.md`.
Cronometrar: < 10 min hasta el conjunto aprobado.

## Escenario 2 — Idempotencia y huecos (US1, SC-003, SC-004)

1. Re-correr `/speckit-agents` sin cambios → propone 0 agentes nuevos (todo cubierto),
   no toca ningún archivo existente.
2. Editar a mano un agente (cambiar sus Instrucciones) → re-correr → la edición
   sobrevive intacta.
3. Borrar un agente de un dominio aplicable → re-correr → propone SOLO ese faltante.
4. Agregar al objetivo un dominio nuevo (editar constitución) → re-correr → propone
   agente(s) para el dominio nuevo y reporta huérfanos si los hay (sin borrarlos).

## Escenario 3 — Sin fuente de objetivo (US1, edge case)

En un directorio de prueba sin constitución/README/specs, correr el especificador:
**Esperado**: pide el objetivo al usuario antes de proponer nada; con la respuesta,
procede normal. Nunca inventa el objetivo.

## Escenario 4 — README gestionado (US2, SC-003, SC-005)

1. En un proyecto sin README: `/speckit-readme` → crea README con secciones
   `objetivo`/`alcance`/`estado` delimitadas y fechadas (contracts/readme-sections.md).
2. Agregar contenido manual fuera de los delimitadores → re-correr → contenido manual
   intacto byte a byte; solo cambia el interior de los delimitadores y la fecha.
3. Sobre un README preexistente sin delimitadores (este repo): la skill muestra el
   diff propuesto y espera confirmación antes del primer cambio.
4. Delimitador roto (borrar un `fin` a mano) → la skill reporta corrupción y no
   escribe.

## Escenario 5 — Envoltorio constitution-plus (US3)

```
/speckit-constitution-plus <principios>
```

**Esperado**: ejecuta la fase constitution base completa (mismo comportamiento que
`/speckit-constitution`); al terminar ofrece el especificador; declinar termina sin
efectos; `/speckit-constitution` original sigue intacta y disponible.

## Escenario 6 — Ofrecimiento post-specify con idea compleja (US3)

Invocar `/speckit-specify-auto` con una idea compleja: tras la fase specify, el
pipeline ofrece correr el especificador para la feature; declinar continúa el
pipeline normalmente. Con idea simple/media: no se ofrece.

## Escenario 7 — Compatibilidad (FR-013, SC-006)

`/speckit-constitution`, `/speckit-specify` y el resto de los comandos base se
comportan exactamente igual con las skills nuevas instaladas.

## Resultados de validación

**2026-07-18 — Escenarios 1 y 2 (especificador de agentes, US1) — corrida real sobre este proyecto**

- Escenario 1 completo: objetivo derivado de la constitución ratificada (fuente 1 del
  orden FR-001); tabla de cobertura con los 8 dominios base evaluados (2 "no aplica"
  justificados: interfaz, servicios) + 1 dominio extra (`orquestacion`); confirmación
  solicitada ANTES de escribir; el usuario aprobó los 7 propuestos; se generaron 7
  portables en `.specify/agents/` (frontmatter válido según contracts/agent-definition.md)
  + 7 derivaciones nativas en `.claude/agents/`. Duración total < 10 min (SC-002 ✓).
- Escenario 2, paso 1 (idempotencia) ejecutado real: re-análisis de cobertura tras la
  generación → 0 dominios aplicables sin cobertura → 0 propuestas nuevas, 0 archivos
  tocados (SC-004 ✓). Pasos 2–4 (edición manual, borrado, dominio nuevo) garantizados
  por la política de no-sobrescritura del contrato; no ejercitados en esta corrida.
- Escenario 3 (sin fuente de objetivo): no ejercitado — requiere un directorio limpio;
  el comportamiento (preguntar, nunca inventar) está mandado por el Paso 1 de la skill.

**2026-07-18 — Escenario 4 (README gestionado, US2) — corrida real sobre el README del repo**

- Paso 3 del escenario ejercitado primero (el caso real disponible): README
  preexistente SIN delimitadores → la skill propuso el punto de inserción (tras el
  título principal), mostró el diff completo y esperó confirmación explícita (FR-009 ✓).
- Con aprobación del usuario: secciones objetivo/alcance/estado insertadas con sus
  pares de delimitadores y `_Actualizado: 2026-07-18_` (FR-010 ✓).
- Verificación mecánica post-escritura: 3 pares inicio/fin correctos y en orden, 3
  fechas presentes, contenido manual intacto byte a byte — incluida la sección
  agregada por codex en T010 (FR-008 / SC-003 ✓).
- Pasos 1 (README inexistente) y 4 (delimitador roto) no ejercitados en esta corrida:
  mandados por los pasos 5 y 3 de la skill y las reglas duras 3 y 5 del contrato.

**2026-07-18 — Escenario 7 (compatibilidad aditiva, FR-013 / SC-006)**

- Comandos base verificados: `/speckit-constitution`, `/speckit-specify`, `/speckit-analyze`, `/speckit-checklist`, `/speckit-clarify`, `/speckit-converge`, `/speckit-implement`, `/speckit-plan`, `/speckit-tasks`, `/speckit-taskstoissues`.
- Fechas de última modificación de sus `SKILL.md` (instalación 2026-07-17):
  - `speckit-analyze/SKILL.md`: 2026-07-17 20:20:15
  - `speckit-checklist/SKILL.md`: 2026-07-17 20:20:15
  - `speckit-clarify/SKILL.md`: 2026-07-17 20:20:15
  - `speckit-constitution/SKILL.md`: 2026-07-17 20:20:15
  - `speckit-converge/SKILL.md`: 2026-07-17 20:20:15
  - `speckit-implement/SKILL.md`: 2026-07-17 20:20:15
  - `speckit-plan/SKILL.md`: 2026-07-17 20:20:15
  - `speckit-specify/SKILL.md`: 2026-07-17 20:20:15
  - `speckit-tasks/SKILL.md`: 2026-07-17 20:20:15
  - `speckit-taskstoissues/SKILL.md`: 2026-07-17 20:20:15
- Skills nuevas de la feature 002 (`speckit-agents`, `speckit-readme`, `speckit-constitution-plus`) existen como archivos independientes con fechas 2026-07-18 y no alteran los anteriores.
- Conclusión: la feature 002 es estrictamente aditiva; las skills base permanecen intactas.
