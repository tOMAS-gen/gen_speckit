# Playbooks portables del orquestador multi-CLI

Esta carpeta contiene la **lógica core** del sistema multi-CLI de gen_speckit. Los
playbooks son Markdown neutral que cualquier CLI (Claude Code, Codex, Kimi) ejecuta
actuando como **principal**. Las skills/prompts de cada CLI son adaptadores finos que
solo dicen "leé y ejecutá el playbook X" — la lógica vive acá y en ningún otro lado.

## Contrato de portabilidad (Constitución II)

Un playbook SOLO puede asumir que el CLI principal sabe:

1. **Leer y escribir archivos** del repositorio.
2. **Ejecutar scripts PowerShell** de `.specify/scripts/powershell/`.
3. **Invocar comandos** de línea de comandos (para despachar a CLIs secundarios,
   siempre vía `invoke-secondary.ps1`, nunca directo).
4. **Razonar sobre instrucciones en Markdown** (clasificar, decidir, verificar).

Un playbook NUNCA puede:

- Referenciar herramientas, APIs o features exclusivas de un CLI (MCP de un
  proveedor, formatos de skill propietarios, flags no documentados en
  `contracts/headless-adapters.md` de la feature).
- Depender de que el principal sea un CLI específico.
- Invocar a un CLI secundario sin pasar por la plantilla `headless` de
  `.specify/models.json`.

## Archivos

| Archivo | Rol |
|---|---|
| `triage.md` | Clasificar la idea, elegir flujo (ECO/IDEAL) y modelo por fase, autoevaluar el punto de entrada |
| `assign.md` | Clasificar complejidad `[C:]` de cada tarea y asignar modelo `[M:]` |
| `orchestrate.md` | Despachar tareas a CLIs secundarios, paralelo, fallback, verificación, marcar `[X]` |
| `report-template.md` | Plantilla del reporte de orquestación por feature |

## Datos que consumen

- `.specify/models.json` — inventario y ranking (generado por `/speckit-models`).
- `specs/<feature>/tasks.md` — tareas con etiquetas `[C:]`/`[M:]`.
- `specs/<feature>/orchestration-report.md` — estado y decisiones (creado desde
  `report-template.md`).
