# Instrucciones para agentes (Codex CLI / Kimi CLI)

Este repositorio es un proyecto **spec-kit** extendido con un **orquestador
multi-CLI**. Cualquier CLI de IA (Claude Code, Codex, Kimi) puede actuar como
**principal** del orquestador: la lógica es portable y vive en playbooks Markdown
neutrales — este archivo es solo el adaptador de entrada.

## Comandos del orquestador multi-CLI

Cuando el usuario pida alguna de estas acciones, leé COMPLETO el playbook indicado y
ejecutalo paso a paso (contrato de portabilidad en `.specify/orchestrator/README.md`):

| Pedido del usuario | Playbook a ejecutar |
|---|---|
| "triage de esta idea" / arranque de un pipeline auto | `.specify/orchestrator/triage.md` |
| "asignar modelos a las tareas" / paso post-tasks | `.specify/orchestrator/assign.md` |
| "orquestar la implementación" / speckit-orchestrate | `.specify/orchestrator/orchestrate.md` |

Datos que consumen: `.specify/models.json` (inventario; generarlo con
`.specify/scripts/powershell/scan-models.ps1` + declaración del usuario),
`specs/<feature>/tasks.md` (etiquetas `[C:]`/`[M:]`) y
`specs/<feature>/orchestration-report.md` (estado, creado desde
`.specify/orchestrator/report-template.md`).

## Reglas duras (idénticas para cualquier principal)

- Solo el principal marca `[X]` en `tasks.md`, y solo tras la verificación estándar
  (diff cumple la tarea + tests/build del proyecto si existen).
- Los CLIs secundarios se invocan SIEMPRE vía
  `.specify/scripts/powershell/invoke-secondary.ps1` (nunca directo) y no operan
  fuera del repositorio.
- El principal nunca se auto-invoca por headless: sus tareas asignadas las ejecuta en
  su propia sesión.
- La única escritura automática sobre `.specify/models.json` es el estado de cuota,
  vía `.specify/scripts/powershell/update-quota.ps1`.
- Las ediciones manuales del usuario (etiquetas en `tasks.md`, valores de
  `models.json`) siempre prevalecen.

## Flujos spec-kit

Los comandos spec-kit estándar (`specify`, `plan`, `tasks`, `implement`, etc.) están
definidos en `.claude/skills/speckit-*/SKILL.md` — son Markdown legible por cualquier
agente; los pipelines de una sola llamada son `speckit-specify-auto` (7 fases) y
`speckit-specify-auto-eco` (4 fases). Podés seguir esas instrucciones desde este CLI:
no dependen de features exclusivas de Claude.

## Skills de contexto de proyecto

Estas skills también son Markdown portable ejecutable desde cualquier CLI principal.

| Skill | Rol |
|---|---|
| speckit-agents | Analiza el objetivo del proyecto y genera las definiciones de agentes necesarias en .specify/agents/ (ver .claude/skills/speckit-agents/SKILL.md) |
| speckit-readme | Crea o actualiza el README.md con secciones gestionadas delimitadas preservando el contenido manual (ver .claude/skills/speckit-readme/SKILL.md) |
| speckit-constitution-plus | Ejecuta la fase constitution base y al terminar ofrece el especificador de agentes (ver .claude/skills/speckit-constitution-plus/SKILL.md) |
