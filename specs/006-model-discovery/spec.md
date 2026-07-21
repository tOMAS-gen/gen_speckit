# Feature Specification: Descubrimiento y verificación real de modelos por CLI

**Feature Branch**: `006-model-discovery`

**Created**: 2026-07-18

**Status**: Draft

**Input**: User description: "mejorar /speckit-models: al escanear, por cada CLI del inventario ejecutar su comando de listado de modelos para extraer los modelos reales y sus niveles de esfuerzo/razonamiento; complementar y verificar contra los sitios oficiales de cada CLI qué modelos están disponibles; y registrar en models.json qué modelos están confirmados en cada CLI/agente"

## Clarifications

### Session 2026-07-18

- Q: ¿Los modelos publicados oficialmente pero no confirmados localmente entran al
  ranking de asignación? → A: **Sí, entran directamente** (opción B). Quedan marcados
  `oficial-sin-confirmar` en el inventario, pero participan del ranking como cualquier
  otro. La red de seguridad es el fallback existente del orquestador: si el despacho a
  un modelo no disponible falla, se clasifica `indisponible` y se escala al siguiente
  candidato sin intervención del usuario.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Modelos reales extraídos de cada CLI (Priority: P1)

Al correr `/speckit-models`, el escaneo no se limita a las semillas del catálogo: por
cada CLI instalado ejecuta el mecanismo de listado de modelos que ese CLI ofrezca (si el
catálogo lo declara) y extrae **los modelos realmente disponibles en esa instalación**,
incluidos sus niveles de esfuerzo/razonamiento cuando el CLI los exponga (p. ej.
"thinking: high", niveles de reasoning effort). El inventario refleja lo que la máquina
del usuario tiene de verdad, no una lista fija.

**Why this priority**: es el corazón del pedido — hoy los modelos salen de semillas
estáticas del catálogo, que quedan viejas (planes cambian, modelos nuevos aparecen, como
K3 recién habilitado). Sin datos reales, el ranking asigna mal.

**Independent Test**: en una máquina con los CLIs instalados, correr el escaneo y
verificar que los modelos listados coinciden con los que cada CLI reporta por su propio
mecanismo (y no solo con las semillas).

**Acceptance Scenarios**:

1. **Given** un CLI instalado cuyo catálogo declara un mecanismo de listado de modelos,
   **When** se ejecuta el escaneo, **Then** el inventario registra los modelos que ese
   CLI reportó, con su nivel de esfuerzo/razonamiento si el CLI lo expone.
2. **Given** un CLI cuyo listado real difiere de las semillas del catálogo (modelo nuevo
   o retirado), **When** se ejecuta el escaneo, **Then** el inventario refleja lo real y
   el origen de cada modelo queda distinguible (detectado vs. semilla).
3. **Given** un CLI instalado que NO ofrece mecanismo de listado no interactivo,
   **When** se ejecuta el escaneo, **Then** se usan las semillas del catálogo/fuentes
   oficiales y el modelo queda marcado como no verificado localmente — nunca se inventa.

---

### User Story 2 - Verificación contra fuentes oficiales (Priority: P2)

El escaneo complementa la detección local consultando las **fuentes oficiales de cada
CLI** (documentación/sitios del proveedor, declarados en el catálogo): qué modelos
existen para ese CLI, cuáles requieren determinado plan, y novedades que el CLI local
todavía no muestre. Con eso se **verifica** cuáles de esos modelos están efectivamente
disponibles en cada CLI/agente de esta máquina, y el resultado queda registrado con su
estado de confirmación.

**Why this priority**: los sitios oficiales son la referencia de qué debería estar
disponible; cruzarlos con lo detectado localmente permite marcar confirmado/no
confirmado y detectar drift del catálogo. Depende de US1 para tener contra qué cruzar.

**Independent Test**: correr el escaneo con acceso a la web y verificar que cada modelo
del inventario queda con un estado de confirmación (confirmado localmente / solo
oficial / solo semilla), y que las fuentes consultadas quedan registradas.

**Acceptance Scenarios**:

1. **Given** fuentes oficiales declaradas para un CLI, **When** se ejecuta el escaneo
   con acceso a la web, **Then** los modelos publicados oficialmente se cruzan con los
   detectados y cada modelo queda con su estado de confirmación.
2. **Given** un entorno sin acceso a la web (o fuente caída), **When** se ejecuta el
   escaneo, **Then** la verificación oficial se omite sin fallar (best-effort) y el
   inventario lo indica.
3. **Given** un modelo publicado oficialmente que el CLI local no reporta, **When** se
   cruza la información, **Then** el modelo se suma al inventario marcado
   `oficial-sin-confirmar` y **entra al ranking de asignación** como cualquier otro
   (Clarifications); si al despachar resulta no disponible, el fallback del orquestador
   escala al siguiente candidato.

---

### User Story 3 - Esfuerzo/razonamiento en el inventario (Priority: P3)

`models.json` registra, por modelo, los **niveles de esfuerzo/razonamiento** que soporta
(cuando se conocen), como campo aditivo del contrato. El usuario puede corregirlos a
mano y sus ediciones prevalecen, igual que el resto del inventario.

**Why this priority**: el usuario lo pidió explícitamente ("información de los modelos y
esfuerzo"); habilita a futuro que el asignador considere el esfuerzo además de capacidad
y costo. No bloquea US1/US2.

**Independent Test**: tras un escaneo, verificar que los modelos que exponen niveles de
esfuerzo los tienen registrados en el inventario y que una edición manual sobrevive un
re-escaneo.

**Acceptance Scenarios**:

1. **Given** un CLI que expone niveles de esfuerzo para un modelo, **When** se escanea,
   **Then** el inventario registra esos niveles en el modelo correspondiente.
2. **Given** una corrección manual de esos niveles, **When** se re-escanea, **Then** la
   corrección del usuario prevalece (regla de merge existente).

---

### Edge Cases

- CLI instalado sin mecanismo de listado no interactivo → semillas + fuentes oficiales,
  marcado como no verificado localmente; nunca inventar.
- El mecanismo de listado consume una llamada/cuota → NO ejecutarlo por defecto; solo
  con aprobación explícita del usuario (paridad con la regla de `--probe-auth`).
- Salida del listado no parseable o con formato nuevo → degradar a semillas con aviso,
  sin romper el escaneo.
- Sin acceso a la web → US2 se omite best-effort; el escaneo local sigue funcionando.
- Discrepancia semillas del catálogo vs. detección real → gana lo real; el origen queda
  registrado para auditar el catálogo.
- Ediciones manuales del usuario (capacidad, costo, esfuerzos) → siempre prevalecen
  sobre lo detectado (regla de merge vigente).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El catálogo de CLIs DEBE poder declarar, por CLI y de forma aditiva, el
  mecanismo de listado de modelos no interactivo (si existe) y las fuentes oficiales de
  referencia (URLs de documentación del proveedor).
- **FR-002**: El escaneo DEBE ejecutar, por cada CLI instalado que lo declare, el
  mecanismo de listado y extraer los modelos reales y sus niveles de
  esfuerzo/razonamiento cuando estén expuestos.
- **FR-003**: El escaneo DEBE cruzar lo detectado con las fuentes oficiales (cuando haya
  acceso a la web) y registrar por modelo un **estado de confirmación** distinguible:
  confirmado localmente / publicado oficialmente sin confirmación local / solo semilla.
  Los tres estados **participan del ranking de asignación** por igual (decisión del
  usuario, ver Clarifications); la indisponibilidad real la resuelve el fallback del
  orquestador en despacho.
- **FR-004**: La verificación web es **best-effort**: sin red o con fuente inaccesible,
  el escaneo local completa igual y el inventario indica que la verificación se omitió.
- **FR-005**: El sistema NUNCA inventa modelos: todo modelo del inventario proviene de
  detección local, fuente oficial o semilla del catálogo, con su origen registrado.
- **FR-006**: Los mecanismos que consumen llamadas/cuota NO se ejecutan por defecto;
  requieren aprobación explícita del usuario (paridad con la prueba de autenticación).
- **FR-007**: `models.json` DEBE incorporar los campos nuevos de forma **aditiva** (sin
  romper el contrato vigente): niveles de esfuerzo por modelo y estado/origen de
  confirmación. Los consumidores existentes del inventario siguen funcionando sin
  cambios.
- **FR-008**: Las ediciones manuales del usuario DEBEN seguir prevaleciendo sobre lo
  detectado/verificado (regla de merge existente aplicada a los campos nuevos).
- **FR-009**: La skill `/speckit-models` DEBE orquestar el flujo completo: escaneo local
  (script) + verificación oficial (a cargo del agente, que es quien puede navegar) +
  presentación del resultado con los estados de confirmación por CLI.

### Key Entities

- **Mecanismo de listado por CLI**: declaración en el catálogo de cómo obtener los
  modelos reales de un CLI de forma no interactiva (y si consume cuota).
- **Fuente oficial**: URL(s) de referencia del proveedor por CLI, declaradas en el
  catálogo, consultadas best-effort.
- **Modelo del inventario (extendido)**: además de `id`, `capacidad`, `costo`,
  `contexto_k`, ahora niveles de esfuerzo (opcional) y estado/origen de confirmación.
- **Estado de confirmación**: confirmado-local / oficial-sin-confirmar / semilla.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tras un escaneo en una máquina con CLIs instalados, el 100% de los modelos
  del inventario tiene origen y estado de confirmación registrados (0 modelos
  inventados).
- **SC-002**: Para los CLIs que exponen listado de modelos, el inventario coincide con
  lo que el CLI reporta localmente (verificable comparando ambos listados).
- **SC-003**: Los modelos que exponen niveles de esfuerzo los tienen registrados; una
  edición manual de cualquier campo sobrevive un re-escaneo.
- **SC-004**: Sin acceso a la web, el escaneo completa igual (la verificación oficial se
  omite declaradamente, sin error).
- **SC-005**: El contrato vigente de `models.json` no se rompe: los consumidores
  actuales (asignador, orquestador, despacho) funcionan sin cambios.

## Assumptions

- No todos los CLIs ofrecen un listado de modelos no interactivo; para esos casos la
  fuente es catálogo + sitios oficiales, con el modelo marcado como no confirmado
  localmente. La investigación de qué ofrece cada CLI es parte de la fase de plan.
- La consulta a sitios oficiales la realiza el **agente** que ejecuta la skill (los
  scripts no navegan); por eso es best-effort y depende del entorno.
- La estimación de `capacidad` (1–10) y `costo` (1–3) sigue siendo propuesta corregible
  por el usuario; esta feature no cambia esa semántica, solo mejora el origen de los
  datos.
- El alcance NO incluye cambiar la lógica del asignador para usar los niveles de
  esfuerzo (se registran; su uso en el ranking es una mejora futura).
- Fuente de verdad de los CLIs conocidos: `clis-catalog.json` versionado; los campos
  nuevos son aditivos y con defaults seguros (sin listado declarado = comportamiento
  actual).
