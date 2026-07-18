# Data Model: Especificador de Agentes y README del Proyecto

**Feature**: 002-agent-specifier | **Date**: 2026-07-18

Todas las entidades son archivos Markdown en el repo.

## 1. Definición portable de agente — `.specify/agents/<nombre>.md`

| Campo (frontmatter) | Tipo | Reglas |
|---|---|---|
| `name` | string kebab-case | único; coincide con el nombre de archivo |
| `dominio` | string | de la taxonomía base o dominio extra declarado; clave para la detección de cobertura |
| `rol` | string | una línea: qué es este agente |
| `origen` | `generado` \| `editado` | `generado` al crear; informativo (la regla dura es no sobrescribir existentes) |
| `fecha` | ISO date | de creación/última generación |

Cuerpo (secciones fijas): `## Responsabilidades`, `## Límites` (qué NO hace),
`## Instrucciones` (system prompt portable).

**Reglas**:
- `speckit-agents` NUNCA sobrescribe un archivo existente (R3); solo crea faltantes.
- Cobertura de dominio = existe algún archivo con ese `dominio` en su frontmatter.
- Huérfano = archivo cuyo `dominio` no aparece en el análisis del objetivo vigente;
  se reporta y se sugiere mover a `.specify/agents/archivo/` (nunca se borra solo).

## 2. Derivación nativa (Claude) — `.claude/agents/<nombre>.md`

Frontmatter: `name`, `description` (rol + dominio), cuerpo = Instrucciones +
Responsabilidades + Límites del portable. Se regenera SOLO junto con la creación del
portable correspondiente (misma corrida aprobada); si el usuario lo edita, queda suyo.

## 3. Taxonomía de dominios (Clarificación S3)

Base fija: `interfaz`, `servicios`, `datos`, `pruebas`, `documentacion`, `seguridad`,
`infraestructura`, `integraciones`. Extensibles: dominios extra derivados del objetivo
(kebab-case libre). La propuesta de cobertura evalúa TODA la base + extras detectados;
los dominios base no aplicables al objetivo se listan como "no aplica" con una línea
de justificación (hace SC-001 verificable).

## 4. Propuesta de cobertura (transitoria, en conversación)

Tabla presentada al usuario antes de escribir: dominio → estado (cubierto por X /
faltante / no aplica) → agente propuesto (nombre, rol, justificación). El usuario
aprueba todo, un subconjunto, o rechaza. Solo lo aprobado se materializa.

## 5. README gestionado — `README.md`

Secciones delimitadas por comentarios HTML (contrato readme-sections.md):

| Sección | Delimitador | Contenido |
|---|---|---|
| objetivo | `<!-- speckit:objetivo:inicio/fin -->` | qué se construye y para qué + fecha de actualización |
| alcance | `<!-- speckit:alcance:inicio/fin -->` | qué es / qué no es |
| estado | `<!-- speckit:estado:inicio/fin -->` | features en curso/completadas (derivado de specs/) |

**Reglas**: todo lo que está FUERA de los delimitadores es intocable; README sin
delimitadores → proponer inserción y pedir confirmación (FR-009); cada actualización
reescribe solo el interior de los delimitadores y actualiza la fecha (FR-008/FR-010).
