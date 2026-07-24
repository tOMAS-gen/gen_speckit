# Implementation Plan: Despacho multi-modelo de todas las fases

**Branch**: `feat/007-arena-model-ranking` (trabajo actual) | **Date**: 2026-07-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-multi-model-phase-dispatch/spec.md`

## Summary

Hoy la tabla "Modelos por fase" del reporte de orquestación es decisión sin ejecución:
todas las fases corren en el principal y el único reparto real ocurre en implement.
Esta feature materializa el reparto en todo el pipeline: (1) un playbook nuevo
`dispatch-phase.md` + extensiones a los pipelines auto para que cada fase no
interactiva se ejecute vía headless en el modelo que el triage le asignó, con
verificación del principal y fallback acotado; (2) `invoke_secondary.py` gana
`--prompt-file` (instrucciones largas por archivo, evitando el límite de ~8191
caracteres de `cmd.exe` y el aplanado de whitespace); (3) el inventario gana
`deshabilitado` por modelo individual (hoy solo existe por CLI) y un campo
`preferido` de alcance usuario para restringir el trabajo a un agente concreto;
(4) el reporte registra modelo asignado vs. efectivo por fase y métricas de ahorro
del pipeline completo. Todo reutiliza los mecanismos existentes: mismo despachador,
mismos contratos de log/clasificación, mismos rankings (`asignacion` /
`asignacion_por_fase`), sin canal paralelo.

## Technical Context

**Language/Version**: Python ≥3.11 (scripts de soporte) + Markdown portable (playbooks/skills)

**Primary Dependencies**: stdlib only (json, subprocess, argparse, re, pathlib) — regla existente de los scripts del orquestador

**Storage**: archivos del repo (`.specify/models.json`, `.specify/clis-catalog.json`, `specs/<feature>/orchestration-report.md`, `specs/<feature>/.phase-dispatch/` para prompts/artefactos intermedios)

**Testing**: pytest (`tests/python/`, corrida con `python -m pytest tests/python`)

**Target Platform**: Windows / Linux / macOS (multiplataforma; límite de línea de comandos de Windows es restricción de diseño)

**Project Type**: CLI tooling + playbooks Markdown (fork de spec-kit)

**Performance Goals**: sin metas de latencia; el costo dominante es el consumo de cuota de modelos (SC-004: reducir uso del modelo caro en fases)

**Constraints**: prompts headless por `cmd.exe` limitados a ~8191 chars (motiva `--prompt-file`); `get_headless_command` aplana whitespace (los prompts de fase requieren instrucciones multilínea → archivo); el principal nunca se auto-invoca headless; solo el principal escribe `tasks.md`/reporte

**Scale/Scope**: 5–7 fases por pipeline, 1 despacho (o 2 para fases con integración de respuestas) por fase; inventario típico de 3–6 agentes con 3–8 modelos cada uno

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Evaluación | Estado |
|---|---|---|
| I. Compatibilidad solo aditiva | Campos nuevos del inventario (`deshabilitado` por modelo, `preferido`) son aditivos; `--prompt-file` es un flag nuevo opcional; los pipelines siguen funcionando sin inventario (modo clásico, FR-013); formato oficial de artefactos intacto | ✅ |
| II. Portabilidad multi-CLI | El despacho de fases se define en un playbook Markdown neutral (`dispatch-phase.md`) ejecutable por cualquier principal; invocaciones solo vía `invoke_secondary.py`; sin features exclusivas de un CLI | ✅ |
| III. El más barato que alcance | Es el objetivo central: fases de producción a modelos económicos; fases de criterio a `alta` (FR-005a) | ✅ |
| IV. Nunca discriminar un modelo | `deshabilitado`/`preferido` son decisiones del USUARIO (prevalecen por regla); el sistema en sí sigue sin excluir; el reporte registra cuando una restricción es del usuario (FR-008b) | ✅ |
| V. Decisiones caras al modelo más capaz | Triage/asignación sin cambios; fases de criterio (clarify, analyze, tasks:asignación) exigen candidatos de `alta` (FR-005a) | ✅ |
| VI. Mínima intervención, gates reales | Despacho automático con inventario válido (FR-013); fallback sin preguntar (FR-004); interacción solo en clarify/analyze/gates vía principal (FR-005); retomable (FR-012) | ✅ |
| Restricción técnica: Python, sin PowerShell | Cambios de scripts solo en `.specify/scripts/python/`; stdlib | ✅ |

**Post-diseño**: re-evaluado tras Phase 1 — sin violaciones; no se requiere Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/008-multi-model-phase-dispatch/
├── plan.md              # Este archivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── phase-dispatch.md        # Contrato de despacho de fase (prompt, artefactos, verificación)
│   ├── inventory-fields.md      # Campos nuevos del inventario (deshabilitado por modelo, preferido)
│   └── prompt-file.md           # Contrato --prompt-file de invoke_secondary.py
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
.specify/
├── orchestrator/
│   ├── dispatch-phase.md        # NUEVO playbook: despacho de una fase a un secundario
│   ├── triage.md                # MOD: quitar "modo decisión-solo" como default; referir dispatch-phase
│   ├── assign.md                # MOD: respetar deshabilitado por modelo y preferido
│   └── orchestrate.md           # MOD: respetar deshabilitado por modelo y preferido; prompts largos por archivo
├── scripts/python/
│   ├── invoke_secondary.py      # MOD: --prompt-file (lee archivo, valida tamaño, sin aplanar el contenido referenciado)
│   ├── scan_models.py           # MOD: build_asignacion/build_asignacion_por_fase filtran modelos deshabilitados; preservar campos nuevos
│   ├── clis_config.py           # MOD: acciones para deshabilitar/habilitar modelo individual y fijar/quitar preferido
│   └── phase_candidates.py      # NUEVO: resolver candidatos efectivos de una fase (ranking + deshabilitados + preferido + cuota)
└── clis-catalog.json            # SIN CAMBIOS de esquema (los campos nuevos viven en models.json)

.claude/skills/
├── speckit-specify-auto/SKILL.md      # MOD: fases despachables vía dispatch-phase.md cuando hay inventario
├── speckit-specify-auto-eco/SKILL.md  # MOD: ídem para el ciclo mínimo
└── speckit-clis/SKILL.md              # MOD: gestión de habilitado por modelo y preferido

src/specify_cli/gen_multicli/assets/   # MOD: sincronizar copias empaquetadas de los archivos anteriores

tests/python/
├── test_prompt_file.py            # NUEVO: --prompt-file (lectura, tamaño, errores)
├── test_phase_candidates.py       # NUEVO: resolución de candidatos (deshabilitado, preferido, vacío)
├── test_modelo_deshabilitado.py   # NUEVO: filtrado en build_asignacion/por_fase + merge preserva flags
└── (existentes)                   # test_invoke_secondary, test_scan_models, test_clis_config: casos nuevos
```

**Structure Decision**: se mantiene la arquitectura existente del orquestador — lógica
de decisión en playbooks Markdown portables (`.specify/orchestrator/`), mecánica
determinista en scripts Python con stdlib (`.specify/scripts/python/`), adaptadores
finos en skills. El único módulo nuevo de código es `phase_candidates.py` (resolución
de candidatos, lógica pura y testeable); el despacho de fase en sí es un playbook
porque requiere juicio del principal (verificación de contenido), no un script.

## Complexity Tracking

Sin violaciones constitucionales que justificar.
