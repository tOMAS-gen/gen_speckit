---
name: "speckit-models"
description: "Genera el inventario multi-CLI (.specify/models.json): detecta CLIs instalados (claude/codex/kimi), modelos, modo headless y autenticación; pide al usuario lo no detectable (plan, cuotas) y arma el ranking de asignación por complejidad. Usar cuando el usuario invoca /speckit-models o cuando un pipeline multi-CLI necesita el inventario y no existe."
argument-hint: "[-Force] [-ProbeAuth]"
compatibility: "Requiere estructura .specify/ de spec-kit y PowerShell"
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

   ```powershell
   .specify/scripts/powershell/scan-models.ps1 -Json
   ```

   Flags que el usuario puede pasar: `-Force` (pisar ediciones manuales, solo si lo
   pidió explícitamente), `-ProbeAuth` (verificar autenticación con una invocación
   real mínima — consume una llamada por CLI).

2. **Leer el resultado** (`.specify/models.json`) y detectar qué quedó `"desconocido"`:
   `plan`, `cuota`, `autenticado`, `contexto_k`.

3. **Preguntar al usuario SOLO lo no detectable**, en una sola tanda:
   - Plan contratado por CLI instalado (ej. "Claude Max 5x", "Kimi free").
   - Estado de cuota si lo conoce (`ok` / `agotada`).
   - Correcciones de capacidad/costo si no está de acuerdo con la siembra.

   Lo que el usuario no sepa queda `"desconocido"` — NUNCA inventar valores.

4. **Aplicar las respuestas** editando `.specify/models.json` (mantener UTF-8 sin BOM,
   indentación 2). No tocar campos que el usuario no mencionó.

5. **Validar contra el contrato** (`specs/001-multi-cli-orchestrator/contracts/models-schema.md`):
   - Toda referencia `cli/modelo` de `asignacion` existe en `clis.<cli>.modelos`.
   - Ningún CLI instalado y autenticado queda fuera de todas las listas (Constitución IV).
   - JSON parseable.

   Si algo falla, corregirlo antes de terminar.

6. **Mostrar resumen**: tabla CLI → instalado/versión/autenticado/plan/cuota, y el
   ranking `asignacion` por nivel. Recordar al usuario que puede corregir el archivo a
   mano y que sus ediciones sobreviven futuras re-ejecuciones.

## Reglas

- Este comando es el ÚNICO que regenera el inventario completo. El resto del sistema
  solo escribe los campos de cuota vía `update-quota.ps1`.
- Re-ejecución: el script compara contra `.specify/models.scan.json` y preserva las
  ediciones del usuario automáticamente; ante conflicto irresoluble, preguntar.
- Si un CLI está instalado pero no autenticado, avisar al usuario cómo autenticarlo
  (login interactivo del propio CLI) — no intentar autenticar por él.
