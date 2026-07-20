---
name: "speckit-models"
description: "Genera el inventario multi-CLI (.specify/models.json): detecta CLIs instalados (claude/codex/kimi), modelos, modo headless y autenticación; pide al usuario lo no detectable (plan, cuotas) y arma el ranking de asignación por complejidad. Usar cuando el usuario invoca /speckit-models o cuando un pipeline multi-CLI necesita el inventario y no existe."
argument-hint: "[--force] [--probe-auth] [--probe-models]"
compatibility: "Requiere estructura .specify/ de spec-kit y Python 3.11+"
metadata:
  author: "gen_speckit"
user-invocable: true
disable-model-invocation: false
---

## Objetivo

Producir/actualizar `.specify/models.json` — la fuente de verdad del sistema multi-CLI
— combinando detección automática con declaración del usuario. Las correcciones
manuales del usuario SIEMPRE prevalecen (FR-004).

## Pasos

1. **Ejecutar el escaneo**:

   ```bash
   python .specify/scripts/python/scan_models.py --json
   ```

   Flags que el usuario puede pasar: `--force` (pisar ediciones manuales, solo si lo
   pidió explícitamente), `--probe-auth` (verificar autenticación con una invocación
   real mínima — consume una llamada por CLI).

   El escaneo además **descubre los modelos reales** de cada CLI (feature 006): usa el
   mecanismo de listado del catálogo (`modelos_cmd`) y los archivos de configuración
   locales (`config_hints`), marcando cada modelo con `origen`
   (`detectado-local` | `semilla`) y sus `esfuerzos` cuando el CLI los expone. Flag
   `--probe-models`: habilita mecanismos que consumen una llamada (opt-in).

2. **Verificación oficial (best-effort, la hace el agente)**: por cada CLI del
   inventario con `fuentes_oficiales` en `.specify/clis-catalog.json`:
   - Consultar esas URLs (WebFetch/WebSearch) y extraer qué modelos publica el
     proveedor para ese CLI.
   - Cruzar con el inventario: un modelo publicado que NO esté detectado ni sembrado se
     **propone como alta** con `origen: "oficial-sin-confirmar"` y `capacidad`/`costo`
     sugeridos (marcarlos como propuesta corregible al presentar). Los ya detectados no
     cambian. NUNCA borrar modelos por ausencia oficial (el usuario decide).
   - Registrar en `clis.<cli>.verificacion_web`: `{"estado": "hecha", "fecha":
     "YYYY-MM-DD", "fuentes": [urls]}`. **Sin acceso web o fuente caída**: dejar
     `{"estado": "omitida"}` y seguir sin fallar.
   - Los modelos `oficial-sin-confirmar` **entran al ranking como cualquier otro**
     (decisión de diseño): si al despachar no están disponibles, el fallback del
     orquestador escala solo.

3. **Leer el resultado** (`.specify/models.json`) y detectar qué quedó `"desconocido"`:
   `plan`, `cuota`, `autenticado`, `contexto_k`.

4. **Preguntar al usuario SOLO lo no detectable**, en una sola tanda:
   - Plan contratado por CLI instalado (ej. "Claude Max 5x", "Kimi free").
   - Estado de cuota si lo conoce (`ok` / `agotada`).
   - Correcciones de capacidad/costo si no está de acuerdo con la siembra.

   Lo que el usuario no sepa queda `"desconocido"` — NUNCA inventar valores.

5. **Aplicar las respuestas** editando `.specify/models.json` (mantener UTF-8 sin BOM,
   indentación 2). No tocar campos que el usuario no mencionó.

6. **Validar contra el contrato** (`specs/001-multi-cli-orchestrator/contracts/models-schema.md`):
   - Toda referencia `cli/modelo` de `asignacion` existe en `clis.<cli>.modelos`.
   - Ningún CLI instalado y autenticado queda fuera de todas las listas (Constitución IV).
   - JSON parseable.

   Si algo falla, corregirlo antes de terminar.

7. **Mostrar resumen**: tabla CLI → instalado/versión/autenticado/plan/cuota, los modelos con su **origen** y **esfuerzos**, el estado de la verificación web, y el
   ranking `asignacion` por nivel. Recordar al usuario que puede corregir el archivo a
   mano y que sus ediciones sobreviven futuras re-ejecuciones.

## Reglas

- Este comando es el ÚNICO que regenera el inventario completo. El resto del sistema
  solo escribe los campos de cuota vía `update_quota.py`.
- Re-ejecución: el script compara contra `.specify/models.scan.json` y preserva las
  ediciones del usuario automáticamente; ante conflicto irresoluble, preguntar.
- Si un CLI está instalado pero no autenticado, avisar al usuario cómo autenticarlo
  (login interactivo del propio CLI) — no intentar autenticar por él.
