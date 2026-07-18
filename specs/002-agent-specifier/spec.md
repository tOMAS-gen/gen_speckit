# Feature Specification: Especificador de Agentes y README del Proyecto

**Feature Branch**: `002-agent-specifier`

**Created**: 2026-07-18

**Status**: Draft

**Input**: User description: "Especificador de agentes: skill que analiza el objetivo del proyecto (en la fase constitution o al correr specify sobre una idea compleja) y determina qué agentes se van a necesitar para cubrir todas las necesidades del proyecto según el stack o tipo de tarea, generando sus definiciones. Además, otra skill que crea/actualiza un README.md que detalla el objetivo del proyecto, para no perder la idea original."

## Clarifications

### Session 2026-07-18

- Q: ¿Cómo se integra el ofrecimiento post-constitution sin modificar la skill base? → A: Con una skill envoltorio (`constitution-plus`): ejecuta la fase constitution base completa y al terminar ofrece el especificador de agentes. Para specify con idea compleja, el ofrecimiento lo hacen los pipelines de este proyecto tras su fase specify.
- Q: ¿Dónde viven las definiciones portables de agentes? → A: En `.specify/agents/<nombre>.md`, un archivo por agente (frontmatter con rol/dominio/límites + instrucciones); las versiones nativas por CLI se derivan de estos archivos.
- Q: ¿Cómo se identifican los dominios de necesidad? → A: Taxonomía base fija (interfaz/frontend, servicios/backend, datos, pruebas, documentación, seguridad, infraestructura/despliegue, integración con terceros) + dominios extra derivados del objetivo cuando no encajan en la base.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Especificar los agentes que el proyecto necesita (Priority: P1)

Como usuario de spec-kit, al establecer la constitución del proyecto (o al especificar
una idea compleja), el sistema analiza el objetivo del proyecto y me propone el
conjunto de agentes especializados que voy a necesitar para cubrir todas las
necesidades (por dominio del stack o tipo de tarea: p. ej. frontend, backend, datos,
testing, documentación, seguridad). Tras mi confirmación, genera las definiciones de
esos agentes listas para usar.

**Why this priority**: es el corazón del pedido — sin el análisis de cobertura, el
usuario arma agentes a mano y a ciegas; con él, el proyecto arranca con el equipo de
agentes correcto.

**Independent Test**: en un proyecto con constitución/objetivo declarado, correr el
especificador y verificar que propone agentes que cubren todos los dominios
detectables del objetivo, que pide confirmación antes de escribir, y que genera una
definición por agente aprobado.

**Acceptance Scenarios**:

1. **Given** un proyecto con objetivo declarado (constitución o README), **When** corro el especificador, **Then** obtengo una propuesta de agentes con nombre, rol, dominio que cubre y justificación, y ningún dominio del objetivo queda sin agente propuesto.
2. **Given** la propuesta de agentes, **When** confirmo (total o parcialmente), **Then** se generan las definiciones SOLO de los agentes aprobados, utilizables por el CLI en uso.
3. **Given** un proyecto que ya tiene agentes definidos, **When** re-corro el especificador, **Then** detecta los existentes, no los duplica ni los pisa, y solo propone los faltantes para cubrir huecos.
4. **Given** un objetivo sin fuente clara (no hay constitución ni README con objetivo), **When** corro el especificador, **Then** me pide que describa el objetivo antes de proponer nada — nunca inventa el objetivo.

---

### User Story 2 - README que preserva la idea del proyecto (Priority: P2)

Como usuario, tengo una skill que crea o actualiza el `README.md` del proyecto
detallando el objetivo, el alcance y el estado, para que la idea original no se
pierda a medida que el proyecto crece. Mis secciones escritas a mano se preservan.

**Why this priority**: es la memoria del proyecto — evita la deriva de objetivo, pero
tiene valor independiente del especificador.

**Independent Test**: en un proyecto sin README, correr la skill y verificar que crea
uno con el objetivo detallado; editar a mano una sección, re-correr, y verificar que
la edición sobrevive y solo se actualizan las secciones gestionadas.

**Acceptance Scenarios**:

1. **Given** un proyecto sin `README.md`, **When** corro la skill, **Then** se crea un README con el objetivo del proyecto, alcance y estado, derivado de las fuentes disponibles (constitución, specs) o de lo que yo declare.
2. **Given** un `README.md` existente con contenido manual, **When** re-corro la skill, **Then** solo se actualizan las secciones gestionadas (delimitadas de forma visible) y todo el contenido manual queda intacto.
3. **Given** un objetivo que cambió (nueva constitución o feature mayor), **When** corro la skill, **Then** el README refleja el objetivo actualizado y deja rastro de la fecha de actualización.

---

### User Story 3 - Integración con el flujo spec-kit (Priority: P3)

Como usuario del pipeline, el especificador de agentes se me ofrece automáticamente en
los momentos correctos: al terminar la fase constitution, y cuando una specify recibe
una idea clasificada compleja. También puedo invocar ambas skills manualmente en
cualquier momento.

**Why this priority**: automatizar el disparo es conveniencia; el valor central ya
existe con la invocación manual (US1/US2).

**Independent Test**: correr la fase constitution y verificar que al final ofrece
ejecutar el especificador; correr una specify con idea compleja y verificar el mismo
ofrecimiento; en ambos casos, declinar no bloquea el flujo.

**Acceptance Scenarios**:

1. **Given** una corrida de la skill envoltorio de constitution (`constitution-plus`), **When** la fase constitution base termina, **Then** se me ofrece correr el especificador de agentes (opcional, no bloqueante); la skill base `/speckit-constitution` sigue disponible sin cambios.
2. **Given** una specify cuya idea fue clasificada compleja, **When** termina la especificación, **Then** se me ofrece correr el especificador para cubrir la feature.
3. **Given** cualquiera de los ofrecimientos, **When** declino, **Then** el flujo continúa normalmente sin efectos secundarios.

---

### Edge Cases

- ¿Qué pasa si no existe ninguna fuente de objetivo (ni constitución, ni README, ni
  specs)? El especificador y la skill de README piden el objetivo al usuario antes de
  actuar; nunca lo inventan.
- ¿Qué pasa si el usuario editó a mano una definición de agente generada? Una
  re-corrida la respeta (no la regenera ni la pisa); solo propone agentes nuevos para
  huecos de cobertura.
- ¿Qué pasa si un dominio del objetivo ya está cubierto por un agente existente con
  otro nombre? El especificador lo reconoce como cubierto (por su rol/dominio
  declarado, no por el nombre) y no propone un duplicado.
- ¿Qué pasa si el objetivo del proyecto cambia radicalmente? El especificador reporta
  los agentes que quedaron huérfanos (sin dominio en el nuevo objetivo) y sugiere
  archivarlos — no los borra por su cuenta.
- ¿Qué pasa si el README no tiene los delimitadores de secciones gestionadas (README
  preexistente al adoptar la skill)? La skill propone dónde insertar las secciones y
  pide confirmación antes del primer cambio; nunca reescribe un README ajeno sin
  aprobación.
- ¿Qué pasa si el CLI en uso no soporta agentes/subagentes nativos? Las definiciones
  quedan en el formato portable del proyecto y el usuario las consume como
  instrucciones; la propuesta y la cobertura no dependen del CLI.
- ¿Qué pasa si un agente propuesto colisiona en nombre con uno existente de otro
  dominio? Se propone un nombre alternativo — un archivo existente jamás se
  sobrescribe.

## Requirements *(mandatory)*

### Functional Requirements

**Especificador de agentes**

- **FR-001**: El sistema MUST derivar el objetivo del proyecto de las fuentes disponibles en este orden: constitución, README, specs existentes; si ninguna existe o el objetivo es ilegible, MUST pedirlo al usuario y MUST NOT inventarlo.
- **FR-002**: El sistema MUST analizar el objetivo e identificar los dominios de necesidad evaluando una taxonomía base fija (interfaz/frontend, servicios/backend, datos, pruebas, documentación, seguridad, infraestructura/despliegue, integración con terceros) y agregando dominios extra derivados del objetivo cuando no encajan en la base; por cada dominio aplicable no cubierto MUST proponer al menos un agente con: nombre, rol, dominio que cubre, responsabilidades y límites (qué no debe hacer).
- **FR-003**: La propuesta MUST presentarse al usuario para confirmación (total, parcial o rechazo) ANTES de escribir cualquier definición; declinar MUST NOT tener efectos secundarios.
- **FR-004**: El sistema MUST generar las definiciones de los agentes aprobados como archivos portables individuales en `.specify/agents/<nombre>.md` (un archivo por agente, con rol, dominio, responsabilidades y límites declarados de forma estructurada) y, además, derivar la versión nativa del CLI en uso cuando este soporte agentes.
- **FR-005**: La re-ejecución MUST ser idempotente: detectar agentes existentes por rol/dominio (no solo por nombre), no duplicarlos, no pisar ediciones manuales, y proponer solo los faltantes.
- **FR-006**: Ante un cambio de objetivo que deje agentes sin dominio, el sistema MUST reportarlos como huérfanos y sugerir su archivo, sin borrarlos automáticamente.

**README del proyecto**

- **FR-007**: La skill de README MUST crear `README.md` si no existe, detallando: objetivo del proyecto, alcance (qué es y qué no es), y estado actual, derivados de las fuentes disponibles o declarados por el usuario.
- **FR-008**: Las secciones gestionadas por la skill MUST estar delimitadas de forma visible en el archivo; una re-ejecución MUST actualizar solo esas secciones y MUST preservar el 100% del contenido manual.
- **FR-009**: Sobre un README preexistente sin delimitadores, la skill MUST proponer la inserción de las secciones gestionadas y pedir confirmación antes del primer cambio.
- **FR-010**: Cada actualización de secciones gestionadas MUST registrar la fecha de última actualización dentro del README.

**Integración y compatibilidad**

- **FR-011**: Ambas capacidades MUST ser invocables manualmente en cualquier momento, de forma independiente entre sí.
- **FR-012**: El ofrecimiento post-constitution se materializa con una skill envoltorio (`constitution-plus`) que ejecuta la fase constitution base completa (sin modificarla) y al terminar ofrece correr el especificador (opcional, no bloqueante). En los pipelines de este proyecto, cuando la idea fue clasificada compleja, el mismo ofrecimiento MUST hacerse al completar la fase specify. En todos los casos el análisis de cobertura es a nivel PROYECTO (la feature nueva puede revelar dominios nuevos del proyecto, pero los agentes cubren al proyecto, no a una feature puntual).
- **FR-013**: Todo lo agregado MUST ser estrictamente aditivo sobre spec-kit (Constitución I): ningún comando ni artefacto base cambia de comportamiento; las skills nuevas MUST funcionar desde cualquier CLI principal (Constitución II).

### Key Entities

- **Objetivo del proyecto**: la declaración de qué se construye y para qué; tiene una fuente (constitución > README > specs > declaración del usuario) y puede cambiar en el tiempo.
- **Dominio de necesidad**: un área del proyecto que requiere cobertura especializada; se evalúa contra la taxonomía base fija (interfaz/frontend, servicios/backend, datos, pruebas, documentación, seguridad, infraestructura/despliegue, integración con terceros) más los dominios extra que el objetivo justifique (Clarificación S3).
- **Definición de agente**: nombre, rol, dominio cubierto, responsabilidades, límites; existe en formato portable y opcionalmente en el formato nativo del CLI; distingue origen (generada vs. editada a mano).
- **Propuesta de cobertura**: el conjunto de agentes sugeridos con su justificación por dominio; requiere confirmación del usuario antes de materializarse.
- **README gestionado**: el `README.md` con secciones delimitadas que la skill mantiene (objetivo, alcance, estado, fecha) conviviendo con secciones manuales intocables.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tras correr el especificador en un proyecto con objetivo declarado, el 100% de los dominios de necesidad identificables en el objetivo tienen al menos un agente propuesto o uno existente reconocido como cobertura.
- **SC-002**: Un usuario obtiene su conjunto de agentes definido y aprobado en menos de 10 minutos, sin escribir ninguna definición a mano.
- **SC-003**: En re-ejecuciones, el 100% de las definiciones editadas a mano y del contenido manual del README sobreviven sin cambios.
- **SC-004**: Cero duplicados: re-correr el especificador N veces sobre el mismo objetivo no genera ningún agente repetido (mismo dominio y rol).
- **SC-005**: Un proyecto que adopta la skill de README mantiene el objetivo visible y actualizado: tras cada corrida, la sección de objetivo refleja la fuente vigente y muestra fecha de actualización.
- **SC-006**: Los comandos base de spec-kit se comportan exactamente igual con las skills instaladas (100% compatibilidad hacia atrás).

## Assumptions

- Las definiciones de agentes viven en `.specify/agents/<nombre>.md` (formato portable,
  un archivo por agente — Clarificación S2), con generación adicional en el formato
  nativo del CLI en uso cuando exista soporte (p. ej. subagentes del CLI principal).
- "Cubrir todas las necesidades" se interpreta como cobertura por dominios derivados
  del objetivo y stack declarado — no como garantía de completitud absoluta; el
  usuario puede agregar dominios manualmente en la confirmación.
- El ofrecimiento automático (US3) se integra en las skills/pipelines de este
  proyecto (constitution y specify/triage) de forma aditiva, sin modificar el
  comportamiento del spec-kit original cuando el usuario declina.
- La skill de README gestiona el README raíz del proyecto; documentación adicional
  queda fuera de alcance.
- El idioma de los artefactos generados sigue el idioma del proyecto (detectado de la
  constitución/README existentes o preguntado la primera vez).
