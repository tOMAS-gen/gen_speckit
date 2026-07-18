# Feature Specification: Soporte Genérico de CLIs y Multiplataforma

**Feature Branch**: `003-generic-cli-support`

**Created**: 2026-07-18

**Status**: Draft

**Input**: User description: "El proyecto hoy solo funciona con tres CLIs fijos (claude, codex, kimi) hardcodeados en scripts, contratos y siembra; debería ser general para cualquier CLI de IA. Incluir un apartado de configuración de CLIs que permita: registrar/crear un CLI nuevo, generar su plantilla de invocación, y verificar que funciona. Además, compatibilidad con Linux y macOS."

## Clarifications

### Session 2026-07-18

- Q: ¿Estrategia multiplataforma? → A: Runtime único — los scripts se mantienen compatibles con Windows PowerShell 5.1 y PowerShell 7, y corren con `pwsh` (PowerShell 7) en Linux/macOS. Prerequisito declarado fuera de Windows: `pwsh`. Sin duplicación de lógica en otros lenguajes.
- Q: ¿Dónde vive el apartado de configuración de CLIs? → A: Skill nueva dedicada (`speckit-clis`) con registrar/editar/verificar/dar de baja; `/speckit-models` conserva su rol de escaneo/ranking y se alimenta del catálogo + CLIs registrados. Ambas comparten el inventario.
- Q: ¿Catálogo e inventarios existentes? → A: Catálogo como archivo de datos versionado en el repo (`.specify/clis-catalog.json`: plantillas, patrones de cuota, quirks de los CLIs conocidos) + lectura compatible del `models.json` existente sin migración: los campos nuevos son opcionales con defaults del catálogo, y las ediciones del usuario en el inventario siempre prevalecen sobre el catálogo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registrar cualquier CLI (Priority: P1)

Como usuario, tengo un apartado de configuración de CLIs donde registro un CLI de IA
nuevo (por ejemplo Gemini CLI, Qwen Code, o uno interno de mi empresa) declarando su
nombre, su comando de invocación no-interactiva, sus modelos (capacidad, costo,
contexto) y sus patrones de error de cuota. El CLI registrado queda en el inventario y
participa del ranking y del reparto de tareas exactamente igual que los precargados —
sin tocar una línea de código.

**Why this priority**: es la esencia del pedido — hoy agregar un CLI exige editar
scripts, contratos y siembra; con esto el sistema es abierto.

**Independent Test**: registrar un CLI ficticio (un stub local que responde a una
invocación), verificar que aparece en `models.json` con su plantilla, que entra en las
listas de asignación según capacidad/costo, y que una asignación posterior le da
tareas.

**Acceptance Scenarios**:

1. **Given** el apartado de configuración, **When** registro un CLI nuevo con nombre, comando de invocación (con los placeholders de prompt y modelo), modelos y patrones de cuota, **Then** queda persistido en el inventario y aparece en las listas de asignación que su capacidad/costo justifican.
2. **Given** un intento de registro con datos inválidos (nombre duplicado, plantilla sin placeholder de prompt, modelo sin capacidad), **When** confirmo, **Then** el sistema rechaza el registro explicando exactamente qué falta — nunca guarda un CLI inválido.
3. **Given** un CLI registrado, **When** lo edito (cambiar plantilla, agregar un modelo) o lo doy de baja, **Then** los cambios se reflejan en el inventario y el ranking se recalcula; dar de baja pide confirmación.
4. **Given** un CLI registrado por configuración, **When** corre una asignación y una orquestación, **Then** recibe y ejecuta tareas igual que los CLIs precargados (cero discriminación — Constitución IV).

---

### User Story 2 - Verificar que un CLI funciona (Priority: P1)

Como usuario, puedo verificar cualquier CLI del inventario (precargado o registrado):
el sistema comprueba que el comando existe en el sistema, que está autenticado (en la
medida detectable) y — con mi permiso explícito, porque consume una llamada — hace una
invocación de prueba mínima y me muestra el diagnóstico con el resultado clasificado.

**Why this priority**: registrar sin poder verificar deja al usuario adivinando; la
verificación convierte la configuración en algo confiable antes de despachar trabajo
real.

**Independent Test**: verificar un CLI instalado (diagnóstico verde), uno no instalado
(diagnóstico claro de qué falta) y uno con plantilla rota (el diagnóstico señala la
plantilla), sin que ninguna verificación gaste cuota sin permiso.

**Acceptance Scenarios**:

1. **Given** un CLI instalado y autenticado, **When** lo verifico con invocación de prueba aprobada, **Then** el diagnóstico muestra: comando resuelto, autenticación, invocación exitosa y tiempo de respuesta.
2. **Given** un CLI no instalado o con plantilla inválida, **When** lo verifico, **Then** el diagnóstico indica exactamente qué falló (comando no encontrado / placeholder faltante / error del CLI) y qué corregir.
3. **Given** la verificación con invocación de prueba, **When** no doy permiso explícito, **Then** solo se ejecutan los chequeos que no consumen cuota (existencia del comando, credenciales detectables).
4. **Given** el resultado de una verificación, **When** termina, **Then** el estado detectado (instalado/autenticado) se actualiza en el inventario sin tocar los campos que me pertenecen.

---

### User Story 3 - Ningún CLI fijo en el código (Priority: P2)

Como mantenedor del proyecto, los nombres claude/codex/kimi dejan de estar
incorporados en scripts, playbooks y contratos: pasan a ser un catálogo de CLIs
conocidos precargado como datos (con sus particularidades documentadas), corregible y
extensible. Los inventarios existentes siguen funcionando sin intervención.

**Why this priority**: es la deuda técnica que habilita a US1 — mientras los nombres
estén en el código, "cualquier CLI" es mentira; pero el valor visible al usuario llega
vía US1/US2.

**Independent Test**: buscar referencias fijas a los tres nombres en los scripts (debe
haber cero fuera del catálogo de datos); cargar un inventario generado por la versión
anterior y verificar que todo sigue funcionando; registrar un cuarto CLI y correr el
ciclo completo sin ninguna edición de código.

**Acceptance Scenarios**:

1. **Given** los scripts y playbooks de la versión nueva, **When** se inspeccionan, **Then** ninguna lógica depende de nombres de CLI fijos: todo se lee del inventario y del catálogo de datos precargado.
2. **Given** un `models.json` generado por la versión anterior (tres claves fijas), **When** la versión nueva lo lee, **Then** funciona sin migración manual (o se migra automáticamente con aviso y sin pérdida de las ediciones del usuario).
3. **Given** el catálogo precargado, **When** el usuario lo corrige (p. ej. un flag que cambió de versión), **Then** su corrección prevalece sobre el dato precargado (FR-004 del proyecto: el usuario siempre gana).

---

### User Story 4 - Compatibilidad Linux y macOS (Priority: P2)

Como usuario de Linux o macOS, instalo el proyecto y todo el sistema multi-CLI
funciona: detección de CLIs, generación del inventario, despacho headless con timeout
y captura de salida, actualización de cuota y agrupación de tareas — con el mismo
comportamiento que en Windows.

**Why this priority**: amplía el alcance del proyecto a todos los entornos donde
corren los CLIs de IA; sin esto, "cualquier CLI" queda limitado a "cualquier CLI en
Windows".

**Independent Test**: en un entorno Linux (o contenedor), correr la suite de tests y
los escenarios de detección/despacho con un CLI stub; verificar comportamiento
idéntico al de Windows.

**Acceptance Scenarios**:

1. **Given** un entorno Linux o macOS con el runtime requerido instalado, **When** corro la detección de CLIs y la generación del inventario, **Then** el resultado es equivalente al de Windows (mismos campos, mismo formato de archivo).
2. **Given** una orquestación en Linux/macOS, **When** se despachan tareas a un CLI, **Then** la invocación respeta timeout, captura stdout/stderr a archivos y clasifica el resultado igual que en Windows (incluido matar el árbol de procesos al expirar).
3. **Given** la suite de tests del proyecto, **When** corre en cada sistema operativo soportado, **Then** pasa completa en los tres.

---

### Edge Cases

- ¿Qué pasa si la plantilla de invocación registrada no contiene el placeholder de
  prompt? El registro se rechaza en el momento (validación de alta), nunca al
  despachar.
- ¿Qué pasa si el usuario registra un CLI con el mismo nombre que uno existente? Se
  rechaza el duplicado y se ofrece editar el existente.
- ¿Qué pasa si se da de baja un CLI que tiene tareas asignadas (`[M:ese-cli/...]`) en
  un `tasks.md` activo? La baja advierte las referencias existentes; el orquestador
  tratará esas etiquetas como inválidas y aplicará el fallback del ranking (regla ya
  existente).
- ¿Qué pasa con un comando de invocación peligroso (el usuario registra una plantilla
  que borra archivos)? La verificación siempre MUESTRA el comando exacto antes de
  ejecutarlo y requiere aprobación; el registro en sí no ejecuta nada.
- ¿Qué pasa si el sistema operativo no tiene el runtime necesario para los scripts?
  La instalación/documentación lo declara como prerequisito verificable, y los
  comandos fallan con un mensaje claro de qué instalar — nunca con un error críptico.
- ¿Qué pasa con un `models.json` de la versión anterior que además tiene ediciones
  manuales? La lectura compatible las preserva (mismas garantías de FR-004 del
  proyecto).
- ¿Qué pasa si un CLI conocido del catálogo se instala DESPUÉS de generar el
  inventario? Una re-detección lo incorpora igual que hoy (comportamiento existente,
  ahora alimentado por el catálogo).
- ¿Qué pasa al dar de baja un CLI del catálogo, si un re-escaneo lo volvería a crear?
  La baja de un CLI de catálogo lo marca como deshabilitado en el inventario (no lo
  borra), y el escaneo y el ranking respetan esa marca hasta que el usuario la quite.
- ¿Qué pasa si el catálogo de CLIs conocidos falta o está corrupto? El sistema sigue
  funcionando con el inventario del usuario más los valores de respaldo genéricos, y
  lo avisa — el catálogo nunca es un punto único de falla.

## Requirements *(mandatory)*

### Functional Requirements

**Configuración de CLIs (apartado nuevo)**

- **FR-001**: El sistema MUST ofrecer un apartado de configuración de CLIs como skill dedicada (`speckit-clis`, Clarificación S2) con las operaciones: registrar (crear), editar, verificar y dar de baja un CLI, persistiendo en el inventario del proyecto. `/speckit-models` conserva su rol actual (escaneo y ranking) alimentándose del catálogo y de los CLIs registrados.
- **FR-002**: El registro MUST capturar como mínimo: nombre único, comando de invocación no-interactiva con placeholders de prompt y modelo, lista de modelos (id, capacidad 1–10, costo 1–3, contexto), y patrones de detección de cuota agotada propios del CLI.
- **FR-003**: El registro MUST validar los datos en el alta (nombre único, placeholder de prompt presente, al menos un modelo válido) y MUST rechazar registros inválidos explicando cada problema; nunca persiste un CLI inválido.
- **FR-004**: Un CLI registrado MUST participar del ranking de asignación y del reparto de tareas en igualdad de condiciones con los precargados (Constitución IV), desde la siguiente regeneración del ranking.
- **FR-005**: La baja de un CLI MUST pedir confirmación, advertir si existen etiquetas `[M:]` activas que lo referencien, y no borrar información del usuario sin aviso.

**Verificación de CLIs**

- **FR-006**: El sistema MUST poder verificar cualquier CLI del inventario en niveles: (a) comando resoluble en el sistema, (b) autenticación detectable sin gastar cuota, (c) invocación de prueba mínima SOLO con permiso explícito del usuario (consume una llamada).
- **FR-007**: La verificación MUST mostrar el comando exacto que va a ejecutar antes de la invocación de prueba y MUST producir un diagnóstico accionable (qué falló y cómo corregirlo).
- **FR-008**: El resultado de la verificación MUST actualizar solo los campos detectables del inventario (instalado, autenticado, versión) sin pisar los campos declarados por el usuario.

**Generalización (sin CLIs fijos)**

- **FR-009**: Ninguna lógica de scripts, playbooks o skills MUST depender de nombres de CLI fijos; toda referencia a CLIs MUST resolverse desde el inventario en tiempo de ejecución.
- **FR-010**: Los CLIs hoy soportados (claude, codex, kimi) y sus particularidades conocidas (plantillas, patrones de cuota, quirks de versión) MUST convertirse en un catálogo de datos versionado en el repo (`.specify/clis-catalog.json` — Clarificación S3), corregible por el usuario y extensible sin tocar código; las ediciones del usuario en el inventario prevalecen sobre el catálogo.
- **FR-011**: Un inventario generado por la versión anterior MUST seguir funcionando por lectura compatible, sin migración: los campos nuevos son opcionales y sus valores se resuelven con defaults del catálogo; el 100% de las ediciones manuales se preserva.
- **FR-012**: Los patrones de cuota agotada MUST leerse del inventario/catálogo por CLI (con un conjunto genérico de respaldo), no de tablas internas del código.

**Multiplataforma**

- **FR-013**: Todas las capacidades del sistema (detección, inventario, configuración, verificación, despacho con timeout y captura, actualización de cuota, agrupación de tareas) MUST funcionar en Windows, Linux y macOS con comportamiento equivalente.
- **FR-014**: El código MUST eliminar los supuestos exclusivos de Windows (intérprete de comandos, utilidades del sistema, separadores de ruta, terminación de árboles de procesos) usando mecanismos portables equivalentes en cada sistema.
- **FR-015**: Los prerequisitos de runtime por sistema operativo MUST estar declarados y ser verificables; su ausencia MUST producir un mensaje claro de instalación, no un error críptico.
- **FR-016**: La suite de tests MUST poder ejecutarse en los tres sistemas operativos y MUST cubrir los puntos sensibles a plataforma (rutas, procesos, encoding).

**Compatibilidad del proyecto**

- **FR-017**: Todo lo anterior MUST ser aditivo sobre spec-kit (Constitución I) y mantener la portabilidad multi-CLI del orquestador (Constitución II): el apartado de configuración es invocable desde cualquier CLI principal.

### Key Entities

- **Definición de CLI**: nombre único, comando de invocación con placeholders, modelos (id, capacidad, costo, contexto), patrones de cuota, origen (`catalogo` | `registrado`), estado detectado (instalado, autenticado, versión). Vive en el inventario.
- **Catálogo de CLIs conocidos**: datos precargados de claude/codex/kimi con sus particularidades por versión (reemplaza la siembra en código); corregible por el usuario, sus correcciones prevalecen.
- **Verificación de CLI**: resultado por niveles (comando / autenticación / invocación de prueba) con diagnóstico, comando mostrado y clasificación del resultado; actualiza solo campos detectables.
- **Inventario (`models.json`) v2**: mismo rol que hoy con CLIs dinámicos; compatible hacia atrás con el formato de tres claves.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario registra y verifica un CLI nuevo en menos de 5 minutos, sin editar ningún archivo de código.
- **SC-002**: Un CLI registrado por configuración recibe tareas en la primera asignación posterior a su alta (cero exclusiones con capacidad/cuota suficientes).
- **SC-003**: Cero referencias a nombres de CLI fijos en la lógica de scripts y playbooks (verificable por búsqueda automática; el catálogo de datos es la única fuente).
- **SC-004**: El 100% de los inventarios generados por la versión anterior funcionan sin intervención manual (con ediciones del usuario preservadas).
- **SC-005**: La suite de tests completa pasa en Windows, Linux y macOS.
- **SC-006**: La verificación de un CLI no consume ninguna llamada sin permiso explícito del usuario (0 invocaciones de prueba no aprobadas).

## Assumptions

- "Cualquier CLI" significa cualquier herramienta de línea de comandos que acepte una
  invocación no-interactiva con un prompt y devuelva texto, con código de salida
  utilizable; CLIs sin modo no-interactivo quedan fuera de alcance.
- El apartado de configuración se materializa como capacidad conversacional del
  sistema (skill/playbook portable), no como interfaz gráfica.
- Estrategia multiplataforma decidida en clarify (S1): runtime único compatible
  5.1/7, con `pwsh` como prerequisito declarado en Linux/macOS (FR-015).
- La validación en Linux/macOS puede ejecutarse en contenedores o máquinas del
  usuario; el entorno de desarrollo actual es Windows y no puede validar macOS
  localmente — SC-005 puede verificarse por CI o por corrida manual documentada.
- Los tres CLIs actuales siguen precargados de fábrica (catálogo), por lo que la
  experiencia existente no cambia para quien no registra CLIs nuevos.
