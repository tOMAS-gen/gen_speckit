# Feature Specification: Clasificación de modelos por nivel y tarea desde leaderboard público

**Feature Branch**: `007-arena-model-ranking`

**Created**: 2026-07-19

**Status**: Draft

**Input**: User description: "Clasificar los modelos disponibles por nivel y por tipo de tarea usando el leaderboard público https://arena.ai/leaderboard/text, e integrarlo en /speckit-models: al armar el inventario, cada modelo detectado en los CLIs se enriquece con su ranking/score y sus fortalezas por categoría de tarea (coding, razonamiento/math, escritura, seguimiento de instrucciones, etc.) tomados del leaderboard, y ese ranking alimenta la asignación por complejidad y por tipo de fase. Además, preguntar al usuario si quiere guardar esta clasificación de forma GLOBAL (compartida entre todos los proyectos que usan speckit, en el home del usuario) en vez de rehacerla en cada proyecto, con precedencia clara entre la clasificación global y la local del proyecto."

## Clarifications

### Session 2026-07-19

- Q: ¿Qué guarda exactamente el almacén de la PC (fuera del repo)? → A: la
  **clasificación de modelos** (leaderboard cacheado, nivel derivado, fortalezas por
  tarea, mapeos confirmados) **y además el plan/suscripción contratado por CLI**, para no
  tener que volver a declararlo en cada proyecto nuevo. Lo específico del proyecto (CLIs
  detectados en esa máquina, comandos headless, estado de cuota vigente, ranking
  resultante) sigue viviendo en el inventario del proyecto.
- Q: ¿Qué hace el puntaje del leaderboard con el nivel que hoy trae el catálogo? → A:
  **lo recalcula** — el puntaje comparativo se normaliza al mismo rango que usa el
  inventario y reemplaza la semilla del catálogo. Las correcciones manuales del usuario
  siempre prevalecen. Un solo campo de nivel, un solo ranking.
- Q: ¿Cómo se obtienen los datos del sitio, si no publica una API documentada? → A:
  **script propio primero, agente como respaldo** — el script descarga e interpreta el
  leaderboard; si falla, la skill le pide al CLI principal que lo consulte con su
  herramienta web y le entrega el resultado al script. Así ningún CLI queda sin poder
  refrescar la clasificación (Principio II).
- Q: ¿Cómo se resuelve el mapeo entre nombres publicados e identificadores de los CLIs?
  → A: **automático para lo inequívoco, confirmación del usuario para lo dudoso** — los
  casos dudosos se presentan en la misma tanda de preguntas que ya hace el comando y la
  elección queda persistida.
- Q: ¿Cómo se expone el reparto por tipo de fase? → A: **como una sección aditiva nueva**
  junto al ranking por complejidad existente, que no cambia; el orquestador cruza ambos
  (primero filtra por complejidad, después ordena por fortaleza en la categoría de la
  fase).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Modelos clasificados con evidencia externa, no a ojo (Priority: P1)

Al correr `/speckit-models`, además de detectar qué CLIs y modelos hay instalados, el
sistema consulta el leaderboard público de arena.ai y **enriquece cada modelo del
inventario con su posición y puntaje comparativo**. El usuario ve, junto a cada modelo,
de dónde salió su nivel: medido por el leaderboard o estimado por el catálogo local.

**Why this priority**: es el corazón del pedido. Hoy `capacidad` (1–10) y `costo` (1–3)
salen de semillas escritas a mano en el catálogo, que envejecen y no son comparables
entre proveedores con rigor. Un puntaje comparativo público convierte una opinión en un
dato verificable, y de ahí depende todo el reparto de tareas.

**Independent Test**: correr `/speckit-models` en una máquina con al menos un CLI
instalado y verificar que los modelos que existen en el leaderboard quedan registrados
con su puntaje y su fecha de consulta, y que los que no existen quedan explícitamente
marcados como "sin dato externo" conservando su valor previo.

**Acceptance Scenarios**:

1. **Given** un inventario con modelos detectados en los CLIs y acceso a internet,
   **When** el usuario corre `/speckit-models`, **Then** cada modelo que tenga
   correspondencia en el leaderboard queda registrado con su puntaje comparativo, su
   posición y la fecha de la consulta, y el resumen final muestra el origen del nivel
   de cada modelo.
2. **Given** un modelo detectado localmente que **no** aparece en el leaderboard,
   **When** termina el escaneo, **Then** ese modelo conserva su nivel previo (semilla o
   corrección manual), queda marcado como "sin dato externo" y **sigue participando**
   del reparto de tareas.
3. **Given** que el usuario corrigió a mano el nivel de un modelo, **When** se vuelve a
   correr `/speckit-models` y el leaderboard dice otra cosa, **Then** la corrección del
   usuario prevalece y la discrepancia se informa sin aplicarse automáticamente.

---

### User Story 2 - Lo que es de la máquina se declara una sola vez (Priority: P1)

La primera vez que se obtiene la clasificación, el sistema **pregunta al usuario si
quiere guardarla en la PC como dato global** (compartido por todos los proyectos que
usen speckit en esa máquina) en lugar de rehacerla en cada proyecto nuevo. Junto con la
clasificación se guarda también **el plan/suscripción contratado de cada CLI**, que hoy
el usuario tiene que volver a declarar proyecto por proyecto. Si acepta, cualquier
proyecto siguiente arranca con esos datos ya disponibles, sin consultar el sitio y sin
repetir preguntas.

**Why this priority**: el usuario lo pidió explícitamente y es lo que hace la feature
sostenible. Ni la clasificación de modelos ni el plan contratado son propiedad de un
proyecto: son propiedad de la máquina y de la cuenta. Rehacerlos por proyecto gasta
tiempo, consume red y produce inventarios divergentes entre proyectos del mismo usuario.

**Independent Test**: aceptar el guardado global en el proyecto A, luego correr
`/speckit-models` en un proyecto B recién inicializado y verificar que la clasificación
y los planes aparecen sin nueva consulta al sitio y sin repetir preguntas.

**Acceptance Scenarios**:

1. **Given** que no existe clasificación global en la máquina, **When** se obtiene la
   clasificación por primera vez, **Then** el sistema pregunta una única vez si
   guardarla globalmente y respeta la respuesta.
2. **Given** que el usuario aceptó el guardado global, **When** corre `/speckit-models`
   en otro proyecto, **Then** la clasificación se reutiliza desde el almacén global, no
   se vuelve a preguntar, y el resumen indica que el dato vino de allí y con qué fecha.
3. **Given** que el usuario rechazó el guardado global, **When** corre `/speckit-models`
   en otro proyecto, **Then** la clasificación se resuelve solo para ese proyecto y la
   pregunta puede volver a ofrecerse en el proyecto nuevo.
4. **Given** una clasificación global y una clasificación local en el mismo proyecto,
   **When** ambas describen el mismo modelo, **Then** se aplica la precedencia definida
   (ver FR-012) y el resumen deja claro qué fuente ganó para cada modelo.
5. **Given** que el plan/suscripción de un CLI ya está declarado en el almacén de la
   máquina, **When** corre `/speckit-models` en un proyecto nuevo, **Then** el plan se
   toma de allí sin volver a preguntarlo, se muestra como dato heredado, y si el usuario
   lo corrige puede guardar la corrección de vuelta en el almacén.

---

### User Story 3 - Reparto por tipo de tarea, no solo por nivel (Priority: P2)

El leaderboard no da un único número: distingue categorías (programación,
razonamiento/matemática, escritura, seguimiento de instrucciones, conversación
multi-turno). El sistema usa esas fortalezas por categoría para **elegir el modelo según
el tipo de fase**, no solo según la complejidad: un modelo fuerte en programación se
prefiere para implementar, uno fuerte en razonamiento para planificar y analizar, uno
fuerte en escritura y seguimiento de instrucciones para especificar y clarificar.

**Why this priority**: refina el reparto y es la mitad "para qué tarea" del pedido, pero
depende de que la clasificación exista primero (US1). Sin ella el sistema ya funciona
con el ranking por nivel actual.

**Independent Test**: con una clasificación cargada, verificar que el reparto propone
para la fase de implementación un candidato distinto al de la fase de planificación
cuando sus fortalezas por categoría difieren, y que la justificación de esa elección
queda registrada.

**Acceptance Scenarios**:

1. **Given** dos modelos de nivel general similar pero fortalezas distintas, **When** se
   arma el reparto, **Then** cada fase recibe primero al candidato fuerte en la
   categoría correspondiente a esa fase.
2. **Given** un modelo sin datos por categoría, **When** se arma el reparto, **Then**
   participa igualmente ordenado por su nivel general y por costo, sin quedar excluido.

---

### User Story 4 - Sin red y sin sorpresas (Priority: P2)

Si el sitio no está accesible, cambió de formato o tarda demasiado, `/speckit-models`
**termina igual** con el inventario que sí pudo armar, informa que la clasificación
externa quedó omitida y usa la última clasificación conocida (global o local) si existe.

**Why this priority**: el inventario es precondición de todo el sistema multi-CLI. Que
un sitio de terceros pueda dejar al usuario sin inventario sería una regresión grave
frente al comportamiento actual.

**Independent Test**: simular el sitio inaccesible y verificar que el comando termina
con éxito, con el inventario válido y un aviso explícito de clasificación omitida.

**Acceptance Scenarios**:

1. **Given** el sitio inaccesible y sin clasificación previa, **When** corre
   `/speckit-models`, **Then** el inventario se genera con los niveles del catálogo, se
   informa "clasificación externa omitida" con el motivo, y el comando termina con
   éxito.
2. **Given** el sitio inaccesible y una clasificación previa guardada, **When** corre
   `/speckit-models`, **Then** se reutiliza la clasificación previa indicando su fecha y
   que puede estar desactualizada.
3. **Given** una clasificación guardada con más antigüedad que el umbral de frescura,
   **When** corre `/speckit-models` con red disponible, **Then** se refresca
   automáticamente; sin red, se usa igual avisando su antigüedad.

---

### Edge Cases

- **Nombres que no coinciden**: el leaderboard nombra los modelos con etiquetas
  comerciales completas y los CLIs con identificadores cortos. Un modelo puede no
  matchear, matchear parcialmente o matchear con varias variantes de esfuerzo. El
  sistema debe resolver el caso claro, dejar sin dato el caso dudoso y **nunca** asignar
  el puntaje de un modelo a otro por parecido de nombre.
- **Variantes de esfuerzo/razonamiento**: un mismo modelo aparece varias veces en el
  leaderboard con distintos niveles de esfuerzo. Debe quedar definido qué variante
  representa al modelo del inventario.
- **Modelos del inventario que no son de texto** o que no compiten en el leaderboard:
  quedan sin dato externo y conservan su nivel.
- **Clasificación global escrita por otra versión** de la herramienta, con formato
  distinto o corrupta: se ignora con aviso, nunca se rompe el comando ni se pisa en
  silencio.
- **Dos proyectos corriendo `/speckit-models` a la vez** sobre el mismo almacén global:
  la escritura no debe dejar el archivo global a medio escribir.
- **Empate de puntaje** entre candidatos: el desempate debe ser determinista (costo
  primero, luego orden estable) para que el reparto sea reproducible.
- **El usuario no tiene permisos de escritura** en el directorio de configuración del
  usuario: se informa y se degrada a clasificación solo local.

## Requirements *(mandatory)*

### Functional Requirements

**Obtención y modelado de la clasificación**

- **FR-001**: El sistema MUST obtener, durante `/speckit-models`, la clasificación
  pública de modelos de texto desde el leaderboard, incluyendo por cada modelo listado
  su puntaje comparativo, su posición y las categorías de tarea disponibles.
- **FR-002**: El sistema MUST registrar, junto a la clasificación, la fecha y la fuente
  de la consulta, de modo que el usuario pueda saber qué antigüedad tiene el dato.
- **FR-003**: El sistema MUST asociar cada modelo del inventario con su entrada del
  leaderboard mediante una correspondencia explícita y auditable, y MUST dejar el modelo
  "sin dato externo" cuando la correspondencia no sea inequívoca.
- **FR-004**: El sistema MUST permitir al usuario declarar o corregir a mano la
  correspondencia entre un modelo del inventario y una entrada del leaderboard, y esa
  declaración MUST sobrevivir a futuras ejecuciones.
- **FR-004a**: La correspondencia automática MUST aplicarse solo cuando sea inequívoca;
  los casos dudosos MUST presentarse al usuario dentro de la misma tanda de preguntas
  que ya hace el comando, y su elección MUST persistirse para no volver a preguntarla.
- **FR-005**: El sistema MUST derivar, para cada modelo con dato externo, un nivel
  comparable con el resto del inventario a partir del puntaje del leaderboard, **que
  reemplaza el nivel sembrado por el catálogo**, y MUST registrar el origen del nivel
  (`medido` / `estimado` / `manual`). El inventario MUST seguir teniendo un único campo
  de nivel por modelo.
- **FR-005a**: El sistema MUST obtener los datos mediante un mecanismo propio,
  independiente de las capacidades particulares del CLI principal; si ese mecanismo
  falla, MUST poder recibir el contenido obtenido por el agente y continuar con él. Un
  CLI sin herramienta web propia MUST poder refrescar la clasificación igual.
- **FR-006**: Las correcciones manuales del usuario sobre nivel, costo o
  correspondencia MUST prevalecer siempre sobre el dato externo; ante discrepancia el
  sistema MUST informarla sin aplicarla automáticamente.
- **FR-007**: El sistema MUST registrar, por cada modelo con dato externo, sus
  fortalezas relativas en las categorías de tarea relevantes para las fases del pipeline
  (programación, razonamiento, escritura, seguimiento de instrucciones).

**Uso en el reparto**

- **FR-008**: El sistema MUST usar el nivel derivado del leaderboard como insumo del
  ranking de asignación por complejidad, manteniendo el criterio vigente de preferir el
  candidato más económico cuya capacidad alcanza.
- **FR-009**: El sistema MUST producir, **como agregado al ranking por complejidad
  existente y sin modificarlo**, un orden de candidatos por tipo de fase basado en las
  fortalezas por categoría. Quien hoy consume el ranking por complejidad MUST seguir
  funcionando sin cambios; el reparto final MUST cruzar ambos (primero el filtro por
  complejidad, después el orden por fortaleza de la fase).
- **FR-010**: Ningún modelo instalado y autenticado MUST quedar excluido del reparto por
  falta de dato externo, por puntaje bajo o por no aparecer en el leaderboard.
- **FR-011**: El desempate entre candidatos con puntaje equivalente MUST ser
  determinista y reproducible entre ejecuciones.

**Almacenamiento global vs. local**

- **FR-012**: El sistema MUST resolver el valor efectivo de cada dato compartido
  (nivel, fortalezas, mapeo, plan/suscripción) con esta precedencia, de mayor a menor:
  (1) corrección manual del usuario en el proyecto, (2) dato local del proyecto,
  (3) dato del almacén de la máquina, (4) valores del catálogo local. El resumen MUST
  indicar qué fuente ganó para cada modelo y para el plan de cada CLI.
- **FR-013**: El sistema MUST preguntar al usuario —una sola vez por máquina, la primera
  vez que obtiene la clasificación— si desea guardarla globalmente, explicando qué
  implica, y MUST recordar la respuesta para no volver a preguntar.
- **FR-014**: Cuando existe clasificación global vigente, `/speckit-models` MUST
  reutilizarla sin volver a consultar el sitio ni repetir la pregunta.
- **FR-015**: Los usuarios MUST poder forzar el refresco de la clasificación, cambiar la
  decisión global↔local y borrar la clasificación global, sin editar archivos a mano.
- **FR-016**: El almacén de la máquina MUST contener únicamente datos que son de la
  máquina y no del proyecto: la clasificación de modelos (leaderboard cacheado, nivel
  derivado, fortalezas por tarea, mapeos confirmados) y el **plan/suscripción contratado
  por CLI**. MUST excluir rutas del proyecto, credenciales, tokens, comandos de
  invocación y el estado de cuota vigente.
- **FR-016a**: Cuando el almacén de la máquina ya tiene declarado el plan/suscripción de
  un CLI, `/speckit-models` MUST NOT volver a preguntarlo en un proyecto nuevo; MUST
  mostrarlo como dato heredado y permitir corregirlo, y la corrección MUST poder
  guardarse de vuelta en el almacén de la máquina.
- **FR-017**: La escritura del almacén global MUST ser atómica: una interrupción o dos
  proyectos escribiendo a la vez nunca MUST dejar el archivo inválido.

**Resiliencia y frescura**

- **FR-018**: Si la fuente externa no está disponible, tarda más que el tiempo máximo
  admitido o entrega un contenido que no se puede interpretar, `/speckit-models` MUST
  completarse igual, con el inventario válido y un aviso explícito del motivo.
- **FR-019**: El sistema MUST considerar la clasificación vencida pasado un umbral de
  frescura **configurable, con un valor por defecto de 7 días**, y refrescarla cuando
  haya red; sin red MUST usarla igual, informando su antigüedad.
- **FR-019a**: El sistema MUST descartar las entradas del leaderboard cuya cantidad de
  votos esté por debajo de un mínimo configurable (por defecto 500), tratándolas como
  "sin dato externo". Una muestra chica produce un puntaje inestable que haría variar el
  reparto sin motivo real.
- **FR-020**: Una clasificación guardada ilegible, corrupta o de un formato no
  reconocido MUST ser ignorada con aviso, sin abortar el comando y sin pisarla en
  silencio. Si el archivo es legible pero de una versión de formato no reconocida, los
  datos **declarados por el usuario** (plan/suscripción y mapeos confirmados) MUST
  preservarse o volver a preguntarse explícitamente: descartarlos en silencio está
  prohibido.
- **FR-020a**: Si el directorio de configuración del usuario no es escribible, el sistema
  MUST informarlo y continuar guardando solo en el proyecto, sin abortar el comando.
- **FR-021**: Toda consulta a la fuente externa MUST ser de solo lectura y no MUST
  enviar información del proyecto ni del usuario.

**Compatibilidad**

- **FR-022**: La feature MUST ser aditiva: un proyecto sin clasificación (global ni
  local) MUST seguir funcionando exactamente como hoy, y el formato vigente del
  inventario MUST seguir siendo válido.

### Key Entities *(include if data involved)*

- **Clasificación de modelos**: conjunto de entradas obtenidas de la fuente externa en
  una fecha dada. Atributos: fuente, fecha de obtención, versión de formato, lista de
  entradas.
- **Entrada de clasificación**: un modelo tal como lo publica el leaderboard. Atributos:
  nombre publicado, organización, puntaje comparativo, posición, variante de esfuerzo si
  la hay, puntajes por categoría de tarea.
- **Correspondencia modelo↔entrada**: vínculo entre un modelo del inventario
  (`cli/modelo`) y una entrada de clasificación. Atributos: entrada elegida, forma en
  que se resolvió (automática o declarada por el usuario), confianza.
- **Nivel efectivo de un modelo**: el valor comparable usado por el reparto. Atributos:
  valor, origen (`medido`/`estimado`/`manual`), fuente que ganó la precedencia.
- **Perfil por tarea**: fortalezas relativas de un modelo por categoría (programación,
  razonamiento, escritura, seguimiento de instrucciones).
- **Almacén de la máquina**: archivo en el directorio de configuración del usuario,
  compartido por todos los proyectos de esa PC. Guarda la clasificación, los mapeos
  confirmados, el plan/suscripción por CLI y la decisión global/local del usuario.
  Excluye credenciales, rutas de proyecto y estado de cuota.
- **Orden de candidatos por fase**: sección nueva del inventario que, para cada tipo de
  fase, lista los modelos ordenados por su fortaleza en la categoría correspondiente.
  Convive con el ranking por complejidad existente sin modificarlo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En una máquina con los CLIs habituales instalados, al menos el 80% de los
  modelos del inventario que compiten en el leaderboard quedan asociados a su entrada
  correcta —contando tanto los resueltos automáticamente como los confirmados por el
  usuario en la única tanda de preguntas— y **ninguno** queda asociado a una entrada
  equivocada. La asociación equivocada es el único fallo inaceptable: dejar un modelo sin
  asociar solo le cuesta precisión al reparto.
- **SC-002**: El segundo proyecto y los siguientes obtienen la clasificación **y el plan
  de cada CLI** sin ninguna consulta a la fuente externa y sin ninguna pregunta al
  usuario.
- **SC-003**: Con la fuente externa caída, `/speckit-models` termina con éxito y con un
  inventario utilizable en el 100% de los casos.
- **SC-004**: La consulta externa agrega como máximo 30 segundos al tiempo total de
  `/speckit-models`, y el comando nunca queda esperando indefinidamente.
- **SC-005**: Un usuario puede entender de dónde salió el nivel de cada modelo leyendo
  únicamente el resumen que imprime el comando, sin abrir ningún archivo.
- **SC-006**: Repetir `/speckit-models` sin cambios en la máquina produce exactamente el
  mismo reparto de candidatos (resultado reproducible).
- **SC-007**: Ninguna corrección manual previa del usuario se pierde al refrescar la
  clasificación (0 sobrescrituras silenciosas).

## Assumptions

- **Fuente**: se asume que el leaderboard de texto de arena.ai es de acceso público, sin
  autenticación, y que expone puntaje comparativo, posición y categorías de tarea por
  modelo. No se asume la existencia de una API oficial documentada; la obtención debe
  tolerar cambios de formato degradando limpiamente (FR-018).
- **Categorías**: de las muchas categorías del leaderboard se usa un subconjunto fijo
  mapeable a las fases del pipeline (programación, razonamiento/matemática, escritura,
  seguimiento de instrucciones). El resto se ignora en esta versión.
- **Variantes de esfuerzo**: cuando un modelo aparece con varias variantes de esfuerzo,
  la variante de mayor puntaje representa al modelo del inventario, salvo que el CLI
  exponga esfuerzos concretos y el usuario elija otra correspondencia.
- **Costo**: el leaderboard publica precios de lista por token, que no reflejan los
  planes por suscripción que usa este proyecto. Por eso el costo sigue viniendo del plan
  declarado por el usuario; el dato externo alimenta el nivel, no el costo.
- **Cuota**: el estado de cuota es volátil y lo escribe la orquestación durante la
  ejecución, así que queda en el proyecto y **no** se comparte en el almacén de la
  máquina, aunque el plan que la origina sí.
- **Umbral de frescura**: 7 días por defecto, refrescable a demanda.
- **Ubicación del almacén global**: el directorio de configuración del usuario propio de
  cada sistema operativo, sin depender de la plataforma.
- **Alcance**: solo modelos de texto. Otros leaderboards (visión, imagen) quedan fuera.
- **Dependencia**: la feature se apoya en el inventario y el descubrimiento de modelos
  ya existentes (features 001 y 006); no los reemplaza.
