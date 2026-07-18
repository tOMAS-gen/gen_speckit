# Data Model: Fork de specify-cli con mejoras multi-CLI integradas

**Feature**: 004-specify-cli-fork | **Fecha**: 2026-07-18

> Esta feature es de empaquetado/distribución: las "entidades" son artefactos y
> configuraciones, no un modelo de dominio persistido. Se documentan sus atributos,
> relaciones y reglas de validación relevantes para tasks e implement.

## Entidad: Paquete del fork (`specify-cli` de gen)

Representa el paquete Python instalable derivado de upstream.

| Atributo | Valor / regla |
|---|---|
| nombre de paquete | `specify-cli` (conservado) |
| comando (entry-point) | `specify` → `specify_cli:main` |
| build backend | `hatchling` |
| Python requerido | ≥3.11 |
| fuente de instalación | `git+https://github.com/tOMAS-gen/gen_speckit.git` |
| versión upstream pineada | declarada en `UPSTREAM.md` (tag concreto) |
| auto-upgrade (`_version.py`) | apunta al fork, no a github/spec-kit |

**Reglas**: al instalar, reemplaza cualquier `specify` oficial en la máquina (FR-008). El
`init` no debe requerir red (assets bundleados).

## Entidad: Producto multi-CLI (conjunto aditivo entregado por el `init`)

Fuente de verdad = el manifiesto vigente de `install.ps1`. Composición:

| Componente | Cantidad | Destino en el proyecto |
|---|---|---|
| Skills multi-CLI | 8 | según agente: `.claude/skills/<n>/SKILL.md`, `.kimi/skills/<n>/SKILL.md`, `.codex/prompts/<n>.md` |
| Playbooks del orquestador | 1 carpeta | `.specify/orchestrator/` (triage, assign, orchestrate, report-template, README) |
| Scripts PowerShell de soporte | 6 | `.specify/scripts/powershell/` |
| Catálogo de CLIs | 1 | `.specify/clis-catalog.json` |
| Aporte a `AGENTS.md` | 1 | raíz del proyecto (no destructivo) |
| Exclusiones `.gitignore` | 3 | `.gitignore` del proyecto (append) |

**Skills (8)**: `speckit-models`, `speckit-clis`, `speckit-agents`, `speckit-readme`,
`speckit-orchestrate`, `speckit-constitution-plus`, `speckit-specify-auto`,
`speckit-specify-auto-eco`.

**Scripts (6)**: `platform.ps1`, `scan-models.ps1`, `invoke-secondary.ps1`,
`update-quota.ps1`, `get-parallel-groups.ps1`, `clis-config.ps1`.

**Reglas de validación**:
- El 100% de estos elementos debe quedar presente tras un único `init` (SC-002).
- El formato oficial de spec-kit no se toca (Principio I): las skills base y `.specify/`
  de upstream conviven sin modificación.
- La lista es la del manifiesto de `install.ps1`; si cambia, esta feature sigue esa fuente.

## Entidad: Integración de agente (mecanismo de upstream reutilizado)

Contrato de upstream (`src/specify_cli/integrations/base.py`) que el fork usa para entregar
las skills al agente elegido.

| Atributo | Descripción |
|---|---|
| `key` | id del CLI (`claude`/`codex`/`kimi`), coincide con el nombre |
| `config.folder` | carpeta destino (`.claude/`, `.codex/`, `.kimi/`) |
| `config.commands_subdir` | subcarpeta de skills/prompts |
| `registrar_config` | formato (markdown/skills), extensión (`/SKILL.md`) |
| `setup(...)` | instala archivos y crea carpetas destino |

**Regla de entrega por agente** (paridad con `install.ps1`):
- `claude` / `kimi`: SKILL.md tal cual → `.<agente>/skills/<nombre>/SKILL.md`.
- `codex`: prompt plano `.codex/prompts/<nombre>.md`, **quitando el frontmatter** y
  anteponiendo `# /<nombre>`.
- `todos`: los tres a la vez.
- default: el mismo agente elegido para las skills base (`--integration`).

## Entidad: Capa upstream

Los artefactos que provienen de github/spec-kit sin cambio de comportamiento (comandos
base, `.specify/memory|scripts|templates`, integraciones, bundler, presets).

**Reglas**: modificación mínima y localizada (idealmente solo `_version.py` + punto de
enganche del preset del producto); todo cambio listado en `UPSTREAM.md`.

## Entidad: Proyecto destino

La carpeta del usuario donde corre `specify init`.

**Estados / reglas de transición (no destructivas)**:
- destino vacío → `init` deposita base + producto.
- destino con `.specify/` previo → preservar lo existente, sumar/actualizar el producto.
- destino con `AGENTS.md` propio → no pisar; el aporte multi-CLI va a
  `AGENTS.gen-speckit.md` (o merge no destructivo).
- `.gitignore` → append de las 3 exclusiones si no están (`models.json`,
  `models.scan.json`, `specs/**/orchestration-logs/`).

## Relaciones

```
Paquete del fork (1) ── bundlea ──> Producto multi-CLI (1)
Paquete del fork (1) ── vendoriza ──> Capa upstream (1) ── pineada a ──> versión (UPSTREAM.md)
specify init ── usa ──> Integración de agente (1..3) ── deposita skills en ──> Proyecto destino
specify init ── deposita playbooks/scripts/catálogo en ──> Proyecto destino (.specify/)
```
