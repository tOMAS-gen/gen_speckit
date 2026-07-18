# gen_speckit

<!-- speckit:objetivo:inicio -->
## Objetivo

Un **fork del [Spec Kit de GitHub](https://github.com/github/spec-kit)** con un
orquestador multi-CLI (Claude Code, Codex y Kimi) integrado dentro del propio
`specify-cli`: el usuario solo escribe la idea y el sistema clasifica su complejidad
(triage), elige el flujo y el modelo para cada fase y cada tarea, y despacha el trabajo
al modelo más económico que alcance — reservando los caros para las decisiones que lo
justifican. Un único `specify init` instala base + producto, y corre en cualquier
entorno con solo Python. Todo de forma estrictamente aditiva sobre spec-kit.

_Actualizado: 2026-07-18_
<!-- speckit:objetivo:fin -->

<!-- speckit:alcance:inicio -->
## Alcance

**Es**: fork de spec-kit con las mejoras multi-CLI dentro de `specify-cli` (un solo
`specify init`); skills y playbooks Markdown portables; scripts de soporte en **Python**
(multiplataforma); inventario y ranking de modelos (`models.json`); pipelines de una sola
llamada (IDEAL y ECO); asignación de tareas por complejidad; orquestación con despacho
headless, paralelismo y fallback por cuota; especificador de agentes y README gestionado.

**No es**: no modifica las skills base ni el formato de artefactos de spec-kit; no usa
API keys (solo los CLIs con sus suscripciones).

_Actualizado: 2026-07-18_
<!-- speckit:alcance:fin -->

<!-- speckit:estado:inicio -->
## Estado

| Feature | Fase | Avance |
|---|---|---|
| 001 — Orquestador Multi-CLI | Implementada | Despacho real a los 3 CLIs validado en producción |
| 002 — Especificador de Agentes y README | Implementada | 7 agentes del proyecto generados y aprobados |
| 003 — Soporte Genérico de CLIs y Multiplataforma | Implementada | Cualquier CLI registrable sin tocar código |
| 004 — Fork de specify-cli (init de un solo paso) | Implementada | `specify init` entrega base + producto, validado con el CLI real |
| 005 — Scripts de soporte en Python (multiplataforma) | Implementada | Corre con solo Python; CI verde en Windows/Linux/macOS |

_Actualizado: 2026-07-18_
<!-- speckit:estado:fin -->

## Instalación

```bash
# 1) Instalar (una sola vez por máquina; reemplaza al specify oficial):
uv tool install specify-cli --force --from git+https://github.com/tOMAS-gen/gen_speckit.git

# 2) En la carpeta de tu proyecto — un solo init instala TODO (base + multi-CLI):
specify init . --integration claude --script ps
```

Con `--skills claude|codex|kimi|todos` elegís a qué agente(s) van las skills multi-CLI
(por defecto, el mismo de `--integration`).

**Requisitos**: Python ≥3.11 (Windows / Linux / macOS), [uv](https://docs.astral.sh/uv/),
y los CLIs de IA instalados ([Claude Code](https://claude.com/claude-code), Codex CLI,
Kimi CLI).

## Qué lo diferencia del spec-kit original

Todo lo del spec-kit oficial funciona **exactamente igual** (mismas skills, mismos
artefactos, mismas opciones). gen_speckit **agrega** un sistema multi-CLI donde solo
ponés la idea:

- **Una sola llamada** ejecuta todo el circuito (triage → specify → … → implement).
- **Triage**: clasifica la complejidad de la idea y decide flujo (ECO/IDEAL) y qué
  modelo ejecuta cada fase.
- **Asignación por tarea**: cada tarea de `tasks.md` se etiqueta con complejidad
  (`[C:baja|media|alta]`) y modelo responsable (`[M:cli/modelo]`).
- **Orquestación**: despacha cada tarea a su CLI (Claude/Codex/Kimi) en headless, en
  paralelo cuando se puede, con fallback automático si un modelo agota cuota — el
  principal verifica e integra.
- **Objetivo**: reducir costo y uso — el grueso del trabajo va a los modelos económicos;
  los caros solo donde hacen la diferencia.

## Comandos

### Base (del spec-kit oficial)

| Comando | Qué hace |
|---|---|
| `/speckit-constitution` | Principios del proyecto |
| `/speckit-specify` | Crear la especificación |
| `/speckit-clarify` | Preguntas de clarificación |
| `/speckit-plan` | Plan de implementación |
| `/speckit-tasks` | Generar `tasks.md` |
| `/speckit-checklist` | Checklists de calidad |
| `/speckit-analyze` | Consistencia spec/plan/tasks |
| `/speckit-implement` | Ejecutar las tareas |
| `/speckit-converge` | Detectar trabajo faltante y sumarlo como tareas |
| `/speckit-taskstoissues` | Tareas → issues de GitHub |

### Multi-CLI (agregados por gen_speckit)

| Comando | Qué hace |
|---|---|
| `/speckit-specify-auto "idea"` | ⭐ **Todo el circuito con una sola llamada** (triage + 7 fases + orquestación) |
| `/speckit-specify-auto-eco "idea"` | Ciclo mínimo (4 fases) para ideas simples |
| `/speckit-models` | Inventario y ranking de CLIs/modelos → `.specify/models.json` (una vez por máquina) |
| `/speckit-clis` | Registrar / editar / verificar / dar de baja cualquier CLI |
| `/speckit-orchestrate` | Fase implement orquestada suelta (con `tasks.md` ya etiquetado) |
| `/speckit-agents` | Especificador de agentes del proyecto |
| `/speckit-readme` | README gestionado (objetivo / alcance / estado) |
| `/speckit-constitution-plus` | Constitution base + ofrece el especificador de agentes |

**Uso típico**: `/speckit-models` (una vez) → `/speckit-specify-auto "tu idea"` — el
resto lo decide el sistema. Flags de los pipelines: `-bypass` (no frena en el gate si no
hay dudas) y `--sin-implementar` (solo planificación).

---

Para el desarrollo del fork (relación con upstream, build, tests), ver
[`UPSTREAM.md`](UPSTREAM.md).
