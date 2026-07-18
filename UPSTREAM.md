# Upstream: relación con github/spec-kit

Este repositorio es un **fork del spec-kit oficial** de GitHub con las mejoras multi-CLI
de gen integradas dentro del propio `specify-cli`. Este documento fija la versión pineada
del upstream y el procedimiento para incorporar actualizaciones sin rehacer la capa propia
(feature 004-specify-cli-fork, FR-007).

## Versión pineada

| Campo | Valor |
|---|---|
| Upstream | https://github.com/github/spec-kit |
| Tag pineado | `v0.13.0` |
| Fecha de release upstream | 2026-07-17 |
| Arquitectura | wheel-bundled + registry de integraciones (post v0.4.0) |
| Vendorizado en | `src/specify_cli/` |
| Fecha de vendorizado | 2026-07-18 |

> El tag puede actualizarse siguiendo el procedimiento de sync de abajo. Al hacerlo,
> actualizar esta tabla y re-aplicar el overlay de gen.

## Separación upstream / capa gen

Para que actualizar el upstream no obligue a rehacer la capa propia, los cambios de gen se
aíslan así:

| Capa | Ubicación | ¿Se toca al sincronizar upstream? |
|---|---|---|
| Upstream sin modificar | `src/specify_cli/` (todo salvo lo de abajo) | Se reemplaza por la versión nueva |
| Seam de gen | `src/specify_cli/gen_multicli/` | Se preserva; se re-valida el enganche |
| Assets del producto | `src/specify_cli/gen_multicli/assets/` | Se preservan |
| Diff mínimo sobre upstream | ver "Diff mínimo" | Se re-aplica a mano |

### Diff mínimo sobre archivos de upstream

- `src/specify_cli/_version.py` — `GITHUB_API_LATEST` y `_GITHUB_SOURCE_URL` apuntan al
  fork `tOMAS-gen/gen_speckit` (2 líneas).
- `src/specify_cli/commands/init.py` — 5 cambios aditivos:
  - helper `_resolve_skills_agents` nuevo;
  - opción `--skills` nueva en la firma de `init`;
  - paso de tracker `"multicli"` registrado en el loop de `tracker.add`;
  - bloque que llama `install_product` tras `ensure_constitution_from_template`;
  - panel "gen_speckit — Multi-CLI" al final del output del `init` (camino recomendado).

Todos los archivos bajo `src/specify_cli/gen_multicli/` y los tests en `tests/python/`
son NUEVOS; no tocan archivos de upstream.

## Mapeo interno del bundler (T006)

El upstream empaqueta los assets del core en el wheel vía `force-include` en su
`pyproject.toml` (sección `[tool.hatch.build.targets.wheel.force-include]`). Origen (dir
raíz del repo) → destino dentro del wheel:

| Origen (raíz del fork) | Destino en el wheel |
|---|---|
| `templates/*.md`, `templates/vscode-settings.json` | `specify_cli/core_pack/templates/` |
| `templates/commands/` | `specify_cli/core_pack/commands/` |
| `scripts/bash/`, `scripts/powershell/` | `specify_cli/core_pack/scripts/` |
| `extensions/{git,agent-context,assess,bug}/` | `specify_cli/core_pack/extensions/` |
| `workflows/speckit/` | `specify_cli/core_pack/workflows/speckit/` |
| `presets/lean/` | `specify_cli/core_pack/presets/lean/` |

Por eso vendorizar el fork exige traer, además de `src/specify_cli/`, los dirs raíz
`templates/`, `scripts/`, `extensions/`, `workflows/`, `presets/` (hecho en T003). El
`init` lee estos assets desde el paquete instalado (`core_pack/`), sin red.

**Implicancia para el producto (T008)**: los assets de gen se agregan al `force-include`
para que también viajen en el wheel; el hook del producto (T010+) los deposita en el
proyecto destino tras el scaffolding base.

## Procedimiento de sync con upstream

1. Traer la versión nueva del upstream al tag deseado (clon/tarball de `github/spec-kit`).
2. Reemplazar `src/specify_cli/` **excepto** `gen_multicli/`.
3. Re-aplicar el "Diff mínimo sobre archivos de upstream" (lista de arriba).
4. Re-validar el enganche del producto en el flujo de `init`.
5. Correr la suite (`pytest tests/python/` + Pester `tests/powershell/`) y el quickstart.
6. Actualizar la tabla "Versión pineada" con el nuevo tag y fecha.

## Scripts de soporte: Python (multiplataforma)

Los scripts de soporte del orquestador ahora residen en `.specify/scripts/python/`:
- Están escritos en Python puro.
- Corren en cualquier entorno con solo Python, sin necesidad de PowerShell.

Los scripts ubicados en `.specify/scripts/powershell/` son **heredados** y se conservan
únicamente durante el período de transición; ya no son la vía invocada por defecto.

Los playbooks y skills del proyecto invocan la versión Python de los scripts de soporte.
