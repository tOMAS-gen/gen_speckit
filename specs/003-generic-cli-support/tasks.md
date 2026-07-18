---

description: "Task list for feature implementation"
---

# Tasks: Soporte Genérico de CLIs y Multiplataforma

**Input**: Design documents from `/specs/003-generic-cli-support/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Pester 5 (migración incluida como tarea foundational); validación E2E por escenarios de quickstart.md con CLI stub.

**Organization**: por historia de usuario; el orden real de ejecución respeta las dependencias técnicas (ver Dependencies).

## Format: `[ID] [P?] [Story] Description`

Etiquetas multi-CLI `[C:...]` `[M:...]` agregadas por el asignador; editables a mano.

## Phase 1: Setup

- [x] T001 [C:media] [M:kimi/kimi-for-coding] Crear `.specify/clis-catalog.json` según `contracts/clis-catalog-schema.md`: los 3 CLIs precargados con TODO el conocimiento actual — plantillas headless vigentes, `version_cmd`, `auth_hints` por SO (rutas actuales de Windows + equivalentes `~/.claude`, `~/.codex`, `~/.kimi-code` para linux/macos), `patrones_cuota` por CLI, `modelos_semilla` (los de la siembra actual de scan-models.ps1) y `quirks` (codex 0.144: sin --ask-for-approval, stdin, sandbox read-only sin git, binario nativo npm; kimi-code 0.27: -p sin --yolo, alias kimi-code/) + `patrones_cuota_genericos`

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T002 [C:alta] [M:claude/fable] Crear `.specify/scripts/powershell/platform.ps1`: `Get-OsFamily` (emulación en 5.1), `Resolve-Executable` (candidatos por SO + hints del catálogo), `Invoke-PortableProcess` (wrapper `.cmd` en Windows / `.sh` en Unix, PATH heredado, stdin cerrado con null device, timeout, captura a archivos, handle antes de esperar), `Stop-ProcessTree` (`taskkill /T` en 5.1 / `Kill($true)` en 7+), `Get-NullDevice`, `Write-Utf8NoBom` y expansión portable de rutas con `~`/variables (research R1–R2)
- [x] T003 [US4] [C:media] [M:kimi/kimi-for-coding] Escribir `tests/powershell/platform.Tests.ps1` en Pester 5 (OsFamily, null device, resolución de ejecutables con stub, kill tree con proceso stub, expansión de rutas)
- [x] T004 [C:media] [M:kimi/kimi-for-coding] Migrar las 4 suites existentes de `tests/powershell/` a sintaxis Pester 5 (`Should -Be`, `BeforeAll`; sin cambios de cobertura) y verificar suite completa en verde local (research R4)

**Checkpoint**: base portable + tests modernizados

---

## Phase 3: User Story 1 - Registrar cualquier CLI (Priority: P1) 🎯 MVP

**Independent Test**: quickstart escenario 1 (alta válida de un stub + 3 rechazos con mensaje específico + participación en asignación)

- [x] T005 [US1] [C:alta] [M:codex/gpt-5.6-sol] Crear `.specify/scripts/powershell/clis-config.ps1`: `Add-CliDefinition` con validaciones V1–V6 de `contracts/cli-config-operations.md` (rechazo completo con lista de problemas), `Edit-CliDefinition` (validación sobre el resultado final), `Remove-CliDefinition` (advertencia de etiquetas `[M:]` activas en `specs/*/tasks.md`, `deshabilitado: true` para CLIs de catálogo), regeneración de `asignacion` preservando ediciones manuales, escritura UTF-8 sin BOM reutilizando helpers; cero nombres de CLI concretos en el código (SC-003)
- [x] T006 [US1] [C:media] [M:kimi/kimi-for-coding] Escribir `tests/powershell/clis-config.Tests.ps1` en Pester 5: V1–V6 uno por uno, duplicado, baja con deshabilitado y re-scan que lo respeta, preservación de ediciones manuales, nombre kebab-case compatible con la regex de etiquetas
- [x] T007 [P] [US1] [C:media] [M:kimi/kimi-for-coding-highspeed] Crear skill `.claude/skills/speckit-clis/SKILL.md` (registrar/editar/dar de baja conversacional sobre `clis-config.ps1`, con confirmaciones donde el contrato las exige) y agregar el puntero en `AGENTS.md`
- [x] T008 [US1] [C:media] [M:kimi/kimi-for-coding] Validar el escenario 1 de `specs/003-generic-cli-support/quickstart.md` con un CLI stub real y documentar resultados en la sección "Resultados de validación"

**Checkpoint**: cualquier CLI se registra sin tocar código

---

## Phase 4: User Story 2 - Verificar que un CLI funciona (Priority: P1)

**Independent Test**: quickstart escenario 2 (niveles sin gasto / con aprobación explícita, diagnóstico accionable)

- [x] T009 [US2] [C:media] [M:kimi/kimi-for-coding] Agregar a `.specify/scripts/powershell/clis-config.ps1` la función `Invoke-CliVerification` (niveles a/b/c acumulativos, comando renderizado mostrado antes del nivel c, aprobación explícita obligatoria, diagnóstico `{nivel, resultado, detalle, correccion}`, clasificación reutilizada de invoke-secondary, actualización solo de campos detectables) + tests correspondientes en `tests/powershell/clis-config.Tests.ps1`
- [x] T010 [US2] [C:media] [M:kimi/kimi-for-coding-highspeed] Integrar la verificación a `.claude/skills/speckit-clis/SKILL.md` (subcomando verificar) y validar el escenario 2 del quickstart (stub + claude real con aprobación), documentando resultados

**Checkpoint**: configuración confiable de punta a punta

---

## Phase 5: User Story 3 - Ningún CLI fijo en el código (Priority: P2)

**Independent Test**: quickstart escenario 3 (grep cero hardcodeo + models.json v1 funciona intacto)

- [x] T011 [US3] [C:alta] [M:claude/fable] Refactorizar `.specify/scripts/powershell/scan-models.ps1`: eliminar `$script:CliNames`, `Get-DefaultHeadless`, `Get-SeedModels` y hints internos → todo desde `.specify/clis-catalog.json` (resolución inventario > catálogo > genéricos); iterar dinámicamente catálogo + CLIs registrados del inventario; respetar `deshabilitado`; catálogo ausente/corrupto → aviso + continuar con inventario y defaults (contracts/clis-catalog inv. 4); mantener intactas las garantías de merge/ediciones
- [x] T012 [US3] [C:alta] [M:claude/fable] Refactorizar `.specify/scripts/powershell/invoke-secondary.ps1`: `$script:QuotaPatterns` y el caso especial de codex → datos del inventario/catálogo (`exe_hints`/`auth_hints`); wrapper y kill de árbol vía `platform.ps1` (`Invoke-PortableProcess`); comportamiento y firma idénticos en Windows
- [x] T013 [US3] [C:media] [M:kimi/kimi-for-coding] Refactor menor: regex de `get-parallel-groups.ps1` y de `contracts/task-labels.md` (feature 001) a nombres kebab-case `[a-z][a-z0-9-]*` (research R7); `update-quota.ps1` usa helpers de `platform.ps1`; grep de verificación SC-003 en los 4 scripts
- [x] T014 [US3] [C:media] [M:kimi/kimi-for-coding-highspeed] Actualizar los tests migrados para la resolución catálogo>inventario>genéricos y la regex kebab; agregar fixture `tests/fixtures/models-v1.json` (formato viejo con ediciones manuales) y test de lectura compatible; validar el escenario 3 del quickstart y documentar

**Checkpoint**: el sistema es genérico de verdad

---

## Phase 6: User Story 4 - Compatibilidad Linux y macOS (Priority: P2)

**Independent Test**: quickstart escenario 4 (CI 3 OS en verde)

- [x] T015 [P] [US4] [C:baja] [M:claude/haiku] Crear `.github/workflows/tests.yml`: matriz windows-latest/ubuntu-latest/macos-latest, shell pwsh, instalar Pester 5 si falta, `Invoke-Pester tests/powershell -CI`
- [x] T016 [US4] [C:media] [M:kimi/kimi-for-coding-highspeed] Agregar stubs `.sh` gemelos de los stubs `.cmd` en los tests que invocan procesos, seleccionados por `Get-OsFamily`, y revisar los tests sensibles a plataforma (rutas con separador, encoding, null device)
- [ ] T017 [US4] [C:media] [M:claude/fable] Push de la rama y verificación de los 3 jobs de CI en verde (iterando sobre fallos reales de linux/macos si aparecen); documentar el resultado en el escenario 4 del quickstart (SC-005)
- [x] T018 [P] [US4] [C:baja] [M:codex/gpt-5.6-luna] Actualizar `README.md`: sección de prerequisitos por SO (pwsh en Linux/macOS, Pester 5 para desarrollo) y documentación del apartado de configuración de CLIs (comandos de speckit-clis)

**Checkpoint**: multiplataforma verificado por CI

---

## Phase 7: Polish & Cross-Cutting

- [x] T019 [C:media] [M:kimi/kimi-for-coding] Validar el escenario 5 del quickstart (ciclo completo con un cuarto CLI stub: registrar → escanear → etiquetar → orquestar) y documentar resultados
- [x] T020 [C:baja] [M:claude/haiku] Auditoría de compatibilidad aditiva (skills base intactas, models.json v1 del usuario funciona) y actualización de la sección Estado del README (vía skill speckit-readme)

---

## Dependencies & Execution Order

- **Orden técnico real**: T001 ∥ T002 → T003/T004 → US3 (T011–T014, necesita catálogo+platform) y US1 (T005–T008, necesita platform para verificación) pueden intercalarse; US2 (T009–T010) tras T005; US4 (T015–T018) al final (la CI corre la suite ya migrada y refactorizada); Polish al cierre.
- T005/T009 tocan `clis-config.ps1` (secuenciales entre sí); T006/T009 tocan `clis-config.Tests.ps1` (secuenciales entre sí); T007/T010 tocan la skill (secuenciales entre sí).
- T011/T012 (fable) y T013 tocan scripts distintos → paralelizables entre sí tras T001+T002.
- T017 requiere TODO lo anterior en verde local (es el push que dispara la CI).

## Parallel Opportunities

- T001 ∥ T002 (archivos distintos); T007 ∥ T006; T011 ∥ T012 ∥ T013; T015 ∥ T018 ∥ T016.

## Implementation Strategy

**MVP**: T001+T002+T004+T005+T006+T007+T008 (US1: registrar CLIs ya funciona en Windows).
Luego US2 → US3 → US4 (CI al final valida todo) → Polish.

## Asignación multi-CLI

Asignadas por `claude/fable` (playbook assign.md) el 2026-07-18. Reparto: kimi 8
(6 kimi-for-coding + los media de highspeed 4 — ver tabla), claude 5 (2 alta fable +
2 baja haiku + 1 media fable por rol de integración), codex 2 (1 alta sol + 1 baja
luna). Justificación de empates por costo y del reparto en `orchestration-report.md`.
Editables a mano; re-generar `tasks.md` exige re-asignar.
