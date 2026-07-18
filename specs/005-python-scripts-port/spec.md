# Feature Specification: Scripts de soporte del orquestador en Python (multiplataforma)

**Feature Branch**: `005-python-scripts-port`

**Created**: 2026-07-18

**Status**: Draft

**Input**: User description: "portar los 6 scripts de soporte del orquestador multi-CLI de PowerShell a Python (alineados con el CLI del fork), reconectar los playbooks y skills que los invocan, y migrar los tests Pester a pytest, para que el producto corra en cualquier entorno solo con Python sin depender de pwsh"

## Clarifications

### Session 2026-07-18

- Sin preguntas de clarificación: la feature tiene requisito claro (portar ps→py
  conservando comportamiento) y criterios verificables.
- **Diferido a plan (HOW, no ambigüedad de spec)**: el mecanismo concreto de invocación de
  los scripts Python (script suelto invocado por el intérprete, módulo `python -m`, o
  subcomando del `specify`). Impacta cómo los playbooks/skills los llaman (FR-004); lo
  decide `/speckit-plan` con fundamento técnico.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Orquestar en Linux/macOS sin instalar PowerShell (Priority: P1)

Una persona instala el fork de gen (`specify init`) en un proyecto sobre Linux o macOS,
donde **no** tiene PowerShell instalado, solo Python (que ya es requisito del CLI). Corre
el flujo multi-CLI (`/speckit-models`, luego un pipeline auto) y todo funciona: la
detección de CLIs, la clasificación de tareas, el despacho headless a los secundarios, el
fallback por cuota y la planificación de tandas — sin ningún error por falta de `pwsh`.

**Why this priority**: es el objetivo entero de la feature. Hoy el producto exige `pwsh`
en Linux/macOS; sacar esa dependencia es lo que lo vuelve usable "en cualquier entorno".

**Independent Test**: en un entorno con Python pero sin PowerShell, correr el ciclo del
orquestador (escaneo de modelos + un despacho) y verificar que completa sin errores de
intérprete faltante.

**Acceptance Scenarios**:

1. **Given** un entorno con Python y sin PowerShell, **When** se ejecuta el escaneo de
   modelos y un despacho de tarea del orquestador, **Then** ambos completan correctamente
   sin requerir `pwsh`.
2. **Given** un proyecto inicializado con el fork, **When** se inspeccionan las
   dependencias necesarias para el orquestador, **Then** solo aparece Python (y los CLIs
   de IA), sin PowerShell.

### User Story 2 - Mismo comportamiento y contratos que hoy (Priority: P1)

Quien ya usa el sistema multi-CLI en Windows obtiene **exactamente el mismo
comportamiento** tras la migración: los contratos de datos (formato de `models.json`, las
etiquetas `[C:]`/`[M:]`, el JSON de tandas paralelas, las clasificaciones de resultado
`exito`/`cuota_agotada`/`indisponible`, los reportes de orquestación) no cambian. La
migración es de lenguaje, no de comportamiento.

**Why this priority**: la migración no debe introducir regresiones en un sistema que ya
funciona en producción (features 001-003). Sin paridad, se rompe el valor existente.

**Independent Test**: comparar salidas de los scripts Python contra los contratos
vigentes (mismos campos, mismos strings de clasificación, mismo formato JSON) con casos
equivalentes a los tests actuales.

**Acceptance Scenarios**:

1. **Given** una tarea despachada a un secundario, **When** el script Python la procesa,
   **Then** clasifica el resultado con los mismos valores (`exito`/`cuota_agotada`/
   `indisponible`) y respeta timeout y reintento como hoy.
2. **Given** un `tasks.md` etiquetado, **When** se planifican las tandas, **Then** el
   agrupamiento `[P]`/serial y el JSON de salida son equivalentes a los actuales.
3. **Given** `models.json` y el catálogo de CLIs, **When** se registra/edita/baja un CLI
   o se actualiza una cuota, **Then** el archivo resultante mantiene el formato y las
   reglas actuales (corrección manual del usuario prevalece).

### User Story 3 - Playbooks, skills y tests reconectados (Priority: P2)

Los playbooks del orquestador (`triage`, `assign`, `orchestrate`) y las skills que
invocan los scripts (`speckit-models`, `speckit-orchestrate`, `speckit-clis`) referencian
la versión Python y funcionan de punta a punta. Los tests que validaban los scripts
existen y pasan en el nuevo lenguaje.

**Why this priority**: sin reconectar los invocadores, los scripts Python quedan
huérfanos; sin tests migrados, no hay red de seguridad para la paridad (US2).

**Independent Test**: correr un pipeline auto que use el orquestador y verificar que las
skills/playbooks llaman a los scripts Python; correr la suite de tests y verla en verde.

**Acceptance Scenarios**:

1. **Given** las skills y playbooks del producto, **When** se inspeccionan sus llamadas a
   scripts, **Then** apuntan a la versión Python (no a `.ps1`).
2. **Given** la suite de tests del proyecto, **When** se ejecuta, **Then** cubre los 6
   scripts portados y pasa sin depender de PowerShell.

### Edge Cases

- ¿Qué pasa en Windows (donde sí hay PowerShell)? El comportamiento debe seguir siendo
  correcto — la migración no debe romper el entorno donde hoy funciona.
- ¿Qué pasa con los scripts PowerShell heredados durante la transición? Se conservan pero
  ya no son la vía invocada; ningún componente nuevo depende de ellos.
- ¿Qué pasa con el despacho headless a secundarios (manejo de procesos, timeout,
  credenciales)? Debe preservar las mismas garantías de seguridad (ejecución dentro del
  repo, no filtrar credenciales) que la versión PowerShell.
- ¿Qué pasa si un entorno tiene ambos (Windows con Python y PowerShell)? El sistema usa la
  vía Python; no debe haber ambigüedad sobre cuál corre.
- ¿Qué pasa con proyectos ya inicializados con la versión PowerShell del producto? La
  migración/coexistencia no debe corromper su estado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Los 6 scripts de soporte del orquestador (detección de modelos, despacho a
  secundario, actualización de cuota, planificación de tandas paralelas, configuración de
  CLIs y el helper de plataforma/proceso) DEBEN reimplementarse en Python, alineados con
  el lenguaje del CLI del fork.
- **FR-002**: El producto DEBE funcionar en cualquier entorno (Windows/Linux/macOS) con
  **solo Python** instalado, sin requerir PowerShell/`pwsh` para ninguna función del
  orquestador.
- **FR-003**: La migración DEBE preservar el comportamiento y los contratos de datos
  vigentes: formato de `models.json` y del catálogo de CLIs, etiquetas `[C:]`/`[M:]`,
  JSON de tandas paralelas, clasificaciones `exito`/`cuota_agotada`/`indisponible`, y
  reglas de timeout/reintento del despacho. Sin cambios de comportamiento observable.
- **FR-004**: Los playbooks del orquestador (`triage`, `assign`, `orchestrate`) y las
  skills que invocan scripts (`speckit-models`, `speckit-orchestrate`, `speckit-clis`)
  DEBEN reconectarse para invocar la versión Python.
- **FR-005**: Los tests que validan los scripts DEBEN migrarse/re-escribirse para cubrir
  la versión Python y pasar sin depender de PowerShell.
- **FR-006**: El despacho headless a secundarios en Python DEBE preservar las garantías de
  seguridad actuales: ejecución dentro del repo, sin filtrar credenciales, timeout y
  reintento acotado.
- **FR-007**: El producto que entrega `specify init` DEBE incluir los scripts Python (en
  lugar de, o además de durante la transición, los PowerShell) de modo que un proyecto
  recién inicializado quede listo para orquestar en cualquier entorno.
- **FR-008**: Los scripts PowerShell heredados PUEDEN conservarse durante la transición,
  pero ningún componente nuevo del orquestador DEBE depender de ellos; la vía invocada por
  defecto es la Python.
- **FR-009**: El comportamiento en Windows (donde hoy funciona) DEBE seguir siendo
  correcto tras la migración (sin regresión).

### Key Entities

- **Scripts de soporte (6)**: detección de modelos, despacho a secundario, actualización
  de cuota, planificación de tandas, configuración de CLIs, helper de plataforma/proceso.
- **Contratos de datos**: `models.json`, catálogo de CLIs, etiquetas de `tasks.md`, JSON
  de tandas, clasificaciones de resultado — invariantes de la migración.
- **Invocadores**: playbooks (`triage`/`assign`/`orchestrate`) y skills
  (`speckit-models`/`speckit-orchestrate`/`speckit-clis`).
- **Suite de tests**: cobertura de los 6 scripts, ahora en el stack de tests del CLI.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El ciclo completo del orquestador (escaneo + clasificación + despacho +
  fallback + planificación de tandas) corre de punta a punta en Linux/macOS **sin
  PowerShell instalado**.
- **SC-002**: El 100% de los contratos de datos vigentes se mantienen idénticos tras la
  migración (verificable comparando formato/campos/strings contra los actuales).
- **SC-003**: El 100% de los 6 scripts tiene cobertura de tests equivalente a la actual,
  y la suite pasa sin depender de PowerShell.
- **SC-004**: Ningún componente del orquestador (skills, playbooks, scripts) invoca
  PowerShell como dependencia para operar tras la migración.
- **SC-005**: El comportamiento en Windows permanece correcto (la suite y un despacho real
  siguen pasando).

## Assumptions

- Los scripts Python se invocan con el intérprete Python ya disponible (requisito del
  CLI); el mecanismo concreto de invocación (script suelto, módulo `-m`, o subcomando del
  CLI) lo decide la fase de plan.
- La fuente de verdad del comportamiento a preservar son los scripts PowerShell actuales y
  sus tests Pester (features 001-003).
- Durante la transición pueden coexistir ambas versiones; la Python es la vía por defecto
  y la única de la que dependen los componentes nuevos.
- El stack de tests del componente forkeado es pytest (ya usado en la feature 004); los
  tests portados viven ahí.
- No se cambian los contratos ni el formato oficial de spec-kit (Principio I); esta
  feature es solo cambio de lenguaje de implementación de los scripts de soporte.
