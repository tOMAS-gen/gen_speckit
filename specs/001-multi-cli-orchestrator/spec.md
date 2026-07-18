# Feature Specification: Orquestador Multi-CLI para Spec Kit

**Feature Branch**: `001-multi-cli-orchestrator`

**Created**: 2026-07-17

**Status**: Draft

**Input**: User description: "@README.md — Mejorar el Spec Kit de GitHub con un orquestador multi-CLI (Claude, Codex y Kimi) que analiza la complejidad de la idea y de cada tarea, y despacha el trabajo al modelo más conveniente para reducir el costo y el uso de cada implementación."

## Clarifications

### Session 2026-07-17

- Q: ¿Qué constituye una tarea "verificada" para que el principal la marque `[X]`? → A: Verificación estándar: el principal revisa que el diff cumpla lo que la tarea describe y ejecuta las validaciones existentes del proyecto (tests/build si los hay).
- Q: ¿Con qué permisos corren los CLIs secundarios invocados en modo headless? → A: Permisos totales de edición dentro del repositorio (modo sin confirmaciones), con la verificación posterior del principal como control.
- Q: ¿Dónde se registra el agotamiento de cuota detectado en tiempo de ejecución? → A: Se persiste en `models.json` (campo `cuota` con marca de tiempo); las corridas futuras lo respetan hasta que venza la ventana del plan o el usuario lo resetee.
- Q: ¿Cuántos reintentos ante un fallo de invocación headless no atribuible a cuota? → A: 1 reintento; si vuelve a fallar, se trata como indisponibilidad y se aplica el fallback al siguiente candidato.
- Q: ¿Qué forma toma el reporte de orquestación? → A: Ambas: resumen en consola al final de cada fase + archivo persistente en el directorio de la feature, actualizado en cada fase (triage, asignación, implementación).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inventario de recursos disponibles (Priority: P1)

Como usuario, ejecuto una sola vez `/speckit-models` y obtengo un inventario de los CLIs
instalados en mi máquina (Claude, Codex, Kimi), con sus modelos, capacidad relativa,
costo, ventana de contexto y modo de invocación headless, más los datos que yo declaro
(plan contratado, cuotas). El resultado queda en `.specify/models.json` como ranking
ordenado por complejidad, que puedo corregir a mano.

**Why this priority**: es la fundación de todo el sistema — sin inventario no hay
triage, asignación ni orquestación. Es independiente y entrega valor propio (visibilidad
de recursos).

**Independent Test**: en una máquina con al menos un CLI instalado, ejecutar
`/speckit-models` y verificar que `.specify/models.json` existe, refleja los CLIs
realmente instalados, contiene el ranking `asignacion` por complejidad, y que una
corrección manual del usuario sobrevive (no es pisada) a una re-ejecución.

**Acceptance Scenarios**:

1. **Given** una máquina con los tres CLIs instalados y autenticados, **When** ejecuto `/speckit-models`, **Then** `models.json` lista los tres con `instalado: true`, su comando headless y al menos un modelo cada uno con capacidad, costo y contexto.
2. **Given** una máquina donde falta un CLI (p. ej. Kimi no instalado), **When** ejecuto `/speckit-models`, **Then** el CLI faltante figura como no instalado, no aparece en las listas de `asignacion`, y el comando termina sin error.
3. **Given** un dato no detectable automáticamente (plan contratado, cuota), **When** el escaneo lo encuentra, **Then** me lo pregunta o lo marca como desconocido, sin inventar valores.
4. **Given** un `models.json` corregido a mano por el usuario, **When** re-ejecuto `/speckit-models`, **Then** las correcciones manuales prevalecen o se me pregunta antes de sobrescribirlas.

---

### User Story 2 - Triage de la idea y elección del flujo (Priority: P1)

Como usuario, escribo mi idea en cualquiera de los tres CLIs con una sola invocación.
Antes de ejecutar nada, el sistema evalúa la complejidad de la idea (alcance,
ambigüedad, riesgo), decide qué flujo usar (ECO de 4 fases o IDEAL de 7 fases) y qué
modelo ejecuta cada fase. El triage se autoevalúa: si escribí una idea compleja en un
CLI económico, escala la planificación a un modelo superior; si escribí una idea simple
en un CLI caro, degrada el trabajo a modelos económicos.

**Why this priority**: es el corazón del contrato "solo pongo la idea" — junto con
US1 forma el MVP mínimo que ya decide y ahorra, incluso despachando a los pipelines
existentes.

**Independent Test**: con un `models.json` válido, invocar el pipeline con una idea
simple y con una idea compleja, y verificar que el reporte de triage clasifica cada una,
recomienda el flujo correcto y asigna modelos por fase, sin haber ejecutado ninguna fase
todavía.

**Acceptance Scenarios**:

1. **Given** una idea simple invocada con el flujo IDEAL sin `-bypass`, **When** el triage detecta la discordancia, **Then** me pregunta si cambiar al flujo ECO antes de continuar.
2. **Given** una idea simple invocada con el flujo IDEAL con `-bypass`, **When** el triage detecta la discordancia, **Then** cambia solo al flujo ECO y lo informa en el reporte.
3. **Given** una idea compleja escrita en el CLI más económico, **When** corre el triage, **Then** la planificación se escala a un modelo superior y el CLI de entrada queda como secundario/despachador, informándolo en el reporte.
4. **Given** una idea simple escrita en el CLI más caro, **When** corre el triage, **Then** las fases se degradan a modelos económicos y el reporte lo explica.

---

### User Story 3 - Pipeline económico de una sola llamada (Priority: P2)

Como usuario con una feature chica o un prototipo, invoco el flujo ECO y el sistema
ejecuta solo el ciclo mínimo (specify → plan → tasks → gate → implement), frenándose
únicamente ante dudas reales o el gate previo a implementar. Con `-bypass`, si no hay
dudas pendientes, implementa directo. Si el proceso se corta, al reinvocar detecta los
artefactos existentes y ofrece continuar desde la fase faltante.

**Why this priority**: completa la pareja de pipelines (el IDEAL ya existe) y habilita
el ahorro en el caso más frecuente: ideas chicas y claras.

**Independent Test**: invocar el flujo ECO con una idea clara y verificar que genera
spec, plan y tasks encadenados sin intervención, se detiene en el gate, y con `-bypass`
llega hasta implementar sin pausas; interrumpirlo y reinvocarlo para verificar que
retoma desde la fase faltante.

**Acceptance Scenarios**:

1. **Given** una idea clara, **When** invoco el flujo ECO sin flags, **Then** se ejecutan specify, plan y tasks sin intervención y el sistema se detiene en el gate previo a implement.
2. **Given** una idea clara, **When** invoco el flujo ECO con `-bypass` y no surgen dudas, **Then** el pipeline llega hasta la implementación sin esperar confirmación.
3. **Given** un pipeline interrumpido después de plan, **When** lo reinvoco, **Then** detecta spec y plan existentes y ofrece continuar desde tasks.
4. **Given** el flag `--sin-implementar`, **When** el pipeline termina la planificación, **Then** se detiene sin ejecutar la implementación.

---

### User Story 4 - Clasificación y asignación de tareas (Priority: P2)

Como usuario, al final de la fase tasks el modelo más capaz disponible clasifica la
complejidad de cada tarea (`[C:baja|media|alta]`) y le asigna el modelo que se hará
cargo (`[M:cli/modelo]`) consultando el ranking, sin excluir a ningún modelo disponible.
Las etiquetas quedan inline en `tasks.md` y puedo editarlas a mano antes de implementar.

**Why this priority**: es el reparto que materializa el ahorro; depende de US1 (ranking)
pero se prueba solo con un `tasks.md` cualquiera.

**Independent Test**: con un `tasks.md` generado y un `models.json` válido, correr el
asignador y verificar que cada tarea tiene exactamente una etiqueta `[C:]` y una `[M:]`,
que el formato oficial de spec-kit quedó intacto y que las asignaciones respetan el
ranking.

**Acceptance Scenarios**:

1. **Given** un `tasks.md` recién generado, **When** corre el asignador, **Then** cada tarea queda con `[C:baja|media|alta]` y `[M:cli/modelo]` inline, y el formato oficial (checkbox, `T###`, `[P]`, `[US#]`, ruta) no cambia.
2. **Given** un ranking con tres CLIs disponibles, **When** se asignan las tareas de una feature mixta, **Then** todos los CLIs disponibles reciben tareas acordes a su capacidad (ninguno queda excluido).
3. **Given** una tarea de complejidad baja, **When** se asigna el modelo, **Then** recibe el modelo más económico cuya capacidad y contexto alcanzan, no el más capaz.
4. **Given** etiquetas editadas a mano por el usuario, **When** arranca la implementación, **Then** se respetan las etiquetas editadas sin re-asignar.

---

### User Story 5 - Orquestación de la implementación (Priority: P3)

Como usuario, en la fase implement el CLI principal lee `tasks.md` con las asignaciones
y despacha cada tarea al CLI/modelo asignado por línea de comandos, ejecutando en
paralelo las tareas marcadas `[P]` y respetando dependencias. Si un modelo agota su
cuota, escala al siguiente del ranking sin frenar el proceso. El principal integra los
resultados, verifica y marca `[X]` cada tarea completada.

**Why this priority**: es la fase final del circuito; requiere US1 y US4 pero entrega
el ahorro real medible.

**Independent Test**: con un `tasks.md` etiquetado y al menos dos CLIs disponibles,
correr la orquestación y verificar que cada tarea fue ejecutada por el CLI asignado
(o su fallback), que las `[P]` corrieron en paralelo y que al final todas quedaron
marcadas `[X]` con el trabajo integrado.

**Acceptance Scenarios**:

1. **Given** un `tasks.md` con asignaciones a dos CLIs distintos, **When** corre la orquestación, **Then** cada tarea es ejecutada por su CLI asignado vía invocación headless y queda marcada `[X]` al completarse y verificarse.
2. **Given** tareas marcadas `[P]` con el mismo modelo asignado o modelos distintos, **When** se despachan, **Then** corren en paralelo respetando las dependencias declaradas.
3. **Given** un modelo que agota su cuota a mitad de la ejecución, **When** el orquestador detecta el fallo por cuota, **Then** reintenta la tarea con el siguiente candidato del ranking y lo registra en el reporte, sin intervención del usuario.
4. **Given** una tarea cuyo resultado no pasa la verificación del principal, **When** se integra el trabajo, **Then** la tarea no se marca `[X]` y se reporta para corrección (reintento o escalada).
5. **Given** el orquestador corriendo desde cualquiera de los tres CLIs como principal, **When** ejecuto el mismo flujo, **Then** el comportamiento es equivalente (portabilidad).

---

### User Story 6 - Instalación compatible con spec-kit (Priority: P4)

Como usuario nuevo, instalo este repositorio con el mismo gesto que el spec-kit
original y obtengo todo lo que spec-kit ya hacía más las mejoras multi-CLI, sin
aprender comandos nuevos obligatorios.

**Why this priority**: es la vía de distribución; el valor funcional ya existe sin
ella para el desarrollo local.

**Independent Test**: en un proyecto limpio, instalar desde este repositorio e
inicializar; verificar que las skills base de spec-kit funcionan igual que las
originales y que las skills nuevas están disponibles.

**Acceptance Scenarios**:

1. **Given** un proyecto vacío, **When** instalo desde este repo e inicializo, **Then** obtengo la estructura `.specify/` estándar, las skills base originales y las skills nuevas (pipelines, models, orquestador).
2. **Given** un usuario que solo usa los comandos originales de spec-kit, **When** trabaja en un proyecto inicializado desde este repo, **Then** todo funciona exactamente igual que con el spec-kit original.

---

### Edge Cases

- ¿Qué pasa si no existe `.specify/models.json` al invocar un pipeline? El sistema lo
  indica y ofrece correr `/speckit-models` antes de continuar; no inventa un ranking.
- ¿Qué pasa si solo hay un CLI instalado? Todo el flujo funciona en modo degradado con
  ese único CLI (el reparto es trivial) y el reporte lo aclara.
- ¿Qué pasa si todos los candidatos de un nivel de complejidad agotaron su cuota? El
  orquestador escala a los candidatos de niveles superiores; si no queda ninguno,
  pausa y reporta qué tareas quedaron pendientes y por qué.
- ¿Qué pasa si una invocación headless a un CLI secundario falla por razones ajenas a
  la cuota (error de red, CLI desactualizado, sesión expirada)? Se reintenta exactamente
  1 vez; si vuelve a fallar, se trata como indisponibilidad: fallback al siguiente del
  ranking y registro en el reporte.
- ¿Qué pasa si dos tareas `[P]` asignadas a CLIs distintos tocan el mismo archivo?
  El orquestador debe detectar el conflicto (por las rutas declaradas en las tareas) y
  serializarlas aunque estén marcadas `[P]`.
- ¿Qué pasa si el usuario edita `tasks.md` con una etiqueta inválida (modelo
  inexistente o CLI no instalado)? El orquestador lo detecta antes de despachar y
  pide corrección o aplica el fallback del ranking, informándolo.
- ¿Qué pasa si la cuota declarada está desactualizada y el modelo preferido rechaza el
  trabajo? Se trata como agotamiento de cuota: fallback automático y actualización del
  estado en el inventario.
- ¿Qué pasa con las tareas en ejecución cuando el orquestador pausa por falta total de
  candidatos? Se espera a que terminen, se verifican normalmente, y solo las tareas aún
  no despachadas quedan pendientes-bloqueadas en el reporte.
- ¿Qué pasa si el CLI principal agota su propia cuota a mitad de la orquestación?
  Pausa ordenada: persiste el estado en el reporte y `tasks.md`, e indica al usuario
  cómo retomar desde otro CLI como principal (la corrida es retomable per FR-012).
- ¿Qué pasa si `.specify/models.json` existe pero es inválido (no cumple el esquema)?
  Se trata igual que si faltara: se informa el problema concreto y se ofrece corregirlo
  o regenerarlo con `/speckit-models`; nunca se opera con un inventario corrupto.
- ¿Qué pasa si el usuario re-genera `tasks.md` (p. ej. re-ejecuta `/speckit-tasks`)
  después de la asignación? Las etiquetas previas se pierden con el archivo nuevo: el
  sistema lo advierte, y la asignación debe re-ejecutarse antes de implementar.
- ¿Qué pasa al retomar si un artefacto existente está incompleto o corrupto (p. ej.
  una spec a medio escribir)? Se trata como faltante: se ofrece regenerarlo desde esa
  fase, nunca continuar en silencio sobre un artefacto inválido.

## Requirements *(mandatory)*

### Functional Requirements

**Inventario de recursos**

- **FR-001**: El sistema MUST detectar automáticamente, por cada CLI soportado (Claude, Codex, Kimi): si está instalado, su versión, si está autenticado, su comando de invocación headless y los modelos que expone.
- **FR-002**: El sistema MUST solicitar al usuario los datos no detectables (plan contratado, cuotas/límites, ventana de contexto cuando no se pueda obtener) y MUST marcar como desconocido lo que el usuario no declare, sin inventar valores.
- **FR-003**: El sistema MUST producir un inventario persistente (`.specify/models.json`) con capacidad relativa (1–10), costo relativo (1–3) y contexto por modelo, y una lista ordenada de candidatos (`asignacion`) por cada nivel de complejidad (alta/media/baja).
- **FR-004**: El inventario MUST ser corregible a mano por el usuario y las correcciones manuales MUST prevalecer sobre valores detectados en re-ejecuciones (o mediar confirmación explícita antes de pisarlas).

**Triage**

- **FR-005**: El sistema MUST evaluar la complejidad de la idea (alcance, ambigüedad, riesgo) antes de ejecutar cualquier fase, clasificándola como simple, media o compleja. La clasificación MUST seguir una rúbrica documentada con indicadores observables (cantidad de componentes/sistemas tocados, claridad de los criterios de éxito, riesgo de datos o integraciones) para que ideas equivalentes reciban clasificaciones equivalentes.
- **FR-006**: El triage MUST ser ejecutado por el modelo más capaz disponible y MUST decidir el flujo (ECO o IDEAL) y qué modelo ejecuta cada fase del pipeline.
- **FR-007**: El triage MUST autoevaluarse respecto del punto de entrada: escalar la planificación a un modelo superior si la idea excede la capacidad del CLI actual, o degradarla a modelos económicos si la idea es trivial para el CLI actual, informándolo en el reporte.
- **FR-008**: Ante discordancia entre el flujo invocado y el recomendado, el sistema MUST preguntar al usuario si cambiar (sin `-bypass`) o cambiar automáticamente e informarlo (con `-bypass`).

**Pipelines**

- **FR-009**: El sistema MUST ofrecer un flujo ECO de una sola llamada con el ciclo mínimo (specify → plan → tasks → gate → implement) y mantener el flujo IDEAL existente de 7 fases.
- **FR-010**: Los pipelines MUST encadenar las fases automáticamente y detenerse SOLO ante decisiones o dudas reales (clarificaciones, hallazgos críticos, gate previo a implement).
- **FR-011**: Con `-bypass` y sin dudas pendientes, los pipelines MUST implementar sin esperar confirmación del usuario; con `--sin-implementar` MUST detenerse tras la planificación. `-bypass` solo salta el gate de confirmación previo a implement: si existen dudas reales pendientes (FR-010), el pipeline MUST frenar igual aunque tenga `-bypass`.
- **FR-012**: Los pipelines MUST ser retomables: detectar artefactos existentes y ofrecer continuar desde la fase faltante sin rehacer trabajo completado. En la fase implement, retomar significa despachar solo las tareas sin `[X]`, reconstruyendo el estado desde `tasks.md` y el reporte de orquestación.

**Asignación de tareas**

- **FR-013**: Al final de la fase tasks, el modelo más capaz disponible MUST clasificar cada tarea con una complejidad (`[C:baja|media|alta]`) considerando alcance, contexto necesario, dependencias, riesgo y tipo.
- **FR-014**: El sistema MUST asignar a cada tarea un modelo responsable (`[M:cli/modelo]`) consultando el inventario, eligiendo el más económico cuya capacidad y contexto alcanzan, sin excluir del reparto a ningún modelo disponible.
- **FR-015**: Las etiquetas MUST quedar inline en `tasks.md`, ser editables a mano antes de implementar, y el formato oficial de spec-kit (checkbox, `T###`, `[P]`, `[US#]`, ruta) MUST permanecer intacto.

**Orquestación**

- **FR-016**: En la fase implement, el orquestador MUST leer las asignaciones de `tasks.md` y despachar cada tarea a su CLI asignado mediante invocación por línea de comandos, respetando las etiquetas editadas por el usuario. Las invocaciones headless corren con permisos totales de edición dentro del repositorio (sin confirmaciones interactivas); el control de calidad es la verificación posterior del principal (FR-019), y los secundarios MUST NOT operar fuera del repositorio. Toda invocación headless tiene un tiempo máximo de ejecución (15 minutos por defecto, configurable); al expirar se cancela y cuenta como fallo del intento en curso.
- **FR-017**: Las tareas marcadas `[P]` MUST ejecutarse en paralelo respetando dependencias, con un límite de concurrencia configurable (4 tareas simultáneas por defecto); tareas que tocan el mismo archivo MUST serializarse aunque estén marcadas `[P]`, y una tarea `[P]` que no declara rutas MUST tratarse como conflicto potencial y ejecutarse serializada.
- **FR-018**: Si un modelo agota su cuota o queda indisponible, el orquestador MUST escalar la tarea al siguiente candidato del ranking sin intervención del usuario y registrarlo en el reporte; si no quedan candidatos, MUST pausar y reportar lo pendiente. El agotamiento MUST persistirse en el inventario (campos de cuota: estado, fecha de detección y fecha estimada de reset), y las corridas futuras MUST respetarlo hasta que venza la ventana del plan o el usuario lo resetee; si el plan es desconocido, la fecha de reset queda desconocida y el estado agotado persiste hasta reset manual. Esta actualización de los campos de cuota es la única escritura automática permitida sobre el inventario y MUST NOT pisar otras correcciones manuales (FR-004).
- **FR-019**: El CLI principal MUST integrar los resultados, verificar cada tarea y marcar `[X]` solo las tareas completadas y verificadas; las que fallan la verificación MUST reportarse para reintento o escalada. Verificar una tarea significa: (a) revisar que el diff producido cumple lo que la tarea describe, y (b) ejecutar las validaciones existentes del proyecto (tests/build, si los hay) sin que fallen. El ciclo de corrección está acotado: 1 reintento con el mismo modelo (incluyendo el motivo del rechazo), luego 1 escalada al siguiente candidato de mayor capacidad; si aún falla, la tarea queda pendiente-bloqueada y se reporta al usuario.
- **FR-020**: El orquestador MUST poder ejecutarse desde cualquiera de los tres CLIs como principal, con comportamiento equivalente, sin depender de features exclusivas de un CLI.

**Distribución y compatibilidad**

- **FR-021**: El proyecto MUST instalarse con el mismo procedimiento que el spec-kit original y MUST preservar intacto todo el comportamiento de spec-kit: mismas skills base, mismos comandos, misma estructura `.specify/`; las mejoras son estrictamente aditivas.

### Key Entities

- **Inventario de modelos** (`models.json`): estado de cada CLI (instalado, autenticado, comando headless, plan, cuota con marca de tiempo de agotamiento cuando aplica) y de cada modelo (capacidad, costo, contexto), más el ranking ordenado de candidatos por nivel de complejidad. Fuente de verdad para triage, asignación y fallback; el sistema solo escribe automáticamente el estado de cuota, el resto es del usuario.
- **Idea / Feature**: la descripción que el usuario escribe una sola vez; tiene una complejidad clasificada (simple/media/compleja) que determina flujo y modelos por fase.
- **Tarea etiquetada**: una tarea de `tasks.md` extendida con complejidad (`[C:]`) y modelo asignado (`[M:]`); conserva el formato oficial de spec-kit y es editable por el usuario.
- **Reporte de orquestación**: registro de las decisiones del sistema (triage, cambios de flujo, escaladas/degradaciones, fallbacks por cuota, tareas verificadas o pendientes). Toma dos formas: resumen en consola al final de cada fase y archivo persistente en el directorio de la feature, actualizado en cada fase (triage, asignación, implementación), auditable junto al resto de los artefactos.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Con una sola invocación de la idea y sin dudas reales pendientes (modo `-bypass`), el circuito completo llega a implementación con cero intervenciones del usuario.
- **SC-002**: El 100% de las tareas clasificadas de complejidad baja se ejecutan con modelos económicos (no el más caro) cuando hay al menos un modelo económico disponible con cuota.
- **SC-003**: En una feature mixta con los tres CLIs disponibles, los tres participan del reparto de tareas (ningún modelo disponible queda con cero tareas asignables de su nivel).
- **SC-004**: El consumo del modelo más caro se reduce al menos un 50% frente a ejecutar la misma feature íntegramente con ese modelo, medido en la unidad de uso que reporta cada CLI (tokens o porcentaje de cuota consumida) durante la validación del flujo completo.
- **SC-005**: Ante el agotamiento de cuota de un modelo durante la implementación, el 100% de sus tareas restantes se completan vía fallback sin intervención del usuario (mientras exista al menos un candidato con cuota).
- **SC-006**: Un usuario que solo usa los comandos originales de spec-kit no percibe ningún cambio de comportamiento (100% de compatibilidad hacia atrás en los flujos base).
- **SC-007**: La preparación inicial (`/speckit-models`, incluida la declaración manual) se completa en menos de 10 minutos por máquina.
- **SC-008**: Un pipeline interrumpido retoma desde la fase faltante sin repetir ninguna fase ya completada, en el 100% de los cortes entre fases.

## Assumptions

- Los tres CLIs soportados en esta versión son exactamente Claude Code, Codex CLI y
  Kimi CLI; agregar otros queda fuera de alcance.
- La plataforma objetivo es Windows 11 con PowerShell; no se exige soporte de otros
  sistemas operativos en esta versión.
- Las cuotas y planes no siempre son detectables por API: se aceptan valores declarados
  por el usuario como fuente válida, y el agotamiento real se detecta reactivamente
  (por el error/rechazo del CLI al invocarlo).
- La detección de "modelo más capaz disponible" se resuelve con el ranking de
  `models.json`; si dos modelos empatan, decide el orden de la lista.
- Un fallo de invocación headless de un CLI (no atribuible a cuota) se reintenta 1 vez;
  el segundo fallo consecutivo se trata como indisponibilidad temporal de ese CLI, con
  fallback al siguiente candidato.
- La verificación de tareas por el principal es la "verificación estándar" definida en
  FR-019 (revisión del diff contra la descripción de la tarea + validaciones existentes
  del proyecto); no incluye una revisión de código profunda por tarea, para no quemar
  cuota del modelo caro.
- El flujo IDEAL (`/speckit-specify-auto`) ya existe y sirve de base; esta feature lo
  extiende con triage y asignación sin romper su comportamiento actual.
- Se asumen versiones de los CLIs iguales o posteriores a las verificadas durante el
  diseño (con soporte de los modos headless documentados); el escaneo de inventario
  valida los flags disponibles y ajusta la plantilla de invocación si difieren.
