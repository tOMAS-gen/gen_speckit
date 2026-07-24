# Feature Specification: Despacho multi-modelo de todas las fases

**Feature Branch**: `008-multi-model-phase-dispatch`

**Created**: 2026-07-22

**Status**: Draft

**Input**: User description: "Algunos agentes (Claude Code, OpenCode, Hermes) permiten tener varios modelos en el mismo agente. El sistema debería tener la opción de analizar los modelos disponibles por agente y usar un modelo orquestador para repartir las tareas de cada paso y de cada implementación — no solamente la implementación sino todos los pasos."

## Clarifications

### Session 2026-07-22

- Q: ¿Cuándo se activa el despacho de fases? → A: Por defecto cuando existe `.specify/models.json` válido; sin inventario → modo clásico automático (todas las fases en el principal).
- Q: ¿Quién ejecuta las fases de criterio (clarify, etc.) y quién decide el modelo? → A: El orquestador decide el modelo de cada paso a partir del inventario (`models.json`); las fases de criterio van a un modelo muy capaz (ej. opus, k3, gpt-5.6-sol) — el modelo asignado hace el trabajo analítico completo de la fase (incluida la integración de respuestas); el principal solo conduce la conversación con el usuario y verifica.
- Q: ¿Cómo participa el usuario en el uso de sus modelos/agentes? → A: Es configurable por el cliente: puede elegir qué agentes participan y qué modelos de cada agente se usan (ej. OpenCode con todos sus modelos en el mismo agente); la configuración del usuario prevalece sobre la asignación automática.
- Q: ¿OpenCode y Hermes se incluyen registrados en el catálogo? → A: No — esta feature entrega solo la capacidad genérica de registrar agentes multi-modelo vía datos; el usuario registra OpenCode/Hermes después con el flujo de registro de CLIs existente.
- Q: ¿Cómo configura el cliente qué agentes/modelos usar? → A: Ambas vías: campo de habilitado/deshabilitado editable a mano en el inventario + gestión desde la skill de configuración de CLIs; la edición manual siempre prevalece. Además el usuario puede elegir explícitamente un CLI/agente concreto como preferido para el trabajo si así lo desea.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Repartir todas las fases entre modelos, no solo implement (Priority: P1)

Hoy el triage decide qué modelo debería ejecutar cada fase (specify, clarify, plan,
checklist, tasks, analyze) y lo registra en el reporte, pero en la práctica todas las
fases las ejecuta el modelo principal en su propia sesión ("modo decisión-solo"): el
único reparto real ocurre en implement, tarea por tarea. El usuario quiere que ese
reparto sea real también para las fases: cuando el triage asigna una fase a un modelo
económico, esa fase debe **ejecutarse efectivamente** en ese modelo vía headless, y el
principal debe verificar el artefacto producido antes de continuar el pipeline.

**Why this priority**: es el pedido central de la feature y la materialización del
principio "el más barato que alcance" en la mitad del pipeline que hoy consume cuota
cara sin necesidad. Sin esto, la tabla "Modelos por fase" del reporte es decorativa.

**Independent Test**: correr un pipeline auto con un inventario válido donde el triage
asigne al menos una fase a un modelo distinto del principal; verificar que esa fase se
despachó por headless (queda log del despacho), que el artefacto resultante existe y
cumple su template, y que el reporte registra la fase como ejecutada por el modelo
asignado.

**Acceptance Scenarios**:

1. **Given** un pipeline IDEAL con triage que asigna la fase checklist a un modelo
   económico distinto del principal, **When** el pipeline llega a esa fase, **Then** la
   fase se ejecuta en el modelo asignado vía headless, el principal valida el artefacto
   producido y el reporte registra la fase como `ejecutada` con el modelo que la corrió.
2. **Given** una fase despachada cuyo artefacto vuelve incompleto o no cumple el
   template, **When** el principal lo verifica, **Then** se aplica el ciclo acotado de
   recuperación (reintento al mismo modelo con el motivo; luego escalada al siguiente
   candidato de mayor capacidad; luego ejecutar la fase en el principal) y el pipeline
   nunca continúa sobre un artefacto inválido.
3. **Given** un modelo de fase que agota su cuota a mitad del pipeline, **When** el
   despacho falla por cuota, **Then** el sistema registra la cuota agotada, reasigna la
   fase al siguiente candidato del ranking y lo anota en Eventos, sin frenar el pipeline
   ni pedir intervención del usuario.
4. **Given** una fase que requiere interacción con el usuario (preguntas de clarify,
   hallazgos críticos de analyze, gates), **When** esa fase se despacha a un secundario,
   **Then** el secundario hace el trabajo analítico completo (genera las preguntas y,
   con las respuestas del usuario, integra los cambios al artefacto), mientras que la
   conversación con el usuario la conduce siempre el principal en su sesión.

---

### User Story 2 - Inventariar los modelos disponibles dentro de cada agente (Priority: P2)

Agentes como Claude Code, OpenCode o Hermes permiten elegir entre varios modelos dentro
del mismo agente (incluso modelos de distintos proveedores). El usuario quiere que el
inventario analice y registre qué modelos ofrece cada agente instalado — no solo los
tres CLIs históricos — de modo que el reparto de fases y tareas pueda elegir el modelo
concreto dentro del agente, con su capacidad, costo y contexto comparables.

**Why this priority**: sin un inventario por-modelo de cada agente, el orquestador no
puede repartir con precisión: vería "OpenCode" como una caja negra en vez de ver los
modelos económicos y caros que expone. Es el habilitador del reparto fino de la US1,
pero la US1 ya funciona con el inventario actual de tres CLIs.

**Independent Test**: registrar un agente multi-modelo (p. ej. OpenCode) en el
inventario; verificar que la detección lista sus modelos disponibles con capacidad,
costo y contexto (detectados o declarados), que cada modelo aparece en los rankings de
asignación, y que el comando headless del agente permite seleccionar el modelo concreto.

**Acceptance Scenarios**:

1. **Given** un agente instalado que expone varios modelos, **When** el usuario genera o
   actualiza el inventario, **Then** el inventario lista cada modelo del agente como
   candidato individual (`agente/modelo`) con capacidad, costo y contexto, y los
   rankings de asignación los ordenan junto a los modelos de los demás agentes.
2. **Given** un agente cuyo mecanismo de selección de modelo es conocido por el
   catálogo, **When** el orquestador despacha una fase o tarea a `agente/modelo`,
   **Then** la invocación headless selecciona ese modelo concreto y no el modelo por
   defecto del agente.
3. **Given** un agente multi-modelo cuyos modelos no se pueden detectar
   automáticamente, **When** se genera el inventario, **Then** el sistema pide la
   declaración del usuario para ese agente (o marca lo no detectable como desconocido)
   y nunca inventa modelos.

---

### User Story 3 - Ver el reparto real de todo el pipeline (Priority: P3)

El usuario quiere que el reporte de orquestación refleje el reparto completo: qué
modelo ejecutó efectivamente cada fase (no solo la intención del triage), qué
fallbacks hubo, y qué porcentaje del pipeline completo (fases + tareas) corrió en
modelos económicos.

**Why this priority**: cierra el ciclo de transparencia y permite medir el ahorro real
que la feature promete; es valioso pero no bloquea el reparto en sí.

**Independent Test**: al terminar un pipeline con fases despachadas, revisar el reporte
y verificar que cada fila de "Modelos por fase" registra el modelo que realmente
ejecutó la fase (incluyendo reasignaciones) y que Métricas incluye el porcentaje de
fases + tareas ejecutadas por modelos económicos.

**Acceptance Scenarios**:

1. **Given** un pipeline terminado donde una fase fue reasignada por cuota, **When** el
   usuario lee el reporte, **Then** la tabla "Modelos por fase" muestra el modelo final
   que la ejecutó y Eventos registra la reasignación con su causa.
2. **Given** un pipeline terminado, **When** el usuario lee Métricas, **Then** encuentra
   el desglose de fases por modelo y el porcentaje del trabajo total (fases y tareas)
   que corrió en modelos económicos.

---

### Edge Cases

- ¿Qué pasa si el artefacto de una fase despachada vuelve válido en formato pero
  incoherente con la idea (p. ej. un spec de otra cosa)? La verificación del principal
  incluye revisión de contenido contra la entrada de la fase, no solo estructura.
- ¿Qué pasa si ningún candidato del ranking puede ejecutar una fase (todos sin cuota)?
  La fase la ejecuta el principal en su sesión (el pipeline nunca queda bloqueado por
  el reparto de fases) y el evento queda registrado.
- ¿Qué pasa si el prompt de despacho de una fase excede los límites de línea de
  comandos de la plataforma? El mecanismo de despacho debe transferir las instrucciones
  largas por archivo, no por argumento (limitación ya observada en Windows).
- ¿Qué pasa con un agente registrado cuyo comando headless no permite seleccionar
  modelo? El agente participa como candidato de un solo modelo efectivo (su default) y
  el inventario lo refleja, sin excluirlo.
- ¿Qué pasa si el principal es a la vez el modelo asignado a la fase? La ejecuta en su
  propia sesión, nunca se auto-invoca por headless (regla existente).
- ¿Qué pasa si el usuario editó a mano la tabla "Modelos por fase" del reporte antes de
  correr el pipeline? La edición manual prevalece sobre la asignación del triage (regla
  existente de precedencia de ediciones del usuario).
- ¿Qué pasa si el usuario deshabilita tantos modelos que un nivel del ranking queda
  vacío, o restringe el trabajo a un solo agente sin cuota? El sistema informa la
  restricción activa, usa los candidatos habilitados restantes y, si no queda ninguno,
  las fases las ejecuta el principal y las tareas quedan `pendiente_bloqueada` con
  indicación clara de que la causa es la configuración del usuario.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE poder ejecutar cada fase no interactiva del pipeline
  (specify, plan, checklist, tasks, analyze — y las equivalentes del flujo ECO) en el
  modelo asignado por el triage, invocándolo en modo headless cuando el modelo asignado
  no es el principal.
- **FR-002**: El principal DEBE verificar el artefacto producido por cada fase
  despachada antes de continuar: estructura conforme al template de la fase y contenido
  coherente con la entrada. Una fase solo se marca `ejecutada` tras esa verificación.
- **FR-003**: Ante una fase despachada que falla (artefacto inválido, error del
  agente), el sistema DEBE aplicar un ciclo acotado: 1 reintento al mismo modelo con el
  motivo del rechazo → 1 escalada al siguiente candidato de mayor capacidad → ejecución
  de la fase por el principal. El pipeline NUNCA continúa sobre un artefacto inválido y
  NUNCA queda bloqueado por el reparto de fases.
- **FR-004**: Ante agotamiento de cuota del modelo de una fase, el sistema DEBE
  registrar el estado de cuota (mecanismo existente), reasignar la fase al siguiente
  candidato del ranking correspondiente y registrar el evento, sin intervención del
  usuario.
- **FR-005**: Las interacciones con el usuario (preguntas de clarificación, hallazgos
  críticos, gates de confirmación) DEBEN ocurrir siempre en la sesión del principal.
  El modelo asignado a la fase hace el trabajo analítico completo: genera las
  preguntas/hallazgos como artefacto y, tras la conversación del principal con el
  usuario, recibe las respuestas e integra los cambios en el artefacto de la fase. El
  principal solo conduce la conversación y verifica el resultado.
- **FR-005a**: Las fases de criterio (clarify, analyze, y el paso de asignación de
  tasks) DEBEN asignarse a un modelo de alta capacidad del ranking (ej. los candidatos
  de `asignacion.alta`): equivocarse en el análisis es caro. Las fases de producción
  mecánica pueden ir a modelos económicos según decida el orquestador.
- **FR-006**: El inventario DEBE poder registrar agentes que exponen múltiples modelos
  (p. ej. Claude Code, OpenCode, Hermes), listando cada modelo como candidato
  individual `agente/modelo` con capacidad, costo y ventana de contexto comparables
  entre agentes.
- **FR-007**: La generación del inventario DEBE analizar los modelos disponibles por
  agente instalado: detectar automáticamente lo detectable (modelos configurados,
  mecanismo de selección) y pedir declaración del usuario para lo no detectable. El
  sistema NUNCA inventa modelos ni capacidades.
- **FR-008**: El comando headless de cada agente en el inventario DEBE poder
  parametrizar el modelo concreto a usar; si un agente no permite seleccionar modelo,
  participa con su modelo por defecto como único candidato, sin ser excluido.
- **FR-008a**: El usuario DEBE poder configurar cómo se usan sus agentes y modelos por
  dos vías equivalentes: (a) editando a mano un campo de habilitado/deshabilitado en el
  inventario, y (b) gestionándolo desde la skill de configuración de CLIs existente. Se
  puede habilitar/deshabilitar un agente completo o modelos individuales dentro de un
  agente (ej. usar OpenCode con todos sus modelos, o solo con algunos). La edición
  manual siempre prevalece y los modelos deshabilitados no reciben fases ni tareas.
  Las tareas pendientes que ya estaban etiquetadas con un modelo luego deshabilitado
  se tratan como etiquetas inválidas al momento del despacho: se reasignan al
  siguiente candidato habilitado de su nivel, con advertencia al usuario en el
  momento de deshabilitar si existen tales tareas.
- **FR-008b**: El usuario DEBE poder designar explícitamente un agente o CLI concreto
  como preferido para el trabajo (ej. "usar solo este CLI"): en ese caso el orquestador
  reparte fases y tareas únicamente entre los modelos habilitados de ese agente,
  registrando en el reporte que la restricción es una decisión del usuario.
- **FR-009**: El despacho de fases DEBE reutilizar el mecanismo de invocación de
  secundarios existente (mismo script, mismos contratos de log y clasificación de
  resultados), extendiéndolo solo donde haga falta (p. ej. instrucciones largas por
  archivo), sin crear un canal de despacho paralelo.
- **FR-010**: El reporte de orquestación DEBE registrar por fase el modelo que
  efectivamente la ejecutó (incluyendo reasignaciones), los eventos de fallback, y en
  Métricas el desglose de fases por modelo y el porcentaje del trabajo total (fases +
  tareas) ejecutado por modelos económicos (costo < 3, la definición vigente del
  reporte de orquestación).
- **FR-011**: El reparto de fases DEBE respetar las reglas existentes: el principal
  nunca se auto-invoca por headless; solo el principal escribe artefactos de estado
  (`tasks.md`, reporte); los secundarios no operan fuera del repositorio; las ediciones
  manuales del usuario prevalecen.
- **FR-012**: El pipeline con despacho de fases DEBE seguir siendo retomable: si se
  interrumpe, al retomar se reconstruye el estado desde los artefactos y el reporte, y
  solo se ejecutan las fases faltantes, con su asignación vigente.
- **FR-013**: El despacho de fases DEBE activarse por defecto cuando existe un
  inventario (`.specify/models.json`) válido, sin configuración adicional. Sin
  inventario válido — o si el usuario pide explícitamente el modo clásico — el pipeline
  se comporta exactamente como hoy (todas las fases en el principal).

### Key Entities

- **Agente (CLI multi-modelo)**: herramienta de IA instalada que expone uno o más
  modelos seleccionables; atributos: identidad, autenticación, comando headless
  parametrizable por modelo, lista de modelos.
- **Modelo de agente**: candidato individual de ejecución (`agente/modelo`) con
  capacidad, costo, ventana de contexto y estado de cuota; unidad real del reparto.
- **Asignación de fase**: vínculo entre una fase del pipeline y el modelo que debe
  ejecutarla; tiene estado (pendiente, ejecutada, omitida) y modelo final efectivo
  (puede diferir del asignado por fallback).
- **Despacho de fase**: ejecución headless de una fase en un secundario; produce un
  artefacto verificable, logs y una clasificación de resultado (éxito, cuota agotada,
  indisponible).
- **Reporte de orquestación**: registro por feature del triage, modelos por fase
  (asignado y efectivo), asignaciones por tarea, eventos y métricas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En un pipeline completo con inventario válido, al menos el 50% de las
  fases no interactivas se ejecutan en modelos distintos del principal (medible por el
  reporte y los logs de despacho).
- **SC-002**: El 100% de las fases despachadas que el pipeline dio por buenas tienen un
  artefacto que pasa la verificación del principal; ningún pipeline continúa sobre un
  artefacto inválido.
- **SC-003**: Un agente multi-modelo nuevo (p. ej. OpenCode) puede registrarse con sus
  modelos y recibir fases o tareas en el mismo ciclo, sin modificar código — solo
  datos de inventario/catálogo.
- **SC-004**: El consumo del modelo más caro en las fases de planificación se reduce
  respecto del baseline actual (todas las fases en el principal), medible comparando el
  desglose de fases por modelo del reporte con la tabla de asignación del triage.
- **SC-005**: Un pipeline interrumpido tras al menos una fase despachada se retoma
  ejecutando solo las fases faltantes, sin rehacer ninguna fase ya verificada.
- **SC-006**: Ante el agotamiento de cuota de un modelo de fase, el pipeline termina
  igual (con fallback registrado) sin intervención del usuario, en el 100% de los
  casos en que exista al menos un candidato con cuota o el principal disponible.

## Assumptions

- El "modelo orquestador" del pedido es el rol de **principal** ya definido en la
  constitución: el modelo más capaz disponible dirige el reparto y la verificación; no
  se introduce un rol nuevo.
- Las fases interactivas no se despachan completas: la interacción con el usuario es
  siempre del principal (FR-005); lo despachable es la producción del artefacto y el
  análisis.
- Los agentes objetivo son los registrables vía el catálogo de CLIs existente
  (feature 003). Registrar OpenCode/Hermes concretos queda fuera del alcance: esta
  feature entrega la capacidad genérica (agente multi-modelo por datos) y el usuario
  los registra con el flujo de registro existente. OpenCode puede usarse como caso de
  validación manual, sin quedar incluido en el catálogo versionado.
- La selección de modelo dentro de un agente se hace por línea de comandos en su modo
  headless (como ya ocurre con los tres CLIs actuales); agentes sin esa opción
  participan con su modelo por defecto.
- La capacidad y el costo de los modelos nuevos se obtienen por el mecanismo de
  clasificación existente (feature 007) o por declaración del usuario; esta feature no
  cambia cómo se puntúa.
- El reparto por fases reutiliza los rankings existentes del inventario
  (`asignacion` / `asignacion_por_fase` cuando exista); esta feature consume esas
  listas, no redefine su cálculo.
