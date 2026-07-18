---
name: "speckit-orchestrate"
description: "Fase implement orquestada multi-CLI: lee tasks.md con etiquetas [C:]/[M:], despacha cada tarea a su CLI asignado (claude/codex/kimi) en modo headless, ejecuta [P] en paralelo, aplica fallback por cuota, verifica y marca [X]. Usar cuando el usuario invoca /speckit-orchestrate, o como fase implement de los pipelines auto cuando existe un tasks.md etiquetado y .specify/models.json."
argument-hint: "[sin argumentos — usa la feature activa de .specify/feature.json]"
compatibility: "Requiere estructura .specify/ de spec-kit, models.json generado y tasks.md etiquetado"
metadata:
  author: "gen_speckit"
user-invocable: true
disable-model-invocation: false
---

## Qué hace

Este comando es un **adaptador fino**: toda la lógica vive en el playbook portable
`.specify/orchestrator/orchestrate.md`. Leerlo COMPLETO y ejecutarlo paso a paso.

## Pasos

1. **Ubicar la feature**: leer `.specify/feature.json` → `feature_directory`. Si no
   existe, preguntar al usuario qué feature orquestar.
2. **Validar prerequisitos** (Paso 0 del playbook):
   - `specs/<feature>/tasks.md` existe y tiene etiquetas `[M:]` (si le faltan,
     ofrecer el playbook `.specify/orchestrator/assign.md` primero).
   - `.specify/models.json` existe y es válido (si no, ofrecer `/speckit-models`).
3. **Ejecutar el playbook** `.specify/orchestrator/orchestrate.md` de punta a punta:
   planificar tandas (`get-parallel-groups.ps1`), despachar (`invoke-secondary.ps1`),
   fallback (`update-quota.ps1` + reasignación), verificar (FR-019) y marcar `[X]`.
4. **Retome**: si hay tareas `[X]` previas, despachar solo las pendientes.
5. **Cierre**: reporte actualizado (Asignaciones, Eventos, Métricas) + resumen en
   consola.

## Reglas duras

- Solo este CLI (el principal) marca `[X]`, y solo tras la verificación estándar.
- El principal nunca se auto-invoca por headless: sus tareas van en sesión.
- Los secundarios corren con permisos totales DENTRO del repo (Clarificación S2);
  nunca fuera.
- Nada de frenar todo por una tarea bloqueada: se reporta y se sigue con el resto.
