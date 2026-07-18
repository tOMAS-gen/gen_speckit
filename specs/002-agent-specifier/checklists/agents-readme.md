# Checklist: Calidad de Requisitos — Especificador de Agentes y README

**Purpose**: Validar completitud, claridad y consistencia de los requisitos antes de generar tareas
**Created**: 2026-07-18
**Feature**: [spec.md](../spec.md)
**Focus**: idempotencia/preservación + integración aditiva | **Depth**: estándar | **Audience**: autor
**Status**: ✅ Revisado 2026-07-18 — 18/18 resueltos (16 ya cubiertos, 2 corregidos en spec)

## Cobertura y Propuesta de Agentes

- [x] CHK001 - ¿Está definido cómo se identifican los dominios de forma reproducible? [Measurability, Spec §FR-002 — taxonomía base fija + extras, Clarificación S3]
- [x] CHK002 - ¿Se especifica qué pasa con los dominios base que no aplican al objetivo? [Coverage, data-model §3 — se listan como "no aplica" con justificación]
- [x] CHK003 - ¿Está definida la aprobación parcial de la propuesta? [Completeness, Spec §FR-003 — total/parcial/rechazo]
- [x] CHK004 - ¿Se define el comportamiento ante colisión de nombre (agente propuesto con nombre ya usado por otro dominio)? [Edge Case → resuelto: nuevo edge case en spec — se propone nombre alternativo, nunca se sobrescribe]
- [x] CHK005 - ¿El alcance del análisis (proyecto vs. feature) está definido cuando se dispara post-specify? [Ambiguity → resuelto: FR-012 aclara que el análisis siempre es a nivel proyecto; la feature puede revelar dominios nuevos]
- [x] CHK006 - ¿Está definido el origen del objetivo y su orden de precedencia? [Clarity, Spec §FR-001]
- [x] CHK007 - ¿Se especifica que declinar no tiene efectos secundarios? [Coverage, Spec §FR-003, §US3-3]

## Idempotencia y Preservación

- [x] CHK008 - ¿La regla de no-duplicación es objetivamente verificable? [Measurability, Spec §FR-005 + SC-004 — por dominio/rol, no por nombre]
- [x] CHK009 - ¿Está definido el trato de definiciones editadas a mano? [Completeness, Spec §FR-005, research R3 — nunca sobrescribir existentes]
- [x] CHK010 - ¿El manejo de agentes huérfanos evita pérdida de datos? [Coverage, Spec §FR-006 — reporta y sugiere, no borra]
- [x] CHK011 - ¿La preservación del contenido manual del README es total y verificable? [Measurability, Spec §FR-008 — 100% fuera de delimitadores, SC-003]
- [x] CHK012 - ¿Está definido el caso de README con delimitadores rotos? [Edge Case, Spec §Edge Cases + contracts/readme-sections regla 5]
- [x] CHK013 - ¿Está definido el caso de README preexistente sin delimitadores? [Coverage, Spec §FR-009 — confirmación antes del primer cambio]

## Integración Aditiva y Portabilidad

- [x] CHK014 - ¿El mecanismo de integración con constitution preserva la skill base intacta? [Consistency, Spec §FR-012 + Clarificación S1 — envoltorio]
- [x] CHK015 - ¿Las definiciones son consumibles desde cualquier CLI principal? [Coverage, Spec §FR-004 + research R2 — portable universal, nativo opcional]
- [x] CHK016 - ¿Los disparos automáticos son opcionales y no bloqueantes en todos los casos? [Consistency, Spec §FR-012, §US3]
- [x] CHK017 - ¿SC-006 (compatibilidad) tiene forma de verificación definida? [Measurability, quickstart escenario 7]
- [x] CHK018 - ¿El idioma de los artefactos generados está definido sin configuración extra? [Clarity, Spec §Assumptions + research R5]

## Notes

- CHK004 y CHK005 generaron ediciones en spec.md (edge case nuevo + FR-012 ampliado);
  el resto ya estaba cubierto por spec, clarificaciones, contratos o data-model.
