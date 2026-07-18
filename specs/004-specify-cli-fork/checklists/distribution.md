# Distribution & Packaging Requirements Checklist: Fork de specify-cli con mejoras multi-CLI

**Purpose**: Validar la calidad (completitud, claridad, consistencia, medibilidad,
cobertura) de los requisitos de esta feature de empaquetado/distribución antes de tareas.
**Created**: 2026-07-18
**Feature**: [spec.md](../spec.md)

**Note**: Estos ítems testean cómo están **escritos** los requisitos, no la implementación.

## Requirement Completeness

- [ ] CHK001 ¿El conjunto exacto de elementos del producto multi-CLI a entregar está enumerado sin ambigüedad? [Completeness, Spec §FR-002, Contracts §product-delivery]
- [ ] CHK002 ¿Está definido el comportamiento del `init` cuando el destino ya tiene `.specify/` previo? [Completeness, Spec §Edge Cases, §FR-005]
- [ ] CHK003 ¿Se especifica qué NO se entrega al destino (separación producto vs. desarrollo del fork)? [Completeness, Contracts §product-delivery]
- [ ] CHK004 ¿Están documentados los requisitos de mantenimiento del fork contra upstream (procedimiento de sync)? [Completeness, Spec §FR-007]
- [ ] CHK005 ¿Se define qué versión del upstream se toma como base del fork? [Gap, Spec §Assumptions]
- [ ] CHK006 ¿Están definidos los requisitos para las tres plataformas soportadas (Windows/Linux/macOS)? [Completeness, Spec §FR-006]

## Requirement Clarity

- [ ] CHK007 ¿El término "fork real / mejoras integradas (no overlay)" está definido de forma verificable? [Clarity, Spec §FR-007, §Clarifications]
- [ ] CHK008 ¿"Instalar todo de una / un solo paso" está cuantificado (qué cuenta como un paso vs. la instalación única de la herramienta)? [Clarity, Spec §SC-001]
- [ ] CHK009 ¿La regla de entrega por agente (claude/kimi vs. codex) está especificada sin ambigüedad de formato/ubicación? [Clarity, Contracts §product-delivery]
- [ ] CHK010 ¿"No destructivo" está definido con reglas concretas por artefacto (AGENTS.md, .specify/, .gitignore)? [Clarity, Spec §FR-005]
- [ ] CHK011 ¿El default de `--skills` (mismo agente que `--integration`) está explícito? [Clarity, Contracts §init-command]

## Requirement Consistency

- [ ] CHK012 ¿La decisión "producto siempre integrado, sin flag para omitir" es consistente entre spec (FR-009) y el contrato del `init`? [Consistency, Spec §FR-009, Contracts §init-command]
- [ ] CHK013 ¿La conservación del comando `specify` (FR-008) es consistente con el gesto de instalación documentado en quickstart? [Consistency, Spec §FR-008, §quickstart]
- [ ] CHK014 ¿El manifiesto como "fuente de verdad" (Assumptions) es consistente con las tablas de data-model y contracts? [Consistency, Spec §Assumptions, §data-model]
- [ ] CHK015 ¿La compatibilidad aditiva (FR-003) no entra en conflicto con "reemplazar al specify oficial" (FR-008)? [Consistency, Spec §FR-003, §FR-008]

## Acceptance Criteria Quality (Measurability)

- [ ] CHK016 ¿SC-002 ("100% de los elementos") es objetivamente verificable ítem por ítem? [Measurability, Spec §SC-002]
- [ ] CHK017 ¿SC-003 ("sin regresión de compatibilidad") tiene un criterio medible de "igual que el oficial"? [Measurability, Spec §SC-003]
- [ ] CHK018 ¿SC-004 (pipelines de punta a punta) define qué constituye "no falta ningún playbook/script/skill"? [Measurability, Spec §SC-004]
- [ ] CHK019 ¿SC-005 (multiplataforma) especifica qué es "entrega equivalente"? [Measurability, Spec §SC-005]

## Scenario & Edge Case Coverage

- [ ] CHK020 ¿Hay requisitos para el caso de colisión con un `specify` oficial ya instalado? [Coverage, Spec §Edge Cases, Research §Decisión 3]
- [ ] CHK021 ¿Se cubre la migración de un usuario que instaló con la vía anterior (`install.ps1`)? [Coverage, Spec §Edge Cases]
- [ ] CHK022 ¿Se define el comportamiento ante un agente de `--skills` desconocido? [Coverage, Contracts §init-command]
- [ ] CHK023 ¿Se define qué pasa si falta un elemento del producto en el bundle (no silencioso)? [Edge Case, Contracts §init-command]
- [ ] CHK024 ¿Están cubiertos los requisitos de idempotencia al re-correr `init` sobre un proyecto ya inicializado? [Coverage, Contracts §init-command]

## Dependencies & Assumptions

- [ ] CHK025 ¿La dependencia de `uv` y de los CLIs (sin API keys) está documentada como supuesto? [Assumption, Spec §Assumptions]
- [ ] CHK026 ¿El supuesto "manifiesto de install.ps1 = fuente de verdad" está validado y es rastreable? [Assumption, Spec §Assumptions]
- [ ] CHK027 ¿El riesgo no verificado (detalle interno del `bundler/` de upstream) está registrado como punto abierto? [Assumption, Research §Riesgos]

## Ambiguities & Conflicts

- [ ] CHK028 ¿Queda alguna decisión de destino de `install.ps1` sin resolver (deprecar vs. conservar)? [Ambiguity, Spec §FR-009]
- [ ] CHK029 ¿El alcance de "reemplaza al oficial, sin convivencia" es inequívoco respecto de máquinas con ambos instalados? [Ambiguity, Spec §FR-008]

## Notes

- Marcar `[x]` al validar cada ítem; anotar hallazgos inline.
- Ítems con `[Gap]`/`[Ambiguity]` que queden abiertos deberían resolverse en tasks/analyze
  o registrarse como riesgo aceptado.
