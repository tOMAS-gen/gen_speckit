# Feature Specification: Fork de specify-cli con mejoras multi-CLI integradas

**Feature Branch**: `004-specify-cli-fork`

**Created**: 2026-07-18

**Status**: Draft

**Input**: User description: "convertir gen_speckit en un fork del spec-kit oficial con las mejoras multi-CLI integradas en specify-cli, para que specify init instale todo de una"

## Clarifications

### Session 2026-07-18

- Q: ¿Cómo debe estructurarse el "fork" (vendorizar el source, wrapper fino, o extensión vía preset)? → A: Fork real — el código de specify-cli vive dentro del repo con las mejoras **integradas** (no overlay que se copia aparte). Es *el spec-kit de gen*, una sola pieza; lo tuyo ya es parte del producto, no un paso extra.
- Q: ¿Cómo se llama la herramienta y cómo convive con el specify-cli oficial? → A: Conserva el comando `specify` (mismo gesto: `uv tool install ... --from git+<este repo>` + `specify init`); el fork de gen reemplaza al oficial, no se busca convivencia.
- Q: ¿Qué pasa con install.ps1 y el producto se instala siempre u opcional? → A: `install.ps1` se da de baja como paso separado; el producto multi-CLI viene **siempre** integrado en el `init`, conservando la elección de agente (claude/codex/kimi/todos).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inicializar un proyecto con todo en un solo paso (Priority: P1)

Una persona quiere empezar a usar gen_speckit en un proyecto nuevo. Instala la
herramienta de línea de comandos una sola vez y corre un único comando de
inicialización en la carpeta de su proyecto. Al terminar, el proyecto tiene la base
completa de spec-kit **y** el producto multi-CLI (pipelines auto/eco, triage,
`/speckit-models`, asignador, orquestador, playbooks portables, scripts de soporte y
catálogo de CLIs) listos para usar — sin correr un segundo instalador ni copiar nada a
mano.

**Why this priority**: es el corazón de la feature. Hoy la instalación son dos gestos
(`specify init` oficial + `install.ps1` que copia el producto). Colapsar eso en un solo
`specify init` es el valor entero de la feature; sin esto, no hay feature.

**Independent Test**: en una carpeta vacía, instalar la herramienta forkeada y correr
el comando de init una sola vez; verificar que quedan presentes tanto los artefactos
base de spec-kit (skills base, `.specify/` con scripts/plantillas/constitución) como el
producto multi-CLI completo, sin pasos adicionales.

**Acceptance Scenarios**:

1. **Given** una máquina con la herramienta forkeada instalada y un directorio de
   proyecto vacío, **When** la persona corre el comando de inicialización una sola vez,
   **Then** el proyecto queda con la base de spec-kit y el producto multi-CLI presentes
   y funcionales, sin ejecutar un segundo instalador.
2. **Given** un proyecto ya inicializado con la herramienta forkeada, **When** la
   persona corre `/speckit-models` y luego `/speckit-specify-auto "idea"`, **Then** los
   pipelines multi-CLI funcionan igual que en el repo de desarrollo (no falta ningún
   playbook, script ni skill).
3. **Given** la documentación de instalación del proyecto, **When** una persona la
   sigue de principio a fin, **Then** en ningún paso se le pide correr `install.ps1` ni
   copiar archivos manualmente para obtener el producto multi-CLI.

---

### User Story 2 - Elegir el agente principal durante la inicialización (Priority: P2)

Al inicializar, la persona elige para qué agente (Claude, Codex, Kimi o varios) se
instalan las skills multi-CLI, con el mismo gesto con el que el spec-kit oficial permite
elegir el agente de las skills base. La elección determina en qué formato y ubicación
quedan las skills del producto, sin romper la elección de agente base del init oficial.

**Why this priority**: preserva la paridad con el instalador actual (`-Skills
claude|codex|kimi|todos`) y con el gesto del spec-kit oficial (elección de agente).
Importante para la adopción, pero el flujo por defecto (un agente) ya entrega valor sin
esta elección explícita.

**Independent Test**: correr el init eligiendo un agente distinto del de las skills base
(p. ej. base para Claude, producto multi-CLI para Kimi) y verificar que las skills
multi-CLI quedan en la ubicación/formato del agente elegido, y las base en el suyo.

**Acceptance Scenarios**:

1. **Given** el comando de init con la opción de agente para el producto multi-CLI,
   **When** la persona elige `claude` (o `codex`, `kimi`, `todos`), **Then** las skills
   multi-CLI quedan instaladas en el formato y ubicación de ese agente.
2. **Given** que la persona no especifica agente para el producto, **When** corre el
   init, **Then** el producto multi-CLI se instala para el mismo agente elegido para las
   skills base (comportamiento por defecto).

---

### User Story 3 - Mantener el fork al día con el spec-kit upstream (Priority: P3)

La persona que mantiene gen_speckit necesita poder incorporar mejoras del spec-kit
oficial de GitHub sin perder ni re-hacer a mano la capa multi-CLI. La relación con el
proyecto upstream está estructurada de modo que las actualizaciones de spec-kit se
integran de forma acotada y la capa propia queda claramente separada y preservada.

**Why this priority**: sostiene el valor en el tiempo (el Principio I exige
compatibilidad total y aditiva con spec-kit). No bloquea la primera entrega, pero sin
esto el fork se vuelve inmantenible a mediano plazo.

**Independent Test**: simular una actualización del upstream (cambio en un archivo base
de spec-kit) e incorporarla al fork verificando que la capa multi-CLI sigue intacta y
que el resultado del init sigue entregando ambos.

**Acceptance Scenarios**:

1. **Given** una nueva versión del spec-kit oficial, **When** el mantenedor la incorpora
   al fork siguiendo el procedimiento definido, **Then** la capa multi-CLI permanece
   intacta y el init sigue entregando base + producto.
2. **Given** el repositorio del fork, **When** alguien lo inspecciona, **Then** puede
   distinguir con claridad qué proviene del upstream y qué es la capa propia multi-CLI.

---

### Edge Cases

- ¿Qué pasa si en la máquina ya está instalada la herramienta `specify` oficial de
  GitHub? El fork de gen usa el mismo comando `specify` y reemplaza al oficial al
  instalarse (no se busca convivencia); tras instalar el fork, `specify init` es el de gen.
- ¿Qué pasa si el directorio destino ya fue inicializado (tiene `.specify/`)? El init
  debe preservar lo existente y sumar/actualizar el producto multi-CLI sin destruir
  trabajo del usuario (paridad con el comportamiento actual de `install.ps1`).
- ¿Qué pasa si el destino ya tiene un `AGENTS.md` propio? No debe pisarse; el aporte
  multi-CLI debe quedar en un archivo separado o fusionarse de forma no destructiva.
- ¿Qué pasa en Linux/macOS (con PowerShell 7) versus Windows? El init debe entregar el
  producto en todas las plataformas soportadas hoy por el proyecto.
- ¿Qué pasa si una persona instaló con la vía anterior (`install.ps1`) y ahora migra al
  fork? La transición no debe duplicar ni corromper artefactos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE distribuirse como un fork del spec-kit oficial cuya
  herramienta de línea de comandos (`specify init`) entrega, en una sola ejecución,
  tanto la base de spec-kit como el producto multi-CLI de gen_speckit.
- **FR-002**: El comando de inicialización DEBE dejar el proyecto destino con **todo** el
  producto multi-CLI que hoy copia `install.ps1`: las 8 skills nuevas, los playbooks de
  `.specify/orchestrator/`, los scripts PowerShell de soporte, el catálogo de CLIs y los
  punteros de portabilidad — sin pasos manuales adicionales.
- **FR-003**: El sistema DEBE preservar intacta la compatibilidad con spec-kit
  (Principio constitucional I): todo lo que hace el spec-kit oficial sigue funcionando
  igual (skills base, comandos, estructura `.specify/`, formato de artefactos). La
  integración multi-CLI es estrictamente aditiva.
- **FR-004**: El comando de inicialización DEBE permitir elegir el/los agente(s) para
  los que se instala el producto multi-CLI (Claude, Codex, Kimi o todos), instalándolo
  en el formato y ubicación correctos de cada agente; por defecto, el mismo agente
  elegido para las skills base.
- **FR-005**: El sistema DEBE conservar el comportamiento no destructivo actual sobre el
  destino: no pisar un `AGENTS.md` existente, preservar un `.specify/` ya inicializado, y
  agregar al `.gitignore` las exclusiones de datos locales (`models.json`,
  `models.scan.json`, logs de orquestación).
- **FR-006**: El sistema DEBE entregar el producto en todas las plataformas soportadas
  hoy (Windows 11 con PowerShell 5.1/7; Linux y macOS con PowerShell 7).
- **FR-007**: El repositorio DEBE ser un fork real del spec-kit oficial: el código del
  `specify-cli` vive dentro de este repo con las mejoras multi-CLI **integradas** (no como
  overlay que se copia aparte). El producto es parte del CLI/plantillas que el `init`
  deposita — una sola pieza, no un agregado. El repositorio DEBE mantener una separación
  interna clara entre lo que proviene del spec-kit upstream y la capa multi-CLI propia,
  de modo que las actualizaciones del upstream puedan incorporarse sin re-hacer la capa
  propia (procedimiento de mantenimiento documentado).
- **FR-008**: La herramienta forkeada DEBE conservar el comando `specify` (mismo gesto
  que el spec-kit oficial: `uv tool install ... --from git+<este repo>` + `specify
  init`). El fork de gen reemplaza al `specify-cli` oficial en la máquina; no se busca
  convivencia con el oficial (quien use este repo usa *el spec-kit de gen*).
- **FR-009**: El comando `specify init` DEBE entregar el producto multi-CLI **siempre**,
  de forma integrada, sin flag para omitirlo (es parte de qué es este spec-kit).
  `install.ps1` DEBE darse de baja como paso/gesto de instalación separado una vez que el
  `init` entrega todo. Se conserva la opción de elegir el/los agente(s) del producto
  (FR-004).
- **FR-010**: La documentación del proyecto (README, distribución, requisitos) DEBE
  actualizarse para reflejar el nuevo gesto de instalación de un solo paso, sin dejar
  instrucciones contradictorias del flujo de dos pasos.

### Key Entities

- **Herramienta forkeada (`specify-cli` fork)**: el paquete de línea de comandos
  derivado del spec-kit oficial que ejecuta `init` y entrega base + producto.
- **Producto multi-CLI**: el conjunto aditivo que hoy define el manifiesto de
  `install.ps1` (8 skills, playbooks del orquestador, 6 scripts, catálogo de CLIs,
  punteros de portabilidad, aporte a `AGENTS.md` y `.gitignore`).
- **Capa upstream**: los artefactos que provienen tal cual del spec-kit oficial y que no
  deben modificarse en su comportamiento.
- **Proyecto destino**: la carpeta del usuario donde corre `specify init` y donde queda
  instalado base + producto.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una persona pasa de cero a un proyecto con base + producto multi-CLI
  ejecutando **un solo** comando de inicialización (más la instalación única de la
  herramienta), sin correr un segundo instalador ni copiar archivos.
- **SC-002**: El 100% de los elementos del producto multi-CLI que hoy entrega
  `install.ps1` quedan presentes y funcionales tras el init de un solo paso (verificable
  ítem por ítem contra el manifiesto actual).
- **SC-003**: El 100% de los comandos y artefactos base del spec-kit oficial siguen
  comportándose igual que en una instalación oficial (sin regresiones de compatibilidad).
- **SC-004**: Tras el init, los pipelines `/speckit-specify-auto` y
  `/speckit-specify-auto-eco` corren de punta a punta en un proyecto recién inicializado
  sin que falte ningún playbook, script o skill.
- **SC-005**: El init entrega el producto correctamente en las tres plataformas
  soportadas (Windows, Linux, macOS) en la corrida de validación del proyecto.

## Assumptions

- El público objetivo ya usa (o está dispuesto a usar) `uv` para instalar herramientas
  Python, igual que con el spec-kit oficial.
- La lista de elementos del producto multi-CLI a entregar es la del manifiesto vigente
  de `install.ps1` (8 skills, 6 scripts, playbooks, catálogo, punteros); si el manifiesto
  cambia, esta feature sigue esa fuente de verdad.
- La convivencia/compatibilidad se evalúa contra la versión del spec-kit oficial vigente
  al momento de forkear; no se garantiza compatibilidad con versiones futuras no
  publicadas del upstream.
- Las plataformas soportadas son las declaradas hoy por el proyecto (Windows 11 +
  PowerShell 5.1/7; Linux/macOS con PowerShell 7).
- El fork no introduce dependencia de API keys: sigue operando solo con los CLIs y sus
  suscripciones (Principio constitucional de no usar API keys).
