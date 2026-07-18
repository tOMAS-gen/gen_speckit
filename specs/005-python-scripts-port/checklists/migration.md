# Migration Quality Checklist: Scripts de soporte en Python

**Purpose**: Validar la calidad de los requisitos de esta migración (completitud, claridad,
consistencia, medibilidad, cobertura) antes de tareas.
**Created**: 2026-07-18
**Feature**: [spec.md](../spec.md)

**Note**: Estos ítems testean cómo están **escritos** los requisitos, no la implementación.

## Requirement Completeness

- [ ] CHK001 ¿Están enumerados los 6 scripts a portar sin ambigüedad? [Completeness, Spec §FR-001, Contracts]
- [ ] CHK002 ¿Está especificado qué invocadores (playbooks/skills) deben reconectarse? [Completeness, Spec §FR-004]
- [ ] CHK003 ¿Se define el destino de los tests (migrar a pytest) y su alcance? [Completeness, Spec §FR-005]
- [ ] CHK004 ¿Se define qué pasa con los scripts PowerShell heredados (conservar/transición)? [Completeness, Spec §FR-008]
- [ ] CHK005 ¿Está cubierta la entrega del producto (bundling) con los scripts Python? [Completeness, Spec §FR-007]

## Requirement Clarity

- [ ] CHK006 ¿"Preservar comportamiento y contratos" está definido con contratos concretos y verificables? [Clarity, Spec §FR-003, data-model]
- [ ] CHK007 ¿"Cualquier entorno con solo Python" está acotado a las plataformas soportadas? [Clarity, Spec §FR-002]
- [ ] CHK008 ¿Las garantías de seguridad del despacho están enunciadas de forma testeable? [Clarity, Spec §FR-006]
- [ ] CHK009 ¿El mecanismo de invocación quedó explícitamente diferido a plan (y luego decidido)? [Clarity, Spec §Clarifications, plan §Summary]

## Requirement Consistency

- [ ] CHK010 ¿La coexistencia ps/python (FR-008) es consistente con el bundling (FR-007) y con la constitución v1.1.0? [Consistency]
- [ ] CHK011 ¿"Sin cambios de comportamiento" (FR-003) es consistente con "sin regresión en Windows" (FR-009)? [Consistency]

## Acceptance Criteria Quality (Measurability)

- [ ] CHK012 ¿SC-001 (correr sin PowerShell) es objetivamente verificable? [Measurability, Spec §SC-001]
- [ ] CHK013 ¿SC-002 (100% de contratos idénticos) tiene un método de comparación claro? [Measurability, Spec §SC-002]
- [ ] CHK014 ¿SC-003 (cobertura de tests equivalente) define "equivalente"? [Measurability, Spec §SC-003]
- [ ] CHK015 ¿SC-004 (ningún componente invoca PowerShell) es verificable por inspección? [Measurability, Spec §SC-004]

## Scenario & Edge Case Coverage

- [ ] CHK016 ¿Se cubre el comportamiento en Windows (donde ya funciona)? [Coverage, Spec §FR-009, Edge Cases]
- [ ] CHK017 ¿Se cubre el despacho headless (procesos, timeout, credenciales) con paridad? [Coverage, Spec §FR-006]
- [ ] CHK018 ¿Se cubre el caso de proyectos ya inicializados con la versión ps? [Coverage, Spec §Edge Cases]
- [ ] CHK019 ¿Se cubre la detección de CLIs que requiere ejecutar `--version`/auth (mock en tests)? [Coverage, research §Riesgos]

## Dependencies & Assumptions

- [ ] CHK020 ¿El supuesto "solo stdlib de Python, sin deps nuevas" está documentado? [Assumption, plan §Technical Context]
- [ ] CHK021 ¿El supuesto "fuente de verdad = scripts ps + Pester actuales" está explícito? [Assumption, Spec §Assumptions]

## Ambiguities & Conflicts

- [ ] CHK022 ¿Queda claro que esta feature NO cambia contratos ni formato oficial de spec-kit (solo lenguaje)? [Ambiguity, Spec §Assumptions, Constitution I]
- [ ] CHK023 ¿El alcance excluye rediseñar la lógica de asignación/fallback (solo port)? [Ambiguity, plan §Constitution Check]

## Notes

- Marcar `[x]` al validar cada ítem. Gaps abiertos → resolver en tasks/analyze o
  registrar como riesgo aceptado.
