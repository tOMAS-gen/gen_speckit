# Quickstart / Validación: Scripts de soporte en Python

**Feature**: 005-python-scripts-port | **Fecha**: 2026-07-18

## Prerrequisitos
- Python ≥3.11 (sin PowerShell para los escenarios de portabilidad).
- Para el despacho real: los CLIs claude/codex/kimi instalados.

## Escenario 1 — Correr sin PowerShell (US1, SC-001/SC-004)
```bash
# en un entorno SIN pwsh
python .specify/scripts/python/get_parallel_groups.py --tasks-path specs/<f>/tasks.md
python .specify/scripts/python/scan_models.py --models-path .specify/models.json --scan-path .specify/models.scan.json
```
**Esperado**: ambos completan sin error de intérprete; ningún componente invoca `pwsh`.

## Escenario 2 — Paridad de contratos (US2, SC-002)
```bash
# comparar salida de tandas Python vs. el contrato/última salida ps conocida
python .specify/scripts/python/get_parallel_groups.py --tasks-path specs/004-specify-cli-fork/tasks.md > /tmp/py.json
# verificar campos: total_tareas, grupos[].paralelo, tareas[].{id,complejidad,cli,modelo,rutas}
```
**Esperado**: mismos campos/estructura y agrupamiento equivalente al de `get-parallel-groups.ps1`.

## Escenario 3 — Despacho headless (US2/FR-006)
```bash
python .specify/scripts/python/invoke_secondary.py --cli codex --model gpt-5.5 \
  --prompt "echo test dentro del repo" --models-path .specify/models.json \
  --log-dir /tmp/logs --log-base-name SMOKE
```
**Esperado**: JSON `{clasificacion: exito|cuota_agotada|indisponible, ...}`; ejecuta dentro
del cwd; no vuelca credenciales a los logs.

## Escenario 4 — CRUD de CLIs y cuota (US2)
```bash
python .specify/scripts/python/clis_config.py --accion verificar --models-path .specify/models.json
python .specify/scripts/python/update_quota.py --cli kimi --estado agotada --models-path .specify/models.json
```
**Esperado**: reporte de validación coherente; `models.json` con `cuota` actualizada y
formato intacto.

## Escenario 5 — Tests (US3, SC-003)
```bash
uv run --no-project --with pytest python -m pytest tests/python/ -q
```
**Esperado**: la suite (incluida la cobertura de los 6 scripts) pasa sin PowerShell.

## Escenario 6 — Reconexión de invocadores (US3, SC-004)
Inspeccionar `assets/orchestrator/orchestrate.md` y las skills `speckit-models`/
`speckit-orchestrate`/`speckit-clis`: sus comandos apuntan a
`python .specify/scripts/python/...`, no a `.ps1`.

## Escenario 7 — Sin regresión en Windows (SC-005)
Repetir Escenarios 1–5 en Windows: mismo resultado (la migración no rompe el entorno que
ya funcionaba).

## Criterios de aceptación
- [ ] E1: corre sin pwsh (SC-001/SC-004)
- [ ] E2: paridad de contratos (SC-002)
- [ ] E3: despacho seguro (FR-006)
- [ ] E4: CRUD/cuota con formato intacto (SC-002)
- [ ] E5: pytest verde sin PowerShell (SC-003)
- [ ] E6: invocadores reconectados (SC-004)
- [ ] E7: sin regresión en Windows (SC-005)
