# gen_speckit

<!-- speckit:objetivo:inicio -->
## Objetivo

Extender el Spec Kit de GitHub con un orquestador multi-CLI (Claude Code, Codex y
Kimi) donde el usuario solo escribe la idea: el sistema clasifica su complejidad
(triage), elige el flujo y el modelo para cada fase y cada tarea, y despacha el
trabajo al modelo más económico que alcance — reservando los modelos caros para las
decisiones que lo justifican. Todo de forma estrictamente aditiva sobre spec-kit.

_Actualizado: 2026-07-18_
<!-- speckit:objetivo:fin -->

<!-- speckit:alcance:inicio -->
## Alcance

**Es**: skills y playbooks Markdown portables + scripts PowerShell sobre un repo
spec-kit; inventario y ranking de modelos (`models.json`); pipelines de una sola
llamada (IDEAL y ECO); asignación de tareas por complejidad; orquestación con
despacho headless, paralelismo y fallback por cuota; especificador de agentes y
README gestionado.

**No es**: no modifica las skills base de spec-kit; no usa API keys (solo los CLIs
con sus suscripciones); v1 es Windows 11 + PowerShell; sin soporte de otros CLIs
fuera de claude/codex/kimi.

_Actualizado: 2026-07-18_
<!-- speckit:alcance:fin -->

<!-- speckit:estado:inicio -->
## Estado

| Feature | Fase | Avance |
|---|---|---|
| 001 — Orquestador Multi-CLI | Implementada | 27/33 tareas; despacho real a los 3 CLIs validado en producción (features 002/003); pendientes las mediciones E2E (SC-004) |
| 002 — Especificador de Agentes y README | Implementada | 10/11 tareas; 7 agentes del proyecto generados y aprobados |
| 003 — Soporte Genérico de CLIs y Multiplataforma | Implementada | 19/20 tareas; cualquier CLI registrable sin tocar código (validado con un 4to CLI stub); suite 76/76; pendiente la corrida de CI en los 3 SO |

_Actualizado: 2026-07-18_
<!-- speckit:estado:fin -->

Repositorio que **mejora el [Spec Kit de GitHub](https://github.com/github/spec-kit) existente** y se instala de la misma manera: obtenés todo el spec-kit original **más** un orquestador multi-CLI (**Claude, Codex y Kimi**) que analiza la complejidad de la idea y de cada tarea, y despacha el trabajo al modelo más conveniente para **reducir el costo y el uso** de cada implementación.

## Objetivo

**Simplificar el sistema spec-kit de GitHub con un sistema multi-CLI donde solo pongo la idea** — desde cualquiera de los CLIs — y el sistema se autocorrige para decidir todo lo demás:

- **Quién planifica**: elige solo qué flujo usar (eco o ideal) y qué modelo ejecuta cada fase, según la complejidad de la idea.
- **Qué tarea hace cada modelo**: clasifica cada tarea y la asigna al modelo adecuado.
- **Aprovechar los modelos económicos y más disponibles** para el grueso del trabajo, y **dejar los más complejos/caros solo para las tareas más importantes**.

En concreto, el sistema:

1. **Identifica la complejidad** de la idea (triage) y de cada tarea generada por spec-kit.
2. **Elige el CLI y modelo adecuado** para cada fase y cada tarea (Claude Code, Codex o Kimi), según complejidad, desempeño del modelo, plan contratado, ventana de contexto y uso/cuota disponible.
3. **Reduce el costo y el uso**: una sola llamada con la idea, mínima intervención del usuario, y cada token caro gastado solo donde hace la diferencia.

### Arquitectura simétrica (principal / secundarios)

El orquestador puede correr desde **cualquiera** de los tres CLIs:

- El CLI que ejecuta el orquestador actúa como **principal**.
- Los otros dos actúan como **secundarios**: reciben las acciones/tareas por invocación de línea de comandos.
- Por eso el orquestador debe ser **portable**: no puede depender de features exclusivas de un CLI.

## Configuración previa (obligatoria)

Antes de usar la skill se debe especificar, para cada plataforma:

| Dato | Descripción |
|---|---|
| **Plan contratado** | Qué plan/suscripción se usa en cada CLI (Claude, Codex, Kimi) |
| **Modelos disponibles** | Qué modelos ofrece cada plan y su desempeño relativo |
| **Ventana de contexto** | Tamaño de contexto de cada modelo (si se puede obtener) |
| **Uso / cuota disponible** | Límite y consumo actual de cada plataforma (si se puede obtener) |

Con estos datos el orquestador puede elegir adecuadamente sin exceder límites ni desperdiciar cuota de los modelos caros.

## Flujo de trabajo

```
Preparación (una vez):
  /speckit-models  → detecta CLIs instalados, modelos, planes y cuotas
                     y genera el ranking en .specify/models.json

Por cada idea / feature:
  Triage (lo hace el modelo importante, antes de arrancar):
    └─> Analiza la complejidad de la especificación (alcance, ambigüedad, riesgo):
         · Idea simple   → flujo ECO, fases con modelos económicos
         · Idea media    → flujo IDEAL, fases con modelos mixtos
         · Idea compleja → flujo IDEAL, fases clave con el modelo importante
        Además decide qué modelo ejecuta CADA FASE del pipeline
        (no solo la implementación se reparte — las fases también).
  Pipeline (specify → ... → tasks):
    └─> En la fase tasks, un MODELO IMPORTANTE (el más capaz disponible):
         1. Clasifica la complejidad de cada tarea [C:baja|media|alta]
         2. Asigna qué modelo se hace cargo de cada tarea
            (regla: nunca discriminar — todos los modelos disponibles
             participan según su capacidad, costo y disponibilidad)
  Orquestador (fase implement):
    └─> 3. Lee tasks.md con las asignaciones
        4. Despacha cada tarea a su CLI asignado ([P] en paralelo)
        5. Si un modelo agota su cuota, escala al siguiente del ranking
        6. El principal integra, verifica y marca [X]
```

### Triage de la especificación

Al recibir la idea, el modelo importante evalúa su complejidad **antes de ejecutar nada**:

| Complejidad de la idea | Flujo | Modelos por fase |
|---|---|---|
| Simple | ECO (4 fases) | Fases con modelos económicos; el importante solo asigna en tasks |
| Media | IDEAL (7 fases) | Mixto: plan/analyze con modelo importante, el resto intermedios |
| Compleja | IDEAL (7 fases) | Specify, plan y analyze con el modelo importante |

- Si el flujo invocado no coincide con lo recomendado (ej. `/speckit-specify-auto` con una idea simple): sin `-bypass` pregunta si cambiar a eco; con `-bypass` cambia solo y lo informa en el reporte.
- El triage lo hace el modelo importante: decidir mal el flujo es caro y el análisis en sí es corto.

**El triage también se evalúa a sí mismo** — la autocorrección incluye al propio modelo que recibió la idea:

- Idea escrita en un CLI **económico** (ej. Kimi) pero la idea es **compleja** → el modelo actual es inferior a lo necesario: **escala** la planificación a un modelo superior y él queda como secundario/despachador.
- Idea escrita en un CLI **caro** (ej. Claude) pero la idea es **simple** → el modelo actual es superior a lo necesario: **degrada** el trabajo a los modelos económicos para no quemar cuota cara en algo trivial.

Ningún punto de entrada es incorrecto: la idea se escribe en cualquier CLI y el sistema se reacomoda solo, hacia arriba o hacia abajo.

### Principios de asignación

- **Nunca discriminar un modelo**: el ranking no excluye a nadie; decide qué tareas le tocan a cada modelo. Todos los CLIs disponibles participan del reparto.
- **Asignar es tarea de modelo importante**: clasificar y repartir lo hace el modelo más capaz (el principal) — equivocarse en el reparto es caro; ejecutar una tarea simple, no.
- **El más barato que alcance**: cada tarea va al modelo más económico cuya capacidad y contexto alcanzan para resolverla bien.

### Contratos de datos

**Etiquetas en `tasks.md`** (las agrega el asignador; editables a mano antes de implementar):

```
- [ ] T012 [P] [US1] [C:baja]  [M:kimi/k2]     Crear modelo User en src/models/user.py
- [ ] T019     [US2] [C:alta]  [M:claude/opus] Integrar pasarela de pagos en src/services/payments.py
```

- `[C:baja|media|alta]` — complejidad clasificada
- `[M:cli/modelo]` — modelo que se hace cargo de la tarea
- El formato oficial de spec-kit (checkbox, `T###`, `[P]`, `[US#]`, ruta) no se modifica

**`.specify/models.json`** (lo genera `/speckit-models`; el usuario puede corregirlo):

```json
{
  "clis": {
    "claude": {
      "instalado": true, "autenticado": true, "headless": "claude -p",
      "plan": "declarado por el usuario", "cuota": "ok",
      "modelos": [ { "id": "opus", "capacidad": 9, "costo": 3, "contexto_k": 200 } ]
    },
    "codex": { "...": "" }, "kimi": { "...": "" }
  },
  "asignacion": {
    "alta":  ["claude/opus"],
    "media": ["codex/gpt-5-codex", "claude/sonnet"],
    "baja":  ["kimi/k2", "codex/gpt-5-mini"]
  }
}
```

- `capacidad` (1–10) y `costo` (1–3): valores comparables, propuestos por el escaneo y corregibles
- `asignacion`: por cada complejidad, lista **ordenada** de candidatos — el primero es el preferido; si no tiene cuota o contexto, se escala al siguiente (fallback resuelto por diseño)
- `headless`: comando exacto con el que el orquestador invoca a cada CLI secundario

## Paso a paso del proyecto

### Paso 1 — Instalar Spec Kit ✅

```powershell
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
specify version   # verificar instalación
```

### Paso 2 — Inicializar el proyecto ✅

```powershell
specify init . --integration claude --script ps
```

Esto creó `.specify/` (scripts, plantillas, constitución) y `.claude/skills/` con las 10 skills base de spec-kit: `constitution`, `specify`, `clarify`, `plan`, `tasks`, `checklist`, `analyze`, `implement`, `converge`, `taskstoissues`.

### Paso 3 — Pipelines automatizados `/speckit-specify-auto` y `/speckit-specify-auto-eco`

Con **una sola llamada** se ejecuta todo el circuito de spec-kit, en dos variantes:

**`/speckit-specify-auto "idea"` — flujo ideal ✅** (creada)

Ejecuta las 7 fases, incluidas las opcionales de calidad:

```
specify → clarify → plan → checklist → tasks → analyze → [gate] → implement
```

Para features medianas/grandes o con requisitos difusos: tres controles de calidad (clarify, checklist, analyze) antes de escribir código.

**`/speckit-specify-auto-eco "idea"` — flujo simple ✅** (creada)

Ejecuta solo el ciclo mínimo, sin las fases opcionales:

```
specify → plan → tasks → [gate] → implement
```

Para features chicas, ideas claras o prototipos: menos pasos, menos consumo.

**Comportamiento común de ambas:**

- Encadenan las fases automáticamente; **solo se frenan ante decisiones o dudas reales** (preguntas de clarificación, hallazgos críticos).
- Flag **`-bypass`**: si no hay dudas pendientes, implementa directamente **sin esperar la orden del usuario** (salta el gate de confirmación previo a implement).
- Flag `--sin-implementar`: se detiene tras la planificación (no ejecuta implement).
- Retomables: detectan artefactos existentes y ofrecen continuar desde la fase faltante.

### Paso 4 — Comando de descubrimiento `/speckit-models` ✅

Skill + script (`scan-models.ps1`) que arma el inventario de recursos disponibles:

- **Detección automática**: qué CLIs están instalados (claude/codex/kimi), versión, autenticación, modo headless disponible (`claude -p`, `codex exec`, etc.) y modelos que exponga cada uno.
- **Declaración del usuario** (lo que no se puede detectar): plan contratado, cuotas/límites, ventana de contexto.
- **Salida**: `.specify/models.json` con el ranking de modelos de mejor a peor por **capacidad según tipo de tarea, costo y disponibilidad**. El usuario puede corregir el ranking a mano.

### Paso 5 — Asignador de modelos en la fase tasks ✅

Paso extra al final de la fase tasks de los pipelines, **ejecutado por el modelo más capaz disponible** (el principal):

- Clasifica la complejidad de cada tarea: alcance, contexto necesario, dependencias, riesgo, tipo → `[C:baja|media|alta]`.
- Asigna qué modelo se hace cargo de cada tarea consultando `.specify/models.json`, sin excluir a ninguno.
- Las etiquetas quedan inline en `tasks.md` (editables a mano antes de implementar).

### Paso 6 — Crear la skill orquestadora ✅

Reemplaza/envuelve la fase implement: lee `tasks.md` con las asignaciones, despacha cada tarea a su CLI por línea de comandos (las `[P]` en paralelo, respetando dependencias), escala al siguiente modelo del ranking si uno agota cuota, integra resultados y marca `[X]`. Portable: puede correr desde cualquiera de los tres CLIs como principal.

**Implementación**: la lógica portable vive en `.specify/orchestrator/` (playbooks `triage.md`, `assign.md`, `orchestrate.md` + `report-template.md`); las skills por CLI son adaptadores finos (`.claude/skills/` para Claude, `AGENTS.md` + `.codex/prompts/` para Codex/Kimi). Scripts de soporte en `.specify/scripts/powershell/` (`scan-models.ps1`, `get-parallel-groups.ps1`, `invoke-secondary.ps1`, `update-quota.ps1`) con tests Pester en `tests/powershell/`.

> **Nota**: `.specify/models.json` y `.specify/models.scan.json` contienen datos locales de tu máquina (planes, cuotas) — al versionar el proyecto con git, agregalos a `.gitignore`.

### Skills de contexto de proyecto (feature 002)

La feature 002-agent-specifier agregó tres comandos slash: `speckit-agents` analiza el objetivo del proyecto contra una taxonomía de dominios y genera las definiciones de agentes necesarias en `.specify/agents/` (portables) y `.claude/agents/` (nativas de Claude), con confirmación previa; `speckit-readme` crea o actualiza el README con secciones gestionadas delimitadas (objetivo, alcance, estado) preservando el contenido manual; `speckit-constitution-plus` corre la fase constitution base y al terminar ofrece el especificador de agentes.

### Configuración de CLIs (feature 003)

El sistema ya no está limitado a claude/codex/kimi — cualquier CLI de IA con modo no-interactivo se puede registrar con el comando slash `speckit-clis` (registrar, editar, verificar, dar de baja), los CLIs conocidos vienen precargados en el catálogo versionado `.specify/clis-catalog.json` (plantillas, patrones de cuota y quirks por versión), y el inventario `.specify/models.json` ahora acepta claves de CLI dinámicas manteniendo compatibilidad con el formato anterior.

### Paso 7 — Probar el flujo completo

Validar con una feature real: planificar con `/speckit-specify-auto` y dejar que el orquestador reparta la implementación entre Kimi, Codex y Claude, midiendo el ahorro de costo/uso.

## Distribución

Este proyecto se empaqueta como repositorio instalable **igual que el spec-kit original**:

```powershell
# 1) Herramienta oficial de spec-kit (una sola vez por máquina):
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# 2) En la carpeta de tu proyecto — inicializa spec-kit oficial Y agrega las
#    mejoras multi-CLI en un solo paso:
irm https://raw.githubusercontent.com/tOMAS-gen/gen_speckit/main/install.ps1 | iex
```

El instalador corre el `specify init` oficial (si el proyecto no está inicializado) y
después copia **solo el producto** según un manifiesto explícito: las 8 skills
multi-CLI, los playbooks de `.specify/orchestrator/`, los 6 scripts, el catálogo de
CLIs y los punteros de portabilidad. **Nada del desarrollo de este repo** (specs,
constitución, agentes, tests, CI) llega a tu proyecto. Desde un clon local:
`.\install.ps1 -Destino C:\mi-proyecto`.

- **Compatibilidad total**: todo lo que hace spec-kit sigue funcionando igual (mismas skills base, mismos comandos, misma estructura `.specify/`).
- **Solo se agregan funciones**: los pipelines `/speckit-specify-auto` y `/speckit-specify-auto-eco`, el triage, `/speckit-models`, el asignador y el orquestador multi-CLI.
- Quien conoce spec-kit no aprende nada nuevo; quien quiere las mejoras las obtiene con el mismo gesto de instalación.

## Requisitos

- Windows 11 con PowerShell 5.1 o 7
- Linux y macOS con PowerShell 7 (`pwsh`) instalado (`apt install powershell` / `brew install powershell`)
- Para desarrollo (correr los tests) se necesita Pester 5 o superior (`Install-Module Pester`)
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes de Python)
- CLIs instalados: [Claude Code](https://claude.com/claude-code), Codex CLI, Kimi CLI

## Estructura del proyecto

```
gen_speckit/
├── .claude/
│   └── skills/          # Skills base de spec-kit + models + auto/auto-eco + orchestrate
├── .codex/
│   └── prompts/         # Adaptadores para Codex como principal
├── .specify/
│   ├── memory/          # Constitución del proyecto
│   ├── orchestrator/    # Playbooks portables (triage, assign, orchestrate, report)
│   ├── scripts/         # Scripts PowerShell de soporte (+ scan/invoke/quota/groups)
│   └── templates/       # Plantillas de spec, plan y tasks
├── specs/               # Features especificadas (spec, plan, tasks, reportes)
├── tests/
│   └── powershell/      # Tests Pester de los scripts
├── AGENTS.md            # Adaptador para Codex/Kimi como principal
└── README.md
```
