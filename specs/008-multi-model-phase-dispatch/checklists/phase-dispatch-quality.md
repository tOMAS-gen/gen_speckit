# Checklist: Calidad de Requisitos — Despacho multi-modelo de todas las fases

**Purpose**: validar completitud, claridad y consistencia de los requisitos antes de tasks/implement
**Created**: 2026-07-22
**Feature**: [spec.md](../spec.md)

## Despacho de fases (US1)

- [x] CHK001 - ¿Está especificado exactamente qué fases son despachables y cuáles quedan siempre en el principal? [Completeness, Spec §FR-001, §FR-005]
- [x] CHK002 - ¿Está definido el criterio de verificación de un artefacto de fase de forma objetiva (qué lo hace válido/inválido)? [Measurability, Spec §FR-002]
- [x] CHK003 - ¿El ciclo de recuperación ante fallo tiene límites explícitos de reintentos y un final garantizado? [Clarity, Spec §FR-003]
- [x] CHK004 - ¿Está definido el comportamiento cuando el modelo asignado a la fase es el propio principal? [Coverage, Spec Edge Cases]
- [x] CHK005 - ¿Está definido el flujo completo para fases con interacción (quién genera preguntas, quién conversa, quién integra)? [Completeness, Spec §FR-005, §FR-005a]
- [x] CHK006 - ¿Se especifica qué fases exigen modelo de alta capacidad y por qué? [Clarity, Spec §FR-005a]
- [x] CHK007 - ¿Está definido el comportamiento ante cuota agotada durante una fase, sin intervención del usuario? [Coverage, Spec §FR-004, SC-006]
- [x] CHK008 - ¿Se define cuándo se activa el despacho de fases y cuál es el fallback sin inventario? [Completeness, Spec §FR-013]

## Inventario multi-modelo y configuración del usuario (US2)

- [x] CHK009 - ¿Está especificado cómo se registra un agente multi-modelo y qué pasa con agentes sin selección de modelo? [Completeness, Spec §FR-006, §FR-008]
- [x] CHK010 - ¿Se define qué es detectable automáticamente vs. qué requiere declaración del usuario? [Clarity, Spec §FR-007]
- [x] CHK011 - ¿Las dos vías de configuración (manual + skill) tienen precedencia definida sin conflicto? [Consistency, Spec §FR-008a]
- [x] CHK012 - ¿Está definido el efecto de deshabilitar un modelo sobre rankings, fallbacks y tareas ya etiquetadas con ese modelo? [Coverage, Spec §FR-008a]
- [x] CHK013 - ¿El modo "agente preferido" define comportamiento cuando el agente preferido queda sin candidatos? [Edge Case, Spec §FR-008b, Edge Cases]
- [x] CHK014 - ¿La restricción del usuario (deshabilitados/preferido) es distinguible en el reporte de una exclusión del sistema (Constitución IV)? [Consistency, Spec §FR-008b]

## Transparencia y métricas (US3)

- [x] CHK015 - ¿Se distingue en los requisitos el modelo asignado del modelo efectivo por fase? [Clarity, Spec §FR-010]
- [x] CHK016 - ¿Las métricas de ahorro están definidas de forma calculable (qué se cuenta y sobre qué total)? [Measurability, Spec §FR-010, SC-004]

## Consistencia transversal

- [x] CHK017 - ¿Los requisitos de despacho de fases reutilizan explícitamente el mecanismo existente sin crear un canal paralelo? [Consistency, Spec §FR-009]
- [x] CHK018 - ¿Las reglas duras existentes (no auto-invocación, solo el principal escribe estado, secundarios dentro del repo) están preservadas? [Consistency, Spec §FR-011]
- [x] CHK019 - ¿La retomabilidad define qué estado se relee y qué se re-ejecuta tras una interrupción? [Completeness, Spec §FR-012, SC-005]
- [x] CHK020 - ¿Los criterios de éxito son verificables sin conocer la implementación? [Measurability, Spec §SC-001..SC-006]
- [x] CHK021 - ¿El alcance excluido (registrar OpenCode/Hermes concretos) está declarado sin ambigüedad? [Clarity, Spec Assumptions, Clarifications Q3]
- [x] CHK022 - ¿Está definido el límite de instrucciones largas y su solución a nivel requisito (no de implementación)? [Clarity, Spec §FR-009, Edge Cases]

## Notes

- Primera pasada: 20/22 — fallaron CHK012 (no estaba definido el efecto de deshabilitar
  un modelo sobre tareas YA etiquetadas con él) y CHK016 (el % económico no declaraba
  el umbral de "económico"). Ambos corregidos en el spec (FR-008a ampliado con la
  regla de reasignación + advertencia; FR-010 fija costo < 3 como definición vigente).
- Segunda pasada: 22/22. Spec listo para la fase tasks.
