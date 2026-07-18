# Contrato: interfaz CLI e I/O de los scripts Python

**Feature**: 005-python-scripts-port

> Cada script Python DEBE ofrecer estos flags y producir estas salidas, preservando la
> semántica de su equivalente PowerShell. Invocación: `python .specify/scripts/python/<script>.py <args>`.

## `platform.py` (módulo helper, no CLI directo)
Funciones exportadas: `os_family()`, `expand_portable_path(p)`, `resolve_executable(name, exe_hints)`,
`run_process(command, timeout, out_file, err_file, work_dir) -> {exitCode, timedOut}`,
`write_utf8_nobom(path, content)`. Comportamiento equivalente a `platform.ps1`.

## `scan_models.py`
- **Flags**: `--models-path`, `--scan-path`, `[--repo-root]` (paths de salida).
- **Salida**: escribe `models.json` (inventario + ranking `asignacion`) y `models.scan.json`.
- **Regla**: detecta CLIs instalados (versión/auth/headless/modelos), combina con catálogo;
  respeta corrección manual previa del usuario si existe.

## `invoke_secondary.py`
- **Flags**: `--cli`, `--model`, `--prompt`, `--models-path`, `--log-dir`,
  `--log-base-name` (default `tarea`), `--timeout` (default 900), `[--working-directory]`.
- **Salida**: JSON `{clasificacion, intentos, exitCode, stdoutPath, stderrPath, comando}`;
  `clasificacion ∈ {exito, cuota_agotada, indisponible}`. Exit 0 solo si `exito`.
- **Reglas**: construye el comando desde la plantilla `headless` del inventario; sanitiza
  el prompt (colapsa whitespace, escapa comillas); resuelve el ejecutable a ruta completa;
  1 reintento ante fallo transitorio; NO filtra credenciales; ejecuta en `--working-directory`
  (dentro del repo).

## `update_quota.py`
- **Flags**: `--cli`, `--estado {ok,agotada}`, `--models-path`, `[--plan]`.
- **Salida**: `models.json` con `cuota` actualizada (+ `cuota_reset` calculado del plan).

## `get_parallel_groups.py`
- **Flags**: `--tasks-path`.
- **Salida**: JSON de tandas (ver data-model). Agrupa `[P]` sin conflicto de rutas
  (límite `max_concurrencia`, default 4); serializa el resto; respeta dependencias de fase.

## `clis_config.py`
- **Flags**: `--accion {agregar,editar,eliminar,verificar}`, más los campos del CLI
  (`--cli`, `--headless`, `--plan`, etc.) según acción; `--models-path`, `[--catalog-path]`.
- **Salida**: `models.json`/catálogo actualizado o reporte de validación; mismas
  validaciones que `clis-config.ps1`.

## Conformidad

- **Paridad (FR-003)**: salidas byte-comparables con la versión ps en casos equivalentes.
- **Portabilidad (FR-002)**: solo stdlib de Python; corre sin `pwsh`.
- **Seguridad (FR-006)**: `invoke_secondary.py` no filtra credenciales y ejecuta dentro del repo.
