# Quickstart: validación del Soporte Genérico de CLIs y Multiplataforma

**Feature**: 003-generic-cli-support | **Date**: 2026-07-18

## Prerequisitos

- Windows: PowerShell 5.1 o 7. Linux/macOS: `pwsh` (PowerShell 7) instalado.
- Pester 5 (`Install-Module Pester -MinimumVersion 5.5 -Force`).
- Un "CLI stub" para pruebas sin cuota: script local que acepta un prompt y responde
  (los tests lo generan; para pruebas manuales sirve cualquier ejecutable propio).

## Escenario 1 — Registrar un CLI nuevo (US1, SC-001, SC-002)

```
/speckit-clis registrar
```

Declarar un CLI stub (nombre `stub-test`, plantilla con `{prompt}`, 1 modelo baratito).

**Esperado**: validación de alta en el momento; entrada en `models.json` con
`origen: "registrado"`; aparece en `asignacion.baja`; una asignación posterior sobre
un tasks.md de juguete le da tareas. Cronometrar: registro + verificación < 5 min.

**Rechazos**: intentar registrar (a) nombre duplicado, (b) plantilla sin `{prompt}`,
(c) modelo con capacidad 15 → los tres rechazados con mensaje específico, sin
persistir nada.

## Escenario 2 — Verificar un CLI (US2, SC-006)

```
/speckit-clis verificar stub-test        → niveles a+b sin gasto
/speckit-clis verificar claude           → ídem; con aprobación explícita, nivel c
```

**Esperado**: sin aprobación, cero invocaciones (SC-006); con aprobación, muestra el
comando exacto antes de ejecutar y clasifica el resultado con latencia; el diagnóstico
de un CLI no instalado dice exactamente qué falta; `instalado/autenticado/version` se
actualizan sin tocar campos del usuario.

## Escenario 3 — Cero hardcodeo (US3, SC-003, SC-004)

```powershell
# SC-003: la única fuente de nombres es el catálogo (datos)
Select-String -Path .specify\scripts\powershell\*.ps1 -Pattern "claude|codex|kimi" |
  Where-Object { $_ -notmatch 'catalog' }   # esperado: 0 resultados en lógica
```

**Compatibilidad v1 (SC-004)**: tomar un `models.json` generado por la versión
anterior (tres claves, sin campos nuevos), correr escaneo/asignación/orquestación →
todo funciona; ediciones manuales intactas.

## Escenario 4 — Multiplataforma (US4, SC-005)

- **CI**: push → el workflow `tests.yml` corre la suite completa en
  windows/ubuntu/macos-latest; los 3 jobs en verde = SC-005 ✓.
- **Manual (Linux/contenedor)**: `pwsh -c "Invoke-Pester tests/powershell"` +
  escenario 1 con un stub `.sh`; despacho con timeout corto → el árbol de procesos
  muere limpio (verificar que no quedan huérfanos con `ps`).

## Escenario 5 — Ciclo completo con un cuarto CLI (integración)

Registrar el stub, correr `/speckit-models` (el ranking lo incluye), etiquetar a mano
una tarea `[M:stub-test/<modelo>]` en un tasks.md de juguete y orquestar: la tarea se
despacha al stub, se clasifica y se verifica — sin que ningún script haya sido
editado.

## Resultados de validación

**2026-07-18 — Escenario 1 (registrar un CLI, US1) — ejecutado real en Windows durante la verificación de T005**:

- Alta INVÁLIDA (nombre con mayúsculas/guión bajo + plantilla sin `{prompt}` +
  capacidad 15): rechazada con los TRES problemas listados (V1, V3, V5), sin
  persistir nada ✓.
- Alta VÁLIDA de `stub-test` (stub `.cmd` ejecutable real en PATH): persistida con
  `origen: "registrado"`, detección `instalado: true` sin gastar cuota, y
  `stub-test/mini` entró a `asignacion.baja` en posición 0 (capacidad 3, costo 1 —
  el más barato primero) ✓ (SC-001/SC-002).
- Baja sin `-Confirmado`: rechazada pidiendo confirmación ✓. Baja confirmada de un
  CLI de catálogo (kimi): `deshabilitado: true` sin borrar la entrada, 0 referencias
  restantes en `asignacion` ✓.
- Hallazgos de la verificación (corregidos): quirk nuevo de PS 5.1 (`@($param)` de
  parámetro tipado sin bindear rompe `.Count` bajo StrictMode) y semántica del merge
  de `asignacion` en operaciones explícitas. Ambos documentados en el reporte.

**2026-07-18 — Escenario 3 parcial (compatibilidad v1 + deshabilitado)**: suite
58/58 en verde incluye el fixture `models-v1.json` (lectura compatible con ediciones
manuales preservadas) y el test de `deshabilitado` excluido del ranking.

**2026-07-18 — Escenario 2 (verificar un CLI, US2)**:

- `codex` verificado **sin** `-AprobarPrueba`: niveles a y b `ok`, nivel c
  `omitido` con detalle "prueba real no solicitada" → cero invocaciones del CLI
  (SC-006) ✓.
- `claude` verificado **con** `-AprobarPrueba`: nivel c `ok`, clasificación
  `exito`, `exit: 0`, latencia **3.578 s**; el detalle incluye el comando
  renderizado completo: `claude -p "responde solo: ok"
  --dangerously-skip-permissions --output-format json --model fable` ✓.
- Campos detectables (`instalado`, `autenticado`, `version`) actualizados en
  ambos CLIs; campos del usuario (`headless`, `modelos`, `plan`, `cuota`)
  quedaron intactos ✓.

**2026-07-18 — Escenario 3 completo (cero hardcodeo, SC-003)**: grep de
claude/codex/kimi sobre la lógica de los 6 scripts de `.specify/scripts/powershell/`:
0 ocurrencias (la única mención era prosa de un comentario y se eliminó); skills base
de spec-kit: 0 modificadas desde la instalación.

**2026-07-18 — Escenario 5 completo (ciclo con un 4to CLI, ejecutado real en sandbox)**:
`cuarto-cli` (stub `.cmd`) registrado vía `Add-CliDefinition` → el re-scan lo detectó
dinámicamente junto a los 3 del catálogo y lo mantuvo en `asignacion.baja` → etiqueta
`[M:cuarto-cli/basico]` (nombre kebab) parseada por `get-parallel-groups` → despacho
real con `invoke-secondary` clasificado `exito` en el intento 1, con la salida del
stub capturada en logs. **Cero ediciones de código para soportar el CLI nuevo.**

## Tests

```powershell
Invoke-Pester tests/powershell/    # Pester 5, en cualquiera de los 3 SO
```

Cobertura nueva mínima: validaciones de alta V1–V6 (cli-config-operations.md),
resolución inventario>catálogo>genérico, regex de etiquetas con nombres kebab-case,
`platform.ps1` (null device, resolución de ejecutables, kill tree con stub), lectura
compatible de un models.json v1 fijo de fixture.
