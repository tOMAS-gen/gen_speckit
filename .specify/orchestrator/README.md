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
   siempre vía `invoke_secondary.py`, nunca directo).
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
| `dispatch-phase.md` | Despacho de una fase del pipeline a un modelo secundario, verificación y cierre |
| `report-template.md` | Plantilla del reporte de orquestación por feature |

## Datos que consumen

- `.specify/models.json` — inventario y ranking (generado por `/speckit-models`).
- `specs/<feature>/tasks.md` — tareas con etiquetas `[C:]`/`[M:]`.
- `specs/<feature>/orchestration-report.md` — estado y decisiones (creado desde
  `report-template.md`).

## Directorio `.phase-dispatch` — intermedios del despacho de fases

Cada feature puede contener un directorio `specs/<feature>/.phase-dispatch/` que
aloja los artefactos intermedios generados durante el despacho de una fase a un
modelo secundario (ver `dispatch-phase.md`).

### Convención de nombres

| Archivo | Descripción |
|---|---|
| `<fase>.prompt.md` | Instrucciones completas de la fase empaquetadas por el principal para enviarse al modelo secundario (identificación, entrada, restricciones, contexto por referencia). |
| `<fase>.questions.md` | Preguntas o hallazgos producidos por el modelo secundario en fases con interacción (clarify, analyze). Solo se genera si hay hallazgos relevantes. |
| `<fase>.answers.md` | Respuestas del usuario a las preguntas, redactadas por el principal durante la sesión interactiva. Usado por el despacho B del mismo modelo para integrar cambios. |

### Carácter de los intermedios

Estos archivos son **auditables pero no son el artefacto final de la fase**:

- El artefacto final oficial de cada fase es siempre el definido por spec-kit
  (`spec.md`, `plan.md`, `checklists/<nombre>.md`, `tasks.md`; analyze reporta en
  consola y sus correcciones quedan en los artefactos que toca).
- Los intermedios quedan para traza, reintento y retome — no escriben directamente
  el artefacto final.

### Logs de despacho

Cada invocación de `invoke_secondary.py` para una fase escribe un log en
`specs/<feature>/orchestration-logs/` con base name `fase-<nombre>`. Por ejemplo:

- `fase-plan.intento1.out.log`
- `fase-analyze.intento2.err.log`

El principal registra despachos, reintentos, escaladas y reasignaciones en Eventos
del reporte de orquestación.
