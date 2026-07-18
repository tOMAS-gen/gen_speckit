# Data Model: Soporte Genérico de CLIs y Multiplataforma

**Feature**: 003-generic-cli-support | **Date**: 2026-07-18

## 1. Catálogo de CLIs conocidos — `.specify/clis-catalog.json` (NUEVO, versionado)

Solo lectura en runtime; se actualiza vía repo (git pull) o edición del usuario.

| Campo (por CLI) | Tipo | Rol |
|---|---|---|
| `headless` | string | Plantilla por defecto con `{prompt}` y `{modelo}` |
| `version_cmd` | string | Comando para detectar versión (p. ej. `--version`) |
| `auth_hints` | objeto por SO | Rutas de credenciales detectables: `windows[]`, `linux[]`, `macos[]` |
| `patrones_cuota` | array de regex | Detección de límite de uso propia del CLI |
| `modelos_semilla` | array | `{id, capacidad, costo, contexto_k}` iniciales |
| `quirks` | array de strings | Notas por versión (documentación operativa) |

**Precarga v1**: `claude`, `codex`, `kimi` con todo el conocimiento acumulado (quirks
de codex 0.144 y kimi-code 0.27 incluidos).

## 2. Inventario — `.specify/models.json` v2 (compatible v1)

Cambios respecto de v1 — todos OPCIONALES (lectura compatible, FR-011):

| Campo nuevo (por CLI) | Tipo | Default si falta |
|---|---|---|
| `origen` | `catalogo` \| `registrado` | `catalogo` si el nombre existe en el catálogo; si no, `registrado` |
| `patrones_cuota` | array de regex | Los del catálogo; si tampoco → genéricos (`rate limit`, `quota`, `429`, `usage limit`) |
| `version_cmd` | string | Del catálogo; si no → `--version` |

- Claves de `clis` **dinámicas**: cualquier nombre que cumpla `[a-z][a-z0-9-]*`
  (el esquema v1 restringía a los tres nombres — se levanta la restricción).
- Resolución de cualquier dato de CLI: **inventario > catálogo > default genérico**.
- Garantías intactas: única escritura automática = campos de cuota; ediciones del
  usuario prevalecen (mecanismo `models.scan.json` sin cambios).

## 3. Definición de CLI registrada (alta vía `speckit-clis`)

Validación de alta (FR-003) — se rechaza el registro si falla cualquiera:

1. `nombre` único y con patrón `[a-z][a-z0-9-]*` (etiquetable en `[M:]` — research R7)
2. `headless` contiene `{prompt}` (y `{modelo}` si declara >1 modelo)
3. Al menos 1 modelo con `id` único, `capacidad` 1–10, `costo` 1–3
4. `patrones_cuota` opcional (default genérico) pero si se declara, cada regex compila

**Estados** de un CLI del inventario: `instalado`/`autenticado` (detectados),
`cuota` (runtime), `origen` (catalogo/registrado). La baja elimina la entrada del
inventario tras confirmación + advertencia de etiquetas `[M:]` activas; los del
catálogo pueden volver a entrar en el próximo escaneo (para excluirlos
permanentemente: campo `deshabilitado: true`, respetado por el escaneo).

## 4. Verificación de CLI (resultado transitorio, reflejado en inventario)

| Nivel | Qué comprueba | Gasta cuota |
|---|---|---|
| a. comando | ejecutable resoluble en el SO actual | No |
| b. autenticación | `auth_hints` del SO actual | No |
| c. invocación de prueba | comando renderizado mostrado + aprobación explícita → invoca y clasifica (exito/cuota_agotada/indisponible) + latencia | **Sí (opt-in)** |

Actualiza SOLO `instalado`, `autenticado`, `version` (FR-008).

## 5. Helper de plataforma (`platform.ps1`) — superficie

`Get-OsFamily` (windows/linux/macos; emulado en 5.1) · `Resolve-Executable`
(Get-Command + candidatos .exe/.cmd/nativo por SO) · `Invoke-PortableProcess`
(wrapper .cmd en Windows / .sh en Unix, PATH heredado, stdin cerrado, timeout,
captura a archivos) · `Stop-ProcessTree` (taskkill /T en 5.1 / `Kill($true)` en 7) ·
`Get-NullDevice` (`NUL` / `/dev/null`) · `Write-Utf8NoBom`.

Todos los scripts consumen SOLO estas primitivas para lo sensible a plataforma
(FR-014); ningún otro archivo menciona `cmd.exe`, `taskkill` ni `NUL`.
