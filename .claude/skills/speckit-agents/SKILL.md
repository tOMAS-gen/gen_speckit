---
name: "speckit-agents"
description: "Especificador de agentes del proyecto: analiza el objetivo (constitución → README → specs → usuario), evalúa la cobertura por dominios con una taxonomía base fija, propone los agentes necesarios y, con confirmación del usuario, genera definiciones portables en .specify/agents/ más la versión nativa del CLI. Usar cuando el usuario invoca /speckit-agents, al terminar constitution-plus, o cuando un pipeline lo ofrece tras una specify compleja."
argument-hint: "[sin argumentos — analiza el proyecto actual]"
compatibility: "Requiere estructura .specify/ de spec-kit"
metadata:
  author: "gen_speckit"
user-invocable: true
disable-model-invocation: false
---

## Objetivo

Que el proyecto tenga el equipo de agentes correcto: por cada dominio de necesidad
del objetivo, un agente definido — sin duplicados, sin pisar nada existente, y solo
con aprobación explícita del usuario.

**Quién ejecuta el análisis**: el modelo más capaz disponible (primer candidato de
`asignacion.alta` de `.specify/models.json` si existe) — decidir la estructura del
equipo es una decisión cara (Constitución V). Sin inventario, ejecuta el modelo actual.

## Paso 1 — Derivar el objetivo del proyecto (FR-001)

Buscar el objetivo EN ESTE ORDEN y usar la primera fuente disponible:

1. `.specify/memory/constitution.md` (si tiene principios ratificados, no template)
2. `README.md` (sección de objetivo si existe)
3. `specs/*/spec.md` (las features dicen qué se está construyendo)
4. **Preguntar al usuario** — si ninguna fuente existe o el objetivo es ilegible.

NUNCA inventar el objetivo. El idioma de todo lo generado = idioma de la fuente (o de
la respuesta del usuario).

## Paso 2 — Análisis de cobertura (FR-002)

El análisis es SIEMPRE a nivel proyecto (no por feature). Evaluar los 8 dominios de
la taxonomía base + extras:

| Dominio base | Aplica si el objetivo involucra... |
|---|---|
| `interfaz` | UI, web, móvil, TUI, experiencia de usuario |
| `servicios` | Backend, APIs, lógica de negocio, procesos |
| `datos` | Persistencia, esquemas, migraciones, datos de usuarios |
| `pruebas` | Cualquier código que deba verificarse (casi siempre aplica) |
| `documentacion` | Docs de usuario/desarrollador, READMEs, guías |
| `seguridad` | Auth, permisos, secretos, datos sensibles, entrada externa |
| `infraestructura` | Despliegue, CI/CD, empaquetado, entornos |
| `integraciones` | APIs de terceros, CLIs externos, protocolos |

- **Extras**: si el objetivo tiene necesidades que no encajan (p. ej. `orquestacion`,
  `contenido`, `ml`), declarar dominios extra en kebab-case.
- **Cobertura existente**: leer el frontmatter `dominio` de cada
  `.specify/agents/*.md` (la cobertura se decide por dominio, NO por nombre).
  Un archivo sin frontmatter parseable se reporta inválido y NO cuenta como cobertura.
- Cada dominio queda: `cubierto por <agente>` | `faltante` | `no aplica` (con una
  línea de justificación — hace verificable la cobertura).

## Paso 3 — Propuesta y confirmación (FR-003) — GATE REAL

Presentar la tabla completa: dominio → estado → agente propuesto (nombre kebab-case,
rol de una línea, justificación). Para cada faltante, proponer al menos un agente con
responsabilidades y límites (qué NO hace).

Esperar la decisión del usuario: **aprobar todo / aprobar un subconjunto / rechazar /
agregar dominios propios**. NO escribir NADA antes de la confirmación. Rechazar o
declinar termina sin ningún efecto secundario.

## Paso 4 — Generación (FR-004, contrato agent-definition.md)

Por cada agente aprobado:

1. **Portable** — `.specify/agents/<nombre>.md`:

   ```markdown
   ---
   name: <nombre-kebab>
   dominio: <dominio>
   rol: <una línea>
   origen: generado
   fecha: <YYYY-MM-DD>
   ---

   ## Responsabilidades
   - ...

   ## Límites
   - ...

   ## Instrucciones
   <system prompt portable, en el idioma del proyecto>
   ```

2. **Nativa (solo si el CLI principal es Claude Code)** — `.claude/agents/<nombre>.md`
   con frontmatter `name` + `description` (rol + dominio + cuándo usarlo) y cuerpo =
   Instrucciones + Responsabilidades + Límites. En otros CLIs, omitir sin error: el
   portable es el consumible universal.

**Reglas duras**:
- NUNCA sobrescribir un archivo existente en `.specify/agents/` ni `.claude/agents/`
  (FR-005). Colisión de nombre → proponer nombre alternativo.
- Solo se crean los agentes APROBADOS.

## Paso 5 — Re-ejecuciones, huecos y huérfanos (FR-005, FR-006)

- Re-corrida sin cambios → "todo cubierto", 0 propuestas, 0 archivos tocados.
- Dominio aplicable sin cobertura (agente borrado o dominio nuevo) → proponer SOLO ese
  faltante.
- **Huérfanos**: agentes cuyo `dominio` ya no aparece en el análisis del objetivo
  vigente → reportarlos y sugerir moverlos a `.specify/agents/archivo/` — NUNCA
  borrarlos ni moverlos automáticamente.

## Paso 6 — Cierre

Resumen: tabla final de cobertura, archivos creados (rutas), huérfanos reportados,
y recordatorio de que las definiciones son editables (las ediciones manuales nunca se
pisan). Si el proyecto usa el README gestionado, sugerir `/speckit-readme` para
reflejar el equipo de agentes en el estado del proyecto.
