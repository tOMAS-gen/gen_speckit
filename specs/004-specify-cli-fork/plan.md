# Implementation Plan: Fork de specify-cli con mejoras multi-CLI integradas

**Branch**: `004-specify-cli-fork` | **Date**: 2026-07-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-specify-cli-fork/spec.md`

## Summary

Convertir gen_speckit en un **fork real del spec-kit oficial** (github/spec-kit, rama
`main` / v0.13.x) con las mejoras multi-CLI **integradas dentro del propio `specify-cli`**,
de modo que un único `specify init` deposite base + producto en un solo gesto —
eliminando el paso separado de `install.ps1`.

**Hallazgo de research que define el enfoque**: el spec-kit oficial abandonó (v0.4.0) el
modelo de descargar ZIPs de plantillas por agente y ahora **empaqueta las plantillas
dentro del wheel de Python** (`init` es offline, copia assets bundleados) y modela los
agentes como un **registry dinámico de integraciones** (`src/specify_cli/integrations/`,
una subclase por agente; `claude`, `codex`, `kimi` ya existen). La integración `claude`
usa `SkillsIntegration` → `.claude/skills/<nombre>/SKILL.md`, **el mismo formato** que las
8 skills actuales de gen_speckit. Por lo tanto el fork:

1. **Vendoriza** el paquete Python `specify-cli` de upstream (pineado a una versión) en el
   repo, con la capa multi-CLI en módulos/assets claramente separados.
2. **Integra el producto como assets bundleados** del wheel: las 8 skills se entregan por
   el mecanismo de integración del agente elegido; los playbooks del orquestador, los 6
   scripts PowerShell y el catálogo de CLIs se suman a los assets `.specify/` que `init`
   ya deposita.
3. **Mantiene el comando `specify`** y hace que el producto se instale **siempre** en el
   `init`, con elección de agente (claude/codex/kimi/todos). `install.ps1` se deprecia.
4. Redirige el auto-chequeo de versión (`_version.py`) al fork.

## Technical Context

**Language/Version**: Python ≥3.11 (paquete `specify-cli` vendorizado de upstream) +
PowerShell 5.1/7 (scripts de soporte del producto, ya existentes).

**Primary Dependencies**: las de upstream (`typer`, `click`, `rich`, `platformdirs`,
`readchar`, `pyyaml`, `packaging`, `pathspec`, `json5`); build backend `hatchling`.
Runtime del producto: `uv` + los CLIs de IA (claude/codex/kimi) con sus suscripciones (sin
API keys).

**Storage**: archivos (assets bundleados en el wheel; `.specify/`, `.claude|.codex|.kimi/`
en el proyecto destino). Sin base de datos.

**Testing**: `pytest` para el CLI vendorizado (suite de upstream + tests del wiring del
producto); Pester 3.4+ para los scripts PowerShell (suite existente 76/76).

**Target Platform**: Windows 11 (PowerShell 5.1/7); Linux y macOS con PowerShell 7. El
CLI Python es multiplataforma; los scripts de soporte corren en pwsh 7 en las tres.

**Project Type**: CLI tool (fork de una herramienta de línea de comandos Python) +
producto de assets Markdown/PowerShell portables.

**Performance Goals**: N/A (herramienta de scaffolding local; el `init` debe completar en
segundos, sin acceso de red gracias al bundling).

**Constraints**: compatibilidad total y aditiva con spec-kit (Principio I); sin API keys;
no romper la elección de agente ni las opciones oficiales del `init` (`--integration`,
`--script`, `--here`, `--force`, `--preset`, etc.); no pisar artefactos del usuario en el
destino (AGENTS.md, `.specify/` existente).

**Scale/Scope**: 1 paquete Python vendorizado (~40 módulos de integración de upstream, no
todos tocados), 8 skills, 6 scripts, playbooks del orquestador, 1 catálogo de CLIs, 1
mecanismo de bundling/preset del producto, documentación (README/distribución).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento en este plan |
|---|---|
| **I. Compatibilidad total aditiva** | El fork preserva TODO el comportamiento oficial (comandos base, `.specify/`, formato de artefactos, opciones del `init`). El producto se agrega como assets/integración bundleados; no modifica el formato oficial. ✅ La validación (quickstart) verifica que las skills base y comandos oficiales siguen igual. |
| **II. Portabilidad multi-CLI** | Los playbooks del orquestador y los scripts siguen siendo portables; que el CLI de scaffolding sea Python NO introduce dependencia exclusiva de un CLI de IA en el producto. El `init` entrega el producto al agente elegido (claude/codex/kimi/todos). ✅ |
| **III. El más barato que alcance** | No afectado: esta feature es empaquetado. El producto entregado (asignador/orquestador) mantiene su lógica intacta. ✅ |
| **IV. Nunca discriminar un modelo** | No afectado: se entrega `models.json`/`assign`/`orchestrate` sin cambios de lógica. ✅ |
| **V. Decisiones caras al más capaz** | No afectado por el empaquetado; el triage/asignador se entregan intactos. ✅ |
| **VI. Mínima intervención, gates reales** | Refuerza el principio: el gesto pasa de 2 pasos (init + install.ps1) a 1 (`specify init`). ✅ |

**Resultado del gate**: PASA. Sin violaciones que justificar → no se completa "Complexity
Tracking".

## Project Structure

### Documentation (this feature)

```text
specs/004-specify-cli-fork/
├── plan.md              # Este archivo
├── research.md          # Fase 0: hallazgos y decisiones (arquitectura upstream, enfoque de fork)
├── data-model.md        # Fase 1: entidades (fork, producto, integración, assets, destino)
├── quickstart.md        # Fase 1: escenarios de validación end-to-end
├── contracts/           # Fase 1: contrato del `specify init` del fork + contrato de entrega del producto
└── tasks.md             # Fase 2 (/speckit-tasks) — NO lo crea este comando
```

### Source Code (repository root) — estructura destino del fork

```text
gen_speckit/                        # el repo pasa a SER el fork (paquete instalable)
├── pyproject.toml                  # NUEVO: nombre `specify-cli`, entry-point `specify`, hatchling
├── src/
│   └── specify_cli/                # VENDORIZADO de upstream (pineado a vX.Y.Z) + capa gen
│       ├── ...                     # módulos de upstream (init, integrations/, bundler/, presets/, ...)
│       └── gen_multicli/           # NUEVO: capa propia (bundling del producto, preset "gen")
├── assets/ (o dentro del paquete)  # assets bundleados que el init deposita:
│   ├── skills-multicli/            #   las 8 skills (SKILL.md) del producto
│   ├── orchestrator/               #   playbooks portables (→ .specify/orchestrator/)
│   ├── scripts-powershell/         #   6 scripts de soporte (→ .specify/scripts/powershell/)
│   └── clis-catalog.json           #   catálogo de CLIs (→ .specify/)
├── tests/
│   ├── python/                     # NUEVO: pytest del wiring del producto (+ suite upstream)
│   └── powershell/                 # EXISTENTE: Pester de los scripts
├── UPSTREAM.md                     # NUEVO: versión pineada + procedimiento de sync con upstream
├── AGENTS.md                       # aporte multi-CLI (entrega no destructiva en el destino)
└── README.md                       # ACTUALIZADO: gesto de instalación de un solo paso

# Se conserva durante la transición (specs/, .specify/, .claude/ de DESARROLLO del repo
# actual) — NO se distribuyen al destino; la separación producto/desarrollo la define el
# bundling/manifiesto, igual que hoy install.ps1.
```

**Structure Decision**: El repositorio se convierte en el **paquete instalable del fork**:
raíz con `pyproject.toml` + `src/specify_cli/` vendorizado. La capa propia vive en un
submódulo `gen_multicli/` y en assets bundleados separados, para cumplir la separación
upstream/gen (FR-007) y permitir el sync documentado en `UPSTREAM.md`. La entrega del
producto por el `init` replica —ahora de forma nativa— la lógica no destructiva y de
elección de agente que hoy tiene `install.ps1`.

## Complexity Tracking

> Sin violaciones de la constitución que justificar. Sección no aplicable.
