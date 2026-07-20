# Implementation Plan: Descubrimiento y verificación real de modelos por CLI

**Branch**: `006-model-discovery` | **Date**: 2026-07-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-model-discovery/spec.md`

## Summary

Mejorar `/speckit-models` para que los modelos del inventario salgan de **evidencia real**
y no solo de semillas: (1) detección local por CLI vía los mecanismos que cada CLI ofrezca
— declarados en el catálogo (comando de listado si existe, archivos de configuración
local, sondeo opt-in); (2) verificación **best-effort contra fuentes oficiales** hecha por
el agente que ejecuta la skill (el único que navega); (3) contrato `models.json` extendido
de forma aditiva con `esfuerzos` y `origen` por modelo. Por decisión del usuario
(Clarifications), **todos los orígenes participan del ranking**; la indisponibilidad real
la absorbe el fallback del orquestador.

**Hallazgo de research que define el enfoque**: ninguno de los 3 CLIs (claude 2.1.214,
codex 0.144.5, kimi 0.27.0) expone hoy un comando headless de listado de modelos (`--help`
solo muestra `--model` para elegir). Por lo tanto la detección local se apoya en:
- **`modelos_cmd`** (catálogo, opcional): para CLIs futuros/terceros que sí lo tengan.
- **`config_hints`** (catálogo): archivos de configuración locales del CLI que declaran
  modelos/aliases (p. ej. `config.toml` de kimi/codex, settings de claude) — gratis, sin
  cuota.
- **Sondeo opt-in** (`--probe-models`): invocación mínima solo con aprobación (FR-006).

## Technical Context

**Language/Version**: Python ≥3.11 (extiende `scan_models.py`, solo stdlib; parseo TOML
con `tomllib` de stdlib). Skill en Markdown (la parte web la hace el agente).

**Primary Dependencies**: ninguna nueva. `tomllib`/`json`/`re` de stdlib.

**Storage**: `models.json` (campos aditivos), `clis-catalog.json` (campos aditivos),
`models.scan.json` (línea base del merge, sin cambios de semántica).

**Testing**: pytest en `tests/python/` (extiende `test_scan_models.py` + tests nuevos de
detección por config y merge de orígenes).

**Target Platform**: Windows / Linux / macOS, solo Python (regla constitucional v1.1.0).

**Project Type**: extensión de scripts de soporte + skill + contrato de datos.

**Performance Goals**: N/A (escaneo local en segundos; web best-effort).

**Constraints**: contrato aditivo (SC-005, Principio I aplicado a contratos propios);
merge manual del usuario prevalece (FR-008); sin gasto de cuota por defecto (FR-006);
nunca inventar modelos (FR-005).

**Scale/Scope**: 1 script extendido, 1 catálogo extendido (3 CLIs conocidos), 1 skill
actualizada, ~4 tests nuevos, doc del contrato.

## Constitution Check

| Principio | Cumplimiento |
|---|---|
| I. Compatibilidad aditiva | Campos nuevos opcionales en `models.json`/catálogo; consumidores actuales intactos (SC-005). ✅ |
| II. Portabilidad multi-CLI | Detección genérica vía catálogo (sin nombres hardcodeados); la parte web la hace cualquier agente principal. ✅ |
| III. El más barato que alcance | Mejora la materia prima del ranking (modelos reales); sin gasto de cuota por defecto. ✅ |
| IV. Nunca discriminar | Todos los orígenes entran al ranking (decisión del usuario); el fallback resuelve indisponibles. ✅ |
| V. Decisiones caras al más capaz | Sin cambios al triage/asignador. ✅ |
| VI. Mínima intervención | El escaneo sigue siendo un comando; el sondeo con cuota es opt-in explícito. ✅ |

**Gate**: PASA. Sin violaciones.

## Project Structure

### Documentation (this feature)

```text
specs/006-model-discovery/
├── plan.md · research.md · data-model.md · quickstart.md
├── contracts/model-discovery.md   # extensión de catálogo + models.json + flujo skill
└── tasks.md                       # (/speckit-tasks)
```

### Source Code (repository root)

```text
.specify/scripts/python/scan_models.py        # + detect_models(): modelos_cmd → config_hints → semillas; origen/esfuerzos
.specify/clis-catalog.json                    # + modelos_cmd?, config_hints?, fuentes_oficiales? por CLI
.claude/skills/speckit-models/SKILL.md        # + paso de verificación oficial (agente) y presentación de estados
src/specify_cli/gen_multicli/assets/          # espejos shippeables de los tres anteriores
tests/python/test_scan_models.py (+ nuevos)   # detección por config (mock), merge de orígenes, contrato aditivo
```

**Structure Decision**: la detección local vive en `scan_models.py` (datos del catálogo,
nada hardcodeado); la verificación web vive en la skill (el agente navega y aplica el
resultado con el propio script para respetar el merge). Ambas copias (dev + assets
shippeables) se actualizan juntas.

## Complexity Tracking

> Sin violaciones. No aplica.
