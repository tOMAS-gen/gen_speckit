# Implementation Plan: Soporte Genérico de CLIs y Multiplataforma

**Branch**: `003-generic-cli-support` | **Date**: 2026-07-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-generic-cli-support/spec.md`

## Summary

Des-hardcodear los tres CLIs: las plantillas, patrones de cuota y quirks pasan a un
catálogo de datos versionado (`.specify/clis-catalog.json`); los 4 scripts leen CLIs
dinámicamente del inventario+catálogo; una skill nueva (`speckit-clis`) permite
registrar/editar/verificar/dar de baja cualquier CLI con validación de alta y
verificación por niveles (sin gastar cuota salvo permiso). Multiplataforma por runtime
único: scripts compatibles Windows PowerShell 5.1 + PowerShell 7, con `pwsh` como
prerequisito en Linux/macOS; las operaciones sensibles a plataforma (wrapper de
invocación, kill de árbol de procesos, null device, resolución de ejecutables) se
concentran en un helper de plataforma compartido. CI de GitHub Actions corre la suite
en los 3 sistemas operativos (SC-005), lo que exige migrar los tests a Pester 5.

## Technical Context

**Language/Version**: PowerShell compatible 5.1 y 7 (scripts) + Markdown (skills/playbooks) + JSON (catálogo e inventario)

**Primary Dependencies**: PowerShell 7 (`pwsh`) como prerequisito SOLO en Linux/macOS (Clarificación S1); Pester 5 (migración desde 3.4 — necesario para correr en los 3 OS); GitHub Actions (repo ya publicado) para la matriz de CI

**Storage**: `.specify/clis-catalog.json` (NUEVO, versionado — datos de CLIs conocidos); `.specify/models.json` v2 (claves de CLI dinámicas, campos nuevos opcionales, lectura compatible v1 — Clarificación S3)

**Testing**: Pester 5 (sintaxis `Should -Be`) en Windows/Linux/macOS vía CI matrix + escenarios quickstart con CLI stub

**Target Platform**: Windows 11 (5.1 o 7), Linux y macOS (pwsh 7)

**Project Type**: Extensión de tooling — 1 skill nueva, 1 catálogo de datos, 1 helper de plataforma, refactor de 4 scripts + 1 script nuevo de configuración, CI

**Performance Goals**: SC-001 registrar+verificar un CLI < 5 min; sin metas de runtime clásicas

**Constraints**: Aditividad (Constitución I) — el flujo existente no cambia para quien no registra CLIs; compatibilidad total con `models.json` v1 sin migración (FR-011); cero nombres de CLI en lógica (SC-003, verificable por grep); verificación jamás gasta cuota sin permiso explícito (SC-006)

**Scale/Scope**: 4 scripts refactorizados + 2 nuevos (`platform.ps1`, `clis-config.ps1`), 1 skill nueva, catálogo con 3 CLIs precargados, migración de 4 suites de tests a Pester 5 + suites nuevas, 1 workflow de CI

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento del diseño | Estado |
|---|---|---|
| I. Compatibilidad Aditiva | Solo se agregan catálogo, skill, helper y CI; los scripts se refactorizan conservando interfaz y comportamiento (mismos parámetros y salidas); `models.json` v1 se lee sin migración; skills base intactas | ✅ PASS |
| II. Portabilidad Multi-CLI | La generalización REFUERZA el principio: cualquier CLI puede ser secundario, y el catálogo/inventario sigue siendo la única fuente de invocación; `AGENTS.md` suma el puntero a `speckit-clis` | ✅ PASS |
| III. El Más Barato que Alcance | Sin cambio en el algoritmo de asignación; CLIs registrados entran al ranking con sus capacidad/costo declarados | ✅ PASS |
| IV. Nunca Discriminar | FR-004 explícito: los registrados participan en igualdad; el generador de `asignacion` ya es genérico (itera el diccionario de CLIs) | ✅ PASS |
| V. Decisiones Caras al Más Capaz | Sin cambio (triage/assign no se tocan) | ✅ PASS |
| VI. Mínima Intervención, Gates Reales | La verificación con gasto de cuota es opt-in explícito (SC-006); la baja pide confirmación; el registro valida en el alta para evitar fallos tardíos | ✅ PASS |

**Re-check post-Phase 1**: sin cambios — el diseño de datos mantiene los seis principios. ✅ PASS

## Project Structure

### Documentation (this feature)

```text
specs/003-generic-cli-support/
├── plan.md
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── clis-catalog-schema.md    # Esquema del catálogo + resolución catálogo→inventario
│   └── cli-config-operations.md  # Semántica de registrar/editar/verificar/baja
└── tasks.md             # Phase 2
```

### Source Code (repository root)

```text
.specify/
├── clis-catalog.json                  # NUEVO: datos precargados de claude/codex/kimi
│                                      #   (plantillas, patrones de cuota, hints de auth, quirks)
└── scripts/powershell/
    ├── platform.ps1                   # NUEVO: helpers de plataforma (Get-OsFamily,
    │                                  #   Invoke-PortableProcess, Stop-ProcessTree,
    │                                  #   Get-NullDevice, Resolve-Executable, Write-Utf8NoBom)
    ├── clis-config.ps1                # NUEVO: Add/Edit/Remove-CliDefinition con validación
    │                                  #   de alta + Invoke-CliVerification por niveles
    ├── scan-models.ps1                # REFACTOR: siembra/hints/plantillas desde el catálogo;
    │                                  #   iteración dinámica de CLIs (sin lista fija)
    ├── invoke-secondary.ps1           # REFACTOR: patrones de cuota desde inventario/catálogo;
    │                                  #   wrapper y kill-tree portables vía platform.ps1
    ├── update-quota.ps1               # REFACTOR menor: ya es genérico; usa platform.ps1
    └── get-parallel-groups.ps1        # REFACTOR menor: regex de [M:] acepta nombres de CLI
                                       #   genéricos ([a-z][a-z0-9-]*)

.claude/skills/
└── speckit-clis/
    └── SKILL.md                       # NUEVA: apartado de configuración de CLIs

.github/workflows/
└── tests.yml                          # NUEVO: matriz windows/ubuntu/macos con Pester 5

tests/powershell/                      # MIGRACIÓN a Pester 5 + suites nuevas
    ├── (4 suites existentes migradas)
    ├── platform.Tests.ps1             # NUEVO
    └── clis-config.Tests.ps1          # NUEVO

AGENTS.md                              # + puntero a speckit-clis
README.md                              # + prerequisitos por SO y sección de configuración de CLIs
```

**Structure Decision**: mismo patrón de las features 001/002 (skills Markdown + scripts
PowerShell testeables). Las diferencias de plataforma se AÍSLAN en `platform.ps1` para
que la lógica de negocio de los demás scripts quede idéntica en los 3 SO; el catálogo
de datos reemplaza a las tablas internas como única fuente de conocimiento de CLIs.

## Complexity Tracking

Sin violaciones de la constitución que justificar. Nota: la migración de tests a
Pester 5 es un cambio de herramienta de desarrollo (no de producto) exigido por la
matriz multi-OS; se documenta como prerequisito de desarrollo en el README.
