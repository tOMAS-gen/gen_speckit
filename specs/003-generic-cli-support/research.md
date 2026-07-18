# Research: Soporte Genérico de CLIs y Multiplataforma

**Feature**: 003-generic-cli-support | **Date**: 2026-07-18

Sin NEEDS CLARIFICATION pendientes. Decisiones:

## R1 — Compatibilidad PowerShell 5.1 + 7 en un solo código

**Decision**: los scripts declaran compatibilidad dual y evitan las divergencias
conocidas entre ediciones: (a) `Set-Content -Encoding Default` no existe igual en 7 →
usar SIEMPRE los helpers propios (`Write-Utf8NoBom`, y un `Write-AnsiWrapper` para los
wrappers de batch que en Unix no aplican); (b) `$IsWindows`/`$IsLinux`/`$IsMacOS` no
existen en 5.1 → `Get-OsFamily` en `platform.ps1` los emula (en 5.1 siempre Windows);
(c) `Start-Process`/redirecciones funcionan igual; (d) `taskkill` es solo Windows →
en .NET Core (pwsh 7) `Process.Kill($true)` mata el árbol nativamente; en 5.1 se
mantiene `taskkill /T`.

**Rationale**: la Clarificación S1 pidió runtime único; las diferencias reales son
pocas y todas encapsulables en `platform.ps1`.

**Alternatives considered**: exigir pwsh 7 también en Windows (rompería a los usuarios
actuales de 5.1 — contra FR-011/aditividad); duplicar en bash (rechazado en clarify).

## R2 — Wrapper de invocación portable

**Decision**: en Windows se conserva el wrapper `.cmd` actual (PATH heredado, `< NUL`,
`%ERRORLEVEL%`); en Linux/macOS el wrapper es un `.sh` equivalente (`#!/bin/sh`,
`export PATH=...`, `command < /dev/null`, `exit $?`) ejecutado con `/bin/sh`. La
elección la hace `Invoke-PortableProcess` en `platform.ps1`; la firma que ven
`invoke-secondary.ps1` y los tests no cambia.

**Rationale**: el wrapper-archivo demostró hoy su valor (evita quoting hell y queda
como evidencia auditable); replicar el patrón por SO mantiene el comportamiento
equivalente que exige FR-013.

**Alternatives considered**: invocar el CLI directo desde .NET sin shell (pierde la
herencia de PATH controlada y la evidencia del comando exacto).

## R3 — Esquema del catálogo y resolución de datos

**Decision**: `.specify/clis-catalog.json` con una entrada por CLI conocido:
`headless` (plantilla), `patrones_cuota[]`, `auth_hints[]` (rutas de credenciales por
SO), `version_cmd`, `modelos_semilla[]` y `quirks[]` (notas por versión). Resolución
en tiempo de ejecución: **inventario del usuario > catálogo > defaults genéricos**
(patrones de cuota genéricos: `rate limit|quota|429|usage limit`). El catálogo nunca
se escribe en runtime; el inventario conserva las garantías de FR-004 (ediciones del
usuario intocables).

**Rationale**: implementa la Clarificación S3; los quirks descubiertos hoy (codex
0.144, kimi-code 0.27) se distribuyen con `git pull` sin tocar código (SC-003).

**Alternatives considered**: catálogo remoto descargable (dependencia de red y
superficie de supply-chain innecesarias en v1).

## R4 — Migración de tests a Pester 5

**Decision**: migrar las 4 suites a sintaxis Pester 5 (`Should -Be`, bloques
`BeforeAll/BeforeDiscovery`) y declarar Pester 5 como prerequisito de desarrollo
(`Install-Module Pester -MinimumVersion 5.5`). Pester 5 corre en 5.1 y en pwsh 7 en
los tres SO; Pester 3.4 (el preinstalado de Windows) no es viable fuera de Windows.

**Rationale**: SC-005 exige la suite en 3 OS; los runners de GitHub Actions traen
pwsh + Pester 5. Mantener 3.4 partiría la suite en dos dialectos.

**Alternatives considered**: doble sintaxis condicional (inmantenible); no correr
tests fuera de Windows (incumple SC-005).

## R5 — CI multiplataforma

**Decision**: `.github/workflows/tests.yml` con matriz
`windows-latest / ubuntu-latest / macos-latest`, shell `pwsh`, pasos: instalar Pester 5
si falta → `Invoke-Pester tests/powershell -CI`. Los tests que tocan plataforma usan
CLIs stub (patrón ya existente con `.cmd`; se agrega el gemelo `.sh`).

**Rationale**: es la única verificación honesta de SC-005 disponible desde una máquina
Windows; el repo ya está publicado en GitHub.

**Alternatives considered**: validación manual documentada por SO (frágil y no
repetible); contenedores locales (no cubren macOS).

## R6 — Verificación de CLIs por niveles

**Decision**: `Invoke-CliVerification` con niveles acumulativos: (a) comando —
`Resolve-Executable` portable; (b) autenticación — `auth_hints` del catálogo/inventario
sin ejecutar nada; (c) invocación de prueba — SOLO con `-AprobarPrueba` explícito,
mostrando antes el comando exacto renderizado; resultado clasificado con la misma
lógica de `invoke-secondary.ps1` (exito/cuota/indisponible) + tiempo de respuesta.
El diagnóstico siempre dice qué falló y el paso concreto para corregirlo.

**Rationale**: FR-006/007 y SC-006 (cero gasto sin permiso); reutilizar la
clasificación existente evita dos verdades sobre qué es un fallo.

**Alternatives considered**: verificación siempre-con-prueba (gasta cuota sin
consentimiento — viola SC-006).

## R7 — Regex de etiquetas con CLIs genéricos

**Decision**: el grupo de CLI en la regex del contrato task-labels pasa de `[a-z]+` a
`[a-z][a-z0-9-]*` (nombres kebab-case: `gemini`, `qwen-code`, `mi-cli-interno`); el
validador de alta impone el mismo patrón al registrar (FR-003), de modo que etiqueta
e inventario nunca divergen.

**Rationale**: hoy `[M:qwen-code/x]` ni parsearía; el alta validada garantiza que todo
nombre registrado es etiquetable.

**Alternatives considered**: permitir cualquier string (rompería el parseo posicional
de etiquetas).
