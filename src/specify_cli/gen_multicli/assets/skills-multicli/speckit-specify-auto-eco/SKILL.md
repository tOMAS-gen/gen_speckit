---
name: "speckit-specify-auto-eco"
description: "Pipeline económico de spec-kit: con una sola llamada /speckit-specify-auto-eco \"idea\" ejecuta el ciclo mínimo (specify → plan → tasks → gate → implement), sin las fases opcionales de calidad. Usar para features chicas, ideas claras o prototipos, o cuando el triage multi-CLI recomienda el flujo ECO."
argument-hint: "Descripción de la feature [-bypass] [--sin-implementar]"
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

El texto después de `/speckit-specify-auto-eco` es la **descripción de la feature**.
Si está vacío, preguntar qué se quiere construir antes de continuar.

**Flags soportados** (removerlos de la descripción antes de pasarla a las fases):

- `-bypass`: si no hay dudas reales pendientes, salta el gate previo a implement y las
  preguntas de discordancia del triage (cambia solo al flujo recomendado e informa).
  NUNCA salta dudas reales: con clarificaciones o hallazgos críticos pendientes, el
  pipeline frena igual.
- `--sin-implementar`: se detiene tras la fase Tasks (solo planificación).

## Pre-fase — Triage multi-CLI

Si existe `.specify/models.json`, ejecutar el playbook `.specify/orchestrator/triage.md`
ANTES de la Fase 1:

1. Clasifica la idea con la rúbrica, decide flujo recomendado y modelos por fase, y se
   autoevalúa respecto del punto de entrada (escalar/degradar).
2. Si el flujo recomendado es IDEAL y este pipeline es ECO: sin `-bypass` preguntar al
   usuario si cambiar a `/speckit-specify-auto`; con `-bypass` ejecutar las 7 fases del
   flujo IDEAL directamente e informarlo en el reporte.
3. Crea/actualiza `specs/<feature>/orchestration-report.md` desde
   `.specify/orchestrator/report-template.md`.
4. Sin `models.json` válido: informar, ofrecer `/speckit-models`, y preguntar si
   continuar sin triage (modo clásico). Nunca inventar inventario.

## Reglas generales del pipeline

1. **Orden estricto**: `specify → plan → tasks → [gate] → implement`. Sin fases
   opcionales (clarify, checklist, analyze) — ese es el punto del flujo ECO.
2. **Cada fase invoca la skill base correspondiente** (`speckit-specify`,
   `speckit-plan`, `speckit-tasks`, `speckit-implement`) siguiendo sus instrucciones
   completas. No reimplementar lo que la skill base hace.
3. **Una fase termina antes de empezar la siguiente.** Si una falla, detener,
   reportar estado y qué falta para retomar.
4. **Frenos solo ante dudas reales**: preguntas de clarificación que la skill specify
   genere, y el gate previo a implement. Nada más.
5. **Anunciar cada fase**: `▶ Fase N/4: <nombre>`.

## Retomabilidad

Antes de empezar, revisar `.specify/feature.json` y el directorio de la feature:

- **Artefactos completos existentes** (spec.md, plan.md, tasks.md): ofrecer continuar
  desde la primera fase faltante, sin rehacer trabajo completado.
- **Artefacto incompleto o corrupto** (no parsea, le faltan secciones obligatorias de
  su template): tratarlo como faltante — informar qué tiene de malo y ofrecer
  regenerarlo desde esa fase. NUNCA continuar en silencio sobre un artefacto inválido.
- **En implement**: retomar = despachar solo tareas sin `[X]`, reconstruyendo el
  estado desde `tasks.md` y el reporte de orquestación.

## Fases

### Fase 1/4 — Specify

Invocar `speckit-specify` con la descripción. Crea `specs/NNN-nombre/spec.md` y puede
hacer hasta 3 preguntas de clarificación — trasladarlas al usuario (son dudas reales).

**Ofrecimiento de agentes (solo idea compleja)**: si el triage clasificó la idea como compleja, ofrecer al usuario correr la skill `speckit-agents` (especificador de agentes; el análisis de cobertura es a nivel PROYECTO, no por feature) de forma opcional y no bloqueante — declinar continúa el pipeline sin efectos.

### Fase 2/4 — Plan

Invocar `speckit-plan`. Genera plan.md y los artefactos de diseño que correspondan.

### Fase 3/4 — Tasks (+ asignación multi-CLI)

Invocar `speckit-tasks`. Genera `tasks.md` con el formato estricto.

Si existe `.specify/models.json`: ejecutar después el playbook
`.specify/orchestrator/assign.md` (paso de asignación) con el modelo más capaz
disponible — clasifica `[C:]` y asigna `[M:]` a cada tarea. Advertir al usuario que
re-generar `tasks.md` pierde las etiquetas y exige re-asignar.

### Gate — Confirmación de implementación

Mostrar resumen: feature, tareas, historias, MVP sugerido, y (si hubo asignación) el
reparto por modelo.

- Con `--sin-implementar`: **terminar acá** con el reporte de planificación.
- Con `-bypass` y sin dudas pendientes: continuar sin preguntar.
- Si no: pedir confirmación explícita del usuario.

### Fase 4/4 — Implement

Con `tasks.md` etiquetado y `models.json` válido: invocar la skill
`speckit-orchestrate` (despacho multi-CLI según el playbook
`.specify/orchestrator/orchestrate.md`).

Sin etiquetas o sin inventario: invocar `speckit-implement` clásico (todo en este CLI)
e informar por qué.

## Reporte final

Al terminar (o detenerse): directorio y artefactos generados, fases completadas,
decisiones del triage, tareas completadas vs. pendientes, y próximo paso sugerido.
Actualizar `orchestration-report.md` en cada fase.

## Cuándo termina

- [ ] Fases ejecutadas en orden (o detenido en el gate por `--sin-implementar` / decisión del usuario)
- [ ] Ninguna duda real salteada (ni siquiera con `-bypass`)
- [ ] Reporte final entregado y orchestration-report.md actualizado
