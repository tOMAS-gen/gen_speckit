# Implementation Plan: Scripts de soporte del orquestador en Python (multiplataforma)

**Branch**: `005-python-scripts-port` | **Date**: 2026-07-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-python-scripts-port/spec.md`

## Summary

Portar los 6 scripts de soporte del orquestador multi-CLI de **PowerShell a Python**
(≈1321 líneas), reconectar los playbooks y skills que los invocan, y migrar los tests
Pester a pytest — para que el producto corra en **cualquier entorno con solo Python**, sin
`pwsh`, **preservando los contratos y el comportamiento** vigentes (features 001-003).

**Decisión de diseño (invocación)**: scripts Python **sueltos** en
`.specify/scripts/python/`, espejando el layout actual (`scripts/powershell/`), con un
`platform.py` helper importado por los demás. Los invocadores llaman
`python .specify/scripts/python/<script>.py <args>`. Es el port más fiel y de menor
riesgo: los scripts operan sobre archivos del proyecto (`models.json`, `tasks.md`,
reportes) y quedan self-contained en `.specify/`, sin acoplarse a la versión del paquete
instalado (a diferencia de `python -m specify_cli...`) ni ampliar la superficie del CLI
(a diferencia de subcomandos `specify ...`, que quedan como posible mejora futura).

## Technical Context

**Language/Version**: Python ≥3.11 (stdlib: `subprocess`, `shutil`, `json`, `re`,
`argparse`, `datetime`, `pathlib`). Sin dependencias nuevas de terceros.

**Primary Dependencies**: solo stdlib de Python + los CLIs de IA (claude/codex/kimi) para
el despacho headless. `pytest` para tests (ya en el proyecto).

**Storage**: archivos JSON/Markdown del proyecto (`models.json`, `clis-catalog.json`,
`tasks.md`, reportes, logs de orquestación).

**Testing**: `pytest` en `tests/python/` (reemplaza los Pester de `tests/powershell/`).

**Target Platform**: Windows / Linux / macOS — **solo Python**, sin PowerShell.

**Project Type**: scripts de soporte CLI (herramientas de línea de comandos que consumen y
producen los contratos de datos del orquestador).

**Performance Goals**: N/A (herramientas locales; despacho headless con timeout de 15 min
como hoy).

**Constraints**: paridad total de contratos y comportamiento (FR-003); mismas garantías de
seguridad en el despacho (FR-006); sin regresión en Windows (FR-009).

**Scale/Scope**: 6 scripts (~1321 líneas ps) → Python; playbooks (3) + skills (3)
reconectadas; tests Pester → pytest; assets del producto (bundling) actualizados.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento |
|---|---|
| **I. Compatibilidad total aditiva** | Los contratos de spec-kit y del orquestador NO cambian (formato de `models.json`, etiquetas, JSON de tandas, clasificaciones). Solo cambia el lenguaje de implementación. ✅ |
| **II. Portabilidad multi-CLI** | Refuerza el principio: el orquestador pasa a correr en cualquier entorno con solo Python; ninguna dependencia exclusiva de un CLI ni de un SO. ✅ |
| **III/IV/V** | La lógica de asignación/ranking/fallback se preserva idéntica (port, no rediseño). ✅ |
| **VI. Mínima intervención** | Sin cambios en el gesto del usuario. ✅ |
| **Restricción técnica (v1.1.0)** | Esta feature **implementa** la constitución recién amendada: scripts de soporte en Python. ✅ |

**Resultado**: PASA. Sin violaciones → sin "Complexity Tracking".

## Project Structure

### Documentation (this feature)

```text
specs/005-python-scripts-port/
├── plan.md · research.md · data-model.md · quickstart.md
├── contracts/            # contratos de cada script (CLI + I/O) — invariantes
└── tasks.md              # (/speckit-tasks)
```

### Source Code (repository root)

```text
.specify/scripts/
├── powershell/           # heredado (se conserva durante la transición; ya no es la vía)
└── python/               # NUEVO — la vía por defecto
    ├── platform.py           # helper: os, rutas portables, resolver ejecutable, subprocess+timeout
    ├── scan_models.py        # detección de CLIs/modelos/auth → models.json + ranking
    ├── invoke_secondary.py   # despacho headless: comando desde plantilla, timeout, clasificación, 1 retry
    ├── update_quota.py       # actualizar cuota + reset time en models.json
    ├── get_parallel_groups.py# parsear tasks.md → tandas [P]/serial (JSON)
    └── clis_config.py        # CRUD de CLIs en models.json/catálogo (agregar/editar/eliminar/verificar)

src/specify_cli/gen_multicli/assets/
├── scripts-python/       # NUEVO — los 6 scripts, bundleados para que specify init los deposite
├── scripts-powershell/   # heredado (transición)
└── orchestrator/         # playbooks: comandos reconectados a `python .../python/...`

tests/python/             # pytest de los 6 scripts (reemplaza tests/powershell Pester)
```

**Structure Decision**: nuevos `.specify/scripts/python/` como vía por defecto; el
bundling del producto (`gen_multicli/assets/scripts-python/`) y el instalador
(`_scripts.py`) se actualizan para depositarlos; los playbooks y skills se reconectan. Los
scripts PowerShell y sus tests se conservan durante la transición (FR-008) pero dejan de
ser la vía invocada.

## Complexity Tracking

> Sin violaciones de la constitución. Sección no aplicable.
