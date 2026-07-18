# Research: Especificador de Agentes y README del Proyecto

**Feature**: 002-agent-specifier | **Date**: 2026-07-18

Sin NEEDS CLARIFICATION pendientes (resueltos en la sesión de clarify). Decisiones:

## R1 — Formato de definición portable de agente

**Decision**: `.specify/agents/<nombre>.md` con frontmatter YAML estructurado
(`name`, `dominio`, `rol`, `origen: generado|editado`, `fecha`) y cuerpo con
Responsabilidades / Límites / Instrucciones. Detalle en contracts/agent-definition.md.

**Rationale**: frontmatter parseable permite la detección de cobertura por dominio
(FR-005) sin heurísticas sobre prosa; un archivo por agente aísla ediciones manuales
y el archivado de huérfanos (Clarificación S2).

**Alternatives considered**: JSON (menos amigable para editar prosa de instrucciones);
un único archivo agregado (rechazado en clarify).

## R2 — Derivación nativa por CLI

**Decision**: para Claude Code, generar `.claude/agents/<nombre>.md` con el frontmatter
de subagente que Claude espera (`name`, `description`, opcional `tools`) y el cuerpo
como system prompt, derivado 1:1 del portable. Para Codex/Kimi (sin formato nativo de
subagentes equivalente), el portable ES el consumible: `AGENTS.md` indica cómo usarlos
como instrucciones de rol.

**Rationale**: Claude tiene soporte nativo de subagentes (`.claude/agents/`); forzar
un equivalente donde no existe violaría la regla de no depender de features exclusivas
— el formato portable cubre a todos (Constitución II).

**Alternatives considered**: generar solo el nativo (rompe portabilidad); no derivar
nativo (desaprovecha el soporte real de Claude).

## R3 — Detección de ediciones manuales e idempotencia

**Decision**: el frontmatter lleva `origen: generado`; si el usuario edita, puede
cambiarlo a `editado` o no — la regla operativa es más simple: `speckit-agents` NUNCA
sobrescribe un archivo existente en `.specify/agents/`; solo crea faltantes y reporta.
La cobertura se evalúa por el campo `dominio` de los existentes (no por nombre).

**Rationale**: "nunca sobrescribir existentes" hace la idempotencia trivial y a prueba
de errores (FR-005, SC-003/SC-004) sin mecanismos de hash/comparación.

**Alternatives considered**: hash de contenido para detectar ediciones (complejidad
innecesaria cuando la política es no tocar existentes).

## R4 — Delimitadores del README gestionado

**Decision**: comentarios HTML invisibles en el render:
`<!-- speckit:seccion:inicio -->` / `<!-- speckit:seccion:fin -->`, con secciones
`objetivo`, `alcance`, `estado`. La fecha de actualización va dentro de cada sección
gestionada. Detalle en contracts/readme-sections.md.

**Rationale**: los comentarios HTML no ensucian el render de GitHub/editores, son
inequívocos para buscar/reemplazar y es el patrón estándar de secciones generadas
(badges, TOCs automáticos).

**Alternatives considered**: encabezados con sufijo especial (visibles y frágiles);
archivo README separado (pierde el punto: EL readme del proyecto).

## R5 — Fuente del objetivo y detección de idioma

**Decision**: orden de fuentes FR-001 (constitución → README → specs → preguntar).
Idioma: el de la fuente del objetivo; si se pregunta el objetivo, el idioma de la
respuesta del usuario.

**Rationale**: coherente con el flujo spec-kit (la constitución es la declaración de
gobierno más curada); cero configuración de idioma.

**Alternatives considered**: setting de idioma en un config (fricción innecesaria).

## R6 — Ofrecimiento post-specify en pipelines

**Decision**: en `speckit-specify-auto(-eco)`, tras la fase specify y SOLO si el triage
clasificó la idea como compleja, agregar una línea de ofrecimiento opcional: "¿Correr
el especificador de agentes para cubrir esta feature?"; declinar continúa el pipeline
sin efectos. La skill base `speckit-specify` no se toca.

**Rationale**: el triage ya conoce la complejidad (no hay costo extra de análisis);
los pipelines son de este proyecto (editarlos no viola Constitución I).

**Alternatives considered**: hooks de extensions.yml para after_specify (el usuario
eligió envoltorio/pipelines en la Clarificación S1; los pipelines cubren el caso
compleja mejor porque tienen el resultado del triage a mano).
