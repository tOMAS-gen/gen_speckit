---
name: "speckit-specify-auto"
description: "Pipeline automatizado de spec-kit: con una sola llamada /speckit-specify-auto \"idea\" ejecuta todo el circuito en orden, incluidas las fases opcionales (specify → clarify → plan → checklist → tasks → analyze → implement), con puntos de control con el usuario. Usar cuando el usuario invoca /speckit-specify-auto con la descripción de una feature, o pide correr el flujo completo de spec-kit de forma automática."
argument-hint: "Descripción de la feature a construir [--sin-implementar]"
compatibility: "Requiere estructura de proyecto spec-kit con directorio .specify/ y las skills base speckit-* instaladas"
metadata:
  author: "gen_speckit"
user-invocable: true
disable-model-invocation: false
---

## Entrada del usuario

```text
$ARGUMENTS
```

El texto que el usuario escribió después de `/speckit-specify-auto` es la **descripción de la feature**. Si está vacío, preguntar qué se quiere construir antes de continuar.

**Flags soportados** (removerlos de la descripción antes de pasarla a las fases):

- `--sin-implementar`: el pipeline se detiene después de la fase Analyze (solo planificación). El usuario ejecuta `/speckit-implement` después, cuando quiera.
- `-bypass`: si no hay dudas reales pendientes, salta el gate de confirmación previo a implement y también las preguntas de discordancia del triage (cambia solo al flujo recomendado e informa). NUNCA salta dudas reales (clarificaciones, hallazgos críticos): con dudas pendientes el pipeline frena igual.

## Reglas generales del pipeline

1. **Ejecutar las fases estrictamente en este orden**, sin saltear ninguna:
   `specify → clarify → plan → checklist → tasks → analyze → [gate] → implement`
2. **Cada fase se ejecuta invocando la skill base correspondiente** (`Skill` tool: `speckit-specify`, `speckit-clarify`, etc.) y siguiendo sus instrucciones completas. No reimplementar lo que la skill base ya hace.
3. **Una fase debe terminar exitosamente antes de empezar la siguiente.** Si una fase falla o queda bloqueada, detener el pipeline, reportar el estado y qué falta para retomar.
4. **La interacción con el usuario ocurre solo donde corresponde**: las preguntas de clarificación de specify/clarify, los hallazgos críticos de analyze y el gate previo a implement. No pedir confirmación entre las demás fases — encadenarlas automáticamente.
5. **Anunciar cada fase** antes de ejecutarla con una línea breve: `▶ Fase N/7: <nombre>` — para que el usuario sepa siempre dónde está el pipeline.
6. **Retomable**: antes de empezar, revisar `.specify/feature.json` y el directorio de la feature en `specs/`. Si ya existen artefactos de fases previas (spec.md, plan.md, tasks.md...), preguntar al usuario si desea retomar desde la primera fase faltante o empezar una feature nueva. Un artefacto incompleto o corrupto (no parsea, le faltan secciones obligatorias de su template) se trata como faltante: informar qué tiene de malo y ofrecer regenerarlo desde esa fase — nunca continuar en silencio sobre un artefacto inválido. En implement, retomar = despachar solo tareas sin `[X]`, reconstruyendo el estado desde `tasks.md` y el reporte de orquestación.

## Pre-fase — Triage multi-CLI (antes de ejecutar cualquier fase)

Si existe `.specify/models.json`, ejecutar el playbook `.specify/orchestrator/triage.md`
ANTES de la Fase 1:

1. El triage clasifica la idea (simple/media/compleja) con la rúbrica del playbook,
   decide el flujo recomendado (ECO/IDEAL) y qué modelo ejecuta cada fase, y se
   autoevalúa respecto del punto de entrada (escalar/degradar).
2. Crea/actualiza `specs/<feature>/orchestration-report.md` desde
   `.specify/orchestrator/report-template.md` (el reporte se crea apenas exista el
   directorio de la feature, tras la fase specify, si aún no existe).
3. Si el flujo recomendado es ECO y este pipeline es IDEAL: sin `-bypass` preguntar al
   usuario si cambiar a `/speckit-specify-auto-eco`; con `-bypass` continuar
   directamente con el ciclo mínimo (specify → plan → tasks → gate → implement,
   omitiendo clarify/checklist/analyze) e informarlo en el reporte.
4. Si `.specify/models.json` NO existe o es inválido: informarlo, ofrecer correr
   `/speckit-models` primero, y preguntar si continuar sin triage (modo spec-kit
   clásico, todas las fases en este CLI). Nunca inventar un inventario.

## Fases

### Fase 1/7 — Specify

Invocar la skill `speckit-specify` pasando la descripción de la feature como argumento. Esta fase crea `specs/NNN-nombre/spec.md`, valida calidad y puede hacer hasta 3 preguntas de clarificación — esperarlas y trasladarlas al usuario tal como la skill lo indica.

**Ofrecimiento de agentes (solo idea compleja)**: si el triage clasificó la idea como compleja, ofrecer al usuario correr la skill `speckit-agents` (especificador de agentes; el análisis de cobertura es a nivel PROYECTO, no por feature) de forma opcional y no bloqueante — declinar continúa el pipeline sin efectos.

### Fase 2/7 — Clarify (opcional, siempre incluida en este pipeline)

Invocar la skill `speckit-clarify`. Hacer al usuario las preguntas dirigidas que genere (máx. 5) y asegurarse de que las respuestas queden codificadas en el spec.

### Fase 3/7 — Plan

Invocar la skill `speckit-plan`. Genera `plan.md`, `research.md`, `data-model.md`, `contracts/` y `quickstart.md`. Si el spec del proyecto no requiere alguno de esos artefactos, la skill base lo decide — no forzarlos.

### Fase 4/7 — Checklist (opcional, siempre incluida en este pipeline)

Invocar la skill `speckit-checklist`. Si el usuario no especificó qué dimensiones auditar, generar un checklist de calidad de requisitos general (completitud, claridad, consistencia). Reportar el resultado del checklist al usuario.

### Fase 5/7 — Tasks

Invocar la skill `speckit-tasks`. Genera `tasks.md` con el formato estricto (`- [ ] T001 [P] [US#] descripción con ruta`), fases y dependencias.

**Paso de asignación multi-CLI**: si existe `.specify/models.json`, ejecutar después
el playbook `.specify/orchestrator/assign.md` con el modelo más capaz disponible —
clasifica cada tarea (`[C:baja|media|alta]`) y le asigna modelo (`[M:cli/modelo]`)
inline, sin tocar el formato oficial. Advertir al usuario que re-generar `tasks.md`
pierde las etiquetas y exige re-asignar (playbook en modo directo).

### Fase 6/7 — Analyze (opcional, siempre incluida en este pipeline)

Invocar la skill `speckit-analyze` para verificar consistencia entre spec.md, plan.md y tasks.md.

- **Sin hallazgos críticos**: continuar.
- **Con hallazgos críticos**: mostrarlos al usuario y ofrecer: (a) corregir los artefactos y re-analizar, o (b) continuar igual. No avanzar sin respuesta del usuario.

### Gate — Confirmación de implementación

Mostrar un resumen: feature, cantidad de tareas, historias de usuario, alcance MVP sugerido y estado de checklists.

- Si el usuario pasó `--sin-implementar`: **terminar aquí** con el reporte final de planificación e indicar que puede ejecutar `/speckit-implement` cuando quiera.
- Si no: preguntar al usuario si desea proceder con la implementación. Solo continuar con confirmación explícita.

### Fase 7/7 — Implement

- **Con `tasks.md` etiquetado (`[M:]`) y `.specify/models.json` válido**: invocar la
  skill `speckit-orchestrate` — despacho multi-CLI según el playbook
  `.specify/orchestrator/orchestrate.md` (paralelo, fallback por cuota, verificación
  del principal, `[X]` solo verificadas).
- **Sin etiquetas o sin inventario**: invocar la skill `speckit-implement` clásica
  (todo en este CLI) e informar por qué se usó el modo clásico.

## Reporte final

Al terminar (o al detenerse), reportar:

- Directorio de la feature y artefactos generados (con rutas)
- Fases completadas y fase donde se detuvo (si aplica)
- Resultado de checklists y analyze
- Tareas completadas vs. pendientes (si se llegó a implement)
- Próximo paso sugerido

## Cuándo termina

- [ ] Todas las fases ejecutadas en orden (o pipeline detenido en el gate por `--sin-implementar` / decisión del usuario)
- [ ] Ninguna fase salteada silenciosamente
- [ ] Reporte final entregado al usuario
