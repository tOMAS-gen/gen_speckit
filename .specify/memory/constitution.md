<!--
Sync Impact Report (v1.1.0 — 2026-07-18)
==================
Version change: 1.0.0 → 1.1.0 (MINOR: restricción técnica materialmente modificada).
Motivo: el proyecto pasó a ser un fork del spec-kit oficial (CLI en Python). La sección
"Contratos de Datos y Restricciones Técnicas" cambia la plataforma objetivo y el lenguaje
de los scripts de soporte: de "Windows 11 + PowerShell" a "cualquier entorno + Python",
sin dependencia de PowerShell/pwsh. Los seis principios quedan intactos.
Plantillas revisadas: plan-template.md (Constitution Check genérico, sin cambios) ✅ ·
spec-template.md (sin secciones nuevas) ✅ · tasks-template.md (sin cambios de formato) ✅.
Follow-up: portar los scripts `.specify/scripts/powershell/` a Python (feature de
migración; los scripts heredados se conservan durante la transición).

---- Sync Impact Report inicial (v1.0.0) ----
Version change: (template, sin versión) → 1.0.0
Ratificación inicial: se reemplazan todos los placeholders del template por los
principios derivados de README.md.

Principios definidos (nuevos, sin títulos previos):
- I. Compatibilidad Total con Spec Kit (Solo Aditiva)
- II. Portabilidad Multi-CLI (Arquitectura Simétrica)
- III. El Más Barato que Alcance
- IV. Nunca Discriminar un Modelo
- V. Las Decisiones Caras las Toma el Modelo Más Capaz
- VI. Mínima Intervención del Usuario, con Gates Reales

Secciones agregadas:
- Contratos de Datos y Restricciones Técnicas (Sección 2)
- Flujo de Trabajo y Puertas de Calidad (Sección 3)
- Governance (completada desde placeholder)

Secciones eliminadas: ninguna (se llenaron todos los slots del template).

Templates revisados:
- ✅ .specify/templates/plan-template.md — el gate "Constitution Check" es genérico
  ("determinado según el archivo de constitución"); compatible sin cambios.
- ✅ .specify/templates/spec-template.md — sin secciones obligatorias nuevas; compatible.
- ⚠ .specify/templates/tasks-template.md — pendiente: cuando se implemente el asignador
  (Paso 5 del README), la línea de formato deberá documentar las etiquetas aditivas
  [C:baja|media|alta] y [M:cli/modelo]. No se modifica ahora porque la feature aún no existe.
- ✅ .claude/skills/speckit-*/SKILL.md — sin referencias agent-específicas obsoletas.

TODOs diferidos: ninguno.
-->

# Constitución de gen_speckit

## Core Principles

### I. Compatibilidad Total con Spec Kit (Solo Aditiva)

Todo lo que hace el spec-kit original de GitHub DEBE seguir funcionando igual: mismas
skills base, mismos comandos, misma estructura `.specify/` y mismo gesto de instalación
(`uv tool install ... --from git+...` + `specify init`). Las mejoras de este proyecto
(pipelines auto, triage, `/speckit-models`, asignador, orquestador) SOLO agregan
funcionalidad; NUNCA modifican ni rompen el formato oficial de los artefactos de
spec-kit (checkbox, `T###`, `[P]`, `[US#]`, rutas en `tasks.md`). Las etiquetas propias
(`[C:...]`, `[M:...]`) son aditivas e inline.

**Racional**: quien conoce spec-kit no debe aprender nada nuevo; quien quiere las
mejoras las obtiene con el mismo gesto. Romper compatibilidad destruiría la propuesta
de valor del proyecto.

### II. Portabilidad Multi-CLI (Arquitectura Simétrica)

El orquestador DEBE poder correr desde cualquiera de los tres CLIs (Claude Code, Codex,
Kimi) actuando como principal, con los otros dos como secundarios invocados por línea
de comandos en modo headless. Ninguna skill, script o contrato de datos del orquestador
PUEDE depender de features exclusivas de un CLI. Las invocaciones a secundarios DEBEN
usar el comando `headless` declarado en `.specify/models.json`.

**Racional**: ningún punto de entrada es incorrecto — la idea se escribe en cualquier
CLI y el sistema se reacomoda solo. Una dependencia exclusiva rompería esa simetría.

### III. El Más Barato que Alcance

Cada tarea DEBE asignarse al modelo más económico cuya capacidad y ventana de contexto
alcanzan para resolverla bien. Los modelos caros se reservan SOLO para las tareas donde
hacen la diferencia (complejidad alta, decisiones de planificación). El sistema DEBE
respetar los límites de cuota declarados/detectados y NUNCA desperdiciar cuota cara en
trabajo trivial.

**Racional**: el objetivo central del proyecto es reducir costo y uso; cada token caro
gastado en algo que un modelo económico resolvía igual es una falla del sistema.

### IV. Nunca Discriminar un Modelo

El ranking de `.specify/models.json` ordena candidatos; NUNCA excluye a ninguno. Todos
los CLIs instalados y autenticados DEBEN participar del reparto de tareas según su
capacidad, costo y disponibilidad. Por cada nivel de complejidad DEBE existir una lista
ordenada de candidatos con fallback resuelto por diseño: si el preferido no tiene cuota
o contexto, se escala al siguiente sin intervención del usuario.

**Racional**: excluir modelos concentra el trabajo en los caros (contradice el
Principio III) y elimina la resiliencia ante agotamiento de cuota.

### V. Las Decisiones Caras las Toma el Modelo Más Capaz

El triage de la idea, la clasificación de complejidad de tareas y la asignación de
modelos DEBEN ser ejecutados por el modelo más capaz disponible: equivocarse en el
reparto es caro; ejecutar una tarea simple, no. El triage DEBE autoevaluarse e incluir
al propio modelo que recibió la idea: si el punto de entrada es inferior a lo que la
idea requiere, DEBE escalar la planificación hacia arriba; si es superior a lo
necesario, DEBE degradar el trabajo hacia los modelos económicos.

**Racional**: la calidad de la orquestación depende de la calidad del reparto; el
análisis en sí es corto, así que pagarlo con el modelo importante es barato comparado
con el costo de un reparto equivocado.

### VI. Mínima Intervención del Usuario, con Gates Reales

Los pipelines DEBEN encadenar fases automáticamente a partir de una sola llamada con la
idea, y SOLO detenerse ante decisiones o dudas reales (preguntas de clarificación,
hallazgos críticos, gate previo a implement). El flag `-bypass` DEBE saltar el gate de
confirmación solo cuando no hay dudas pendientes, informándolo en el reporte. Los
pipelines DEBEN ser retomables: detectar artefactos existentes y continuar desde la
fase faltante sin rehacer trabajo.

**Racional**: "solo pongo la idea" es el contrato con el usuario; cada interrupción
innecesaria o trabajo rehecho erosiona ese contrato y quema cuota.

## Contratos de Datos y Restricciones Técnicas

- `tasks.md`: las etiquetas `[C:baja|media|alta]` y `[M:cli/modelo]` las agrega el
  asignador al final de la fase tasks y DEBEN quedar inline, editables a mano antes de
  implementar. El formato oficial de spec-kit no se toca (Principio I).
- `.specify/models.json`: lo genera `/speckit-models` combinando detección automática
  (CLIs instalados, versión, autenticación, modo headless, modelos expuestos) con
  declaración del usuario (plan contratado, cuotas, ventana de contexto). Los campos
  `capacidad` (1–10) y `costo` (1–3) son comparables entre CLIs y corregibles a mano;
  la corrección manual del usuario SIEMPRE prevalece sobre lo detectado.
- Configuración previa obligatoria: antes de orquestar DEBE existir `models.json` con
  plan, modelos, contexto y cuota por plataforma (lo detectable, detectado; lo no
  detectable, declarado o marcado como desconocido).
- Plataforma objetivo: cualquier entorno (Windows / Linux / macOS). Como el proyecto es
  un **fork del spec-kit oficial** (CLI en Python), los scripts de soporte del orquestador
  se escriben en **Python**, alineados con el lenguaje del CLI forkeado, de modo que el
  producto corra en cualquier plataforma con solo Python instalado, **sin dependencia de
  PowerShell/`pwsh`**. Dependencias: `uv` (Python ≥3.11) y los CLIs de IA instalados
  (Claude Code, Codex, Kimi u otros registrados). Los scripts PowerShell heredados
  (`.specify/scripts/powershell/`) se conservan durante la transición pero se migran a
  Python; ningún componente nuevo del orquestador DEBE depender de PowerShell.

## Flujo de Trabajo y Puertas de Calidad

- Preparación (una vez): `/speckit-models` genera el inventario y ranking.
- Por cada idea: triage primero (Principio V) → elige flujo ECO (specify → plan →
  tasks → gate → implement) o IDEAL (specify → clarify → plan → checklist → tasks →
  analyze → gate → implement) y qué modelo ejecuta cada fase.
- Si el flujo invocado no coincide con lo recomendado por el triage: sin `-bypass` se
  pregunta al usuario; con `-bypass` se cambia solo y se informa en el reporte.
- Fase implement: el orquestador lee `tasks.md`, despacha cada tarea a su CLI asignado
  (las `[P]` en paralelo, respetando dependencias), escala al siguiente candidato del
  ranking si un modelo agota cuota, y el principal integra, verifica y marca `[X]`.
- Toda nueva skill o script DEBE validarse contra el flujo completo (Paso 7 del
  README): planificar con el pipeline y medir ahorro de costo/uso real.

## Governance

- Esta constitución prevalece sobre cualquier otra práctica del proyecto. El gate
  "Constitution Check" de `plan-template.md` DEBE verificar los seis principios; toda
  violación DEBE justificarse en "Complexity Tracking" o corregirse antes de avanzar.
- Enmiendas: se proponen editando este archivo vía `/speckit-constitution`, documentando
  el cambio en el Sync Impact Report y propagándolo a los templates dependientes
  (`plan-template.md`, `spec-template.md`, `tasks-template.md`) y skills afectadas.
- Versionado semántico de la constitución: MAJOR para remociones o redefiniciones
  incompatibles de principios; MINOR para principios o secciones nuevas o guía
  materialmente ampliada; PATCH para clarificaciones y correcciones de redacción.
- Revisión de cumplimiento: en cada fase plan se corre el Constitution Check; en cada
  revisión de artefactos (analyze) se verifica que las asignaciones de modelos respeten
  los Principios III, IV y V.

**Version**: 1.1.0 | **Ratified**: 2026-07-17 | **Last Amended**: 2026-07-18
