# Research: Scripts de soporte del orquestador en Python

**Feature**: 005-python-scripts-port | **Fecha**: 2026-07-18

## Decisión 1 — Mecanismo de invocación

- **Decisión**: scripts Python **sueltos** en `.specify/scripts/python/<script>.py`,
  invocados como `python .specify/scripts/python/<script>.py <args>` con `argparse`. Un
  `platform.py` helper (importable) concentra os/rutas/subprocess.
- **Rationale**: espeja el layout PowerShell actual (mínimo cambio en playbooks/skills);
  self-contained en el `.specify/` del proyecto; testeable en aislamiento; no acopla el
  runtime a la versión del paquete instalado.
- **Alternativas**: `python -m specify_cli.gen_multicli.<mod>` (acopla a la versión
  instalada; complica tests locales) y subcomandos `specify ...` (más superficie de CLI y
  más trabajo) — descartadas para el port; el subcomando queda como posible mejora futura.

## Decisión 2 — Mapeo ps→py (paridad de comportamiento, FR-003)

| Script PowerShell (líneas) | Script Python | Notas de port |
|---|---|---|
| `platform.ps1` (140) | `platform.py` | `subprocess.run(timeout=)`, `shutil.which`, expansión de `~`/env vars, escritura UTF-8 sin BOM. Python nativo simplifica el helper. |
| `scan-models.ps1` (368) | `scan_models.py` | Detección de CLIs (versión, auth), lectura de catálogo, armado de `models.json` + ranking. Preservar campos y estructura. |
| `invoke-secondary.ps1` (169) | `invoke_secondary.py` | Comando desde plantilla `headless`, sanitizado del prompt, timeout 900s, 1 retry, clasificación `exito`/`cuota_agotada`/`indisponible`. |
| `update-quota.ps1` (76) | `update_quota.py` | Set de estado de cuota + `cuota_reset` según plan. |
| `get-parallel-groups.ps1` (124) | `get_parallel_groups.py` | Parseo de `tasks.md`, etiquetas `[P]`/`[C:]`/`[M:]`, agrupamiento por conflicto de rutas, JSON idéntico. |
| `clis-config.ps1` (444) | `clis_config.py` | CRUD `agregar/editar/eliminar/verificar` sobre `models.json`/catálogo, con validaciones. |

- **Regla de paridad**: las salidas (JSON, strings de clasificación, formato de
  `models.json`) deben ser byte-comparables con la versión PowerShell en casos
  equivalentes. Los tests portados fijan esta paridad.

## Decisión 3 — Preservar garantías de seguridad del despacho (FR-006)

- `invoke_secondary.py` DEBE: ejecutar dentro del repo (cwd controlado), NO filtrar
  credenciales (no volcar env sensible a logs), aplicar timeout y 1 retry, y clasificar
  cuota por los patrones del inventario/catálogo. Mismo contrato que `headless-adapters`.
- **Rationale**: es el punto más sensible (permisos totales del secundario). El dominio del
  agente `revisor-despachos` cubre esta verificación.

## Decisión 4 — Reconexión de invocadores (FR-004)

- **Playbooks** (`assets/orchestrator/orchestrate.md`, `assign.md`, `triage.md`): cambiar
  los ejemplos de comando de `.specify/scripts/powershell/*.ps1` a
  `python .specify/scripts/python/*.py`.
- **Skills** (`speckit-models`, `speckit-orchestrate`, `speckit-clis`): idem en sus
  referencias a scripts.
- **Bundling** (`_scripts.py` + `assets/scripts-python/`): el instalador deposita
  `.specify/scripts/python/`; durante la transición puede seguir depositando también
  `powershell/` (FR-008).

## Decisión 5 — Migración de tests (FR-005)

- **Decisión**: reescribir los Pester de `tests/powershell/` como pytest en
  `tests/python/`, un módulo por script, cubriendo los mismos casos (parseo de tandas,
  clasificación de resultado, CRUD de CLIs, actualización de cuota, resolución de
  ejecutable).
- **Rationale**: sin PowerShell en CI para estos scripts; una sola suite (pytest) para
  todo el fork.
- **Nota**: los Pester heredados se conservan durante la transición pero no son la vía de
  validación por defecto.

## Riesgos / puntos abiertos

- `scan_models.py` y `clis_config.py` son los más grandes (detección + CRUD con
  validaciones) → mayor superficie de paridad; tests exhaustivos.
- Detección de CLIs depende de ejecutar `--version`/auth de cada CLI: mockear en tests.
- Verificar en Windows que no hay regresión (FR-009) además de Linux/macOS.
