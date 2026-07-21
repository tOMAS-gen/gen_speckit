# Model Discovery Requirements Checklist: Descubrimiento y verificación de modelos

**Purpose**: Validar completitud, claridad, consistencia y medibilidad de los requisitos
de detección/verificación de modelos antes de tareas.
**Created**: 2026-07-18
**Feature**: [spec.md](../spec.md)

**Note**: Estos ítems testean cómo están **escritos** los requisitos, no la implementación.

## Requirement Completeness

- [ ] CHK001 ¿Está definida la cadena completa de detección (comando → config → semillas) y su orden? [Completeness, data-model §Reglas]
- [ ] CHK002 ¿Está definido el comportamiento para CLIs sin ningún mecanismo de listado? [Completeness, Spec §US1-3, Edge Cases]
- [ ] CHK003 ¿Está definido quién hace la verificación web y qué pasa sin red? [Completeness, Spec §FR-004, §FR-009]
- [ ] CHK004 ¿Están definidos los campos nuevos del contrato (origen, esfuerzos, verificacion_web) con sus valores válidos? [Completeness, data-model]
- [ ] CHK005 ¿Está definido el tratamiento de mecanismos que consumen cuota (opt-in)? [Completeness, Spec §FR-006]

## Requirement Clarity

- [ ] CHK006 ¿"Nunca inventar modelos" es verificable (todo modelo con origen de 3 valores)? [Clarity, Spec §FR-005, SC-001]
- [ ] CHK007 ¿"Best-effort" está definido operacionalmente (omitir declarándolo, sin fallar)? [Clarity, Spec §FR-004, SC-004]
- [ ] CHK008 ¿La decisión de ranking (todos los orígenes participan) quedó inequívoca y trazada a la clarificación del usuario? [Clarity, Spec §Clarifications, FR-003]

## Requirement Consistency

- [ ] CHK009 ¿La entrada al ranking de `oficial-sin-confirmar` es consistente con el fallback del orquestador (no requiere cambios en él)? [Consistency, Spec §Clarifications, plan §Constitution IV]
- [ ] CHK010 ¿El merge de campos nuevos es consistente con la regla vigente (usuario prevalece)? [Consistency, Spec §FR-008, research §Riesgos]
- [ ] CHK011 ¿La aditividad del contrato (SC-005) es consistente con los consumidores listados (asignador, orquestador, despacho)? [Consistency, contracts §Invariantes]

## Acceptance Criteria Quality

- [ ] CHK012 ¿SC-001 (100% con origen, 0 inventados) es objetivamente verificable? [Measurability]
- [ ] CHK013 ¿SC-002 (coincidencia con lo que el CLI reporta) define el método de comparación? [Measurability]
- [ ] CHK014 ¿SC-003 (esfuerzos + merge) es testeable con un re-escaneo? [Measurability]

## Edge Case Coverage

- [ ] CHK015 ¿Salida no parseable / config corrupta → degradar sin abortar está cubierto? [Edge Case, contracts §Script 3]
- [ ] CHK016 ¿Discrepancia semilla vs. detección real (gana lo real) está cubierta? [Edge Case, Spec §Edge Cases]
- [ ] CHK017 ¿Modelo retirado (semilla que ya no existe oficialmente) tiene comportamiento definido? [Gap — ver Notes]

## Dependencies & Assumptions

- [ ] CHK018 ¿El supuesto "config files por CLI a confirmar al implementar" está registrado como riesgo? [Assumption, research §Riesgos]
- [ ] CHK019 ¿El alcance excluye cambios al asignador (esfuerzos solo se registran)? [Assumption, Spec §Assumptions]

## Notes

- CHK017: el spec cubre "modelo retirado" solo implícitamente (gana lo real/lo oficial).
  Comportamiento por defecto propuesto: no se borra — se conserva con su origen previo y
  el usuario decide (borrar automático rompería ediciones manuales). Registrado para que
  tasks lo haga explícito en la lógica de cruce.
