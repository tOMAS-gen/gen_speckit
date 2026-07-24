# Data Model: Despacho multi-modelo de todas las fases

**Feature**: `008-multi-model-phase-dispatch` | **Date**: 2026-07-22

## 1. Inventario — `.specify/models.json` (campos aditivos)

### 1.1 `deshabilitado` por modelo (NUEVO alcance)

```jsonc
{
  "clis": {
    "opencode": {
      "instalado": true,
      "deshabilitado": false,          // nivel CLI — YA EXISTE (feature 003)
      "headless": "opencode run \"{prompt}\" --model {modelo} ...",
      "modelos": [
        { "id": "gpt-5.6-sol", "capacidad": 9, "costo": 3, "contexto_k": 272 },
        { "id": "big-pickle", "capacidad": 7, "costo": 1, "contexto_k": 200,
          "deshabilitado": true }      // nivel MODELO — NUEVO, opcional, default false
      ]
    }
  }
}
```

- Tipo: booleano opcional; ausente ⇒ habilitado.
- Semántica: un modelo deshabilitado no aparece en `asignacion`, `asignacion_por_fase`
  ni en la resolución de candidatos de fase/tarea; no recibe despachos ni fallbacks.
- Preservación: `merge_node` ya mergea `modelos[]` por `id` y por campo ⇒ el flag
  puesto a mano sobrevive a re-scans (sin cambios en el merge).
- Un CLI con `deshabilitado: true` a nivel CLI excluye TODOS sus modelos
  (comportamiento existente, sin cambio).

### 1.2 `preferido` a nivel raíz (NUEVO)

```jsonc
{
  "clis": { ... },
  "preferido": "opencode",   // opcional; ausente ⇒ sin restricción
  "asignacion": { ... }
}
```

- Tipo: string opcional, debe ser clave existente en `clis` (validación al escribirlo).
- Semántica: si está presente, fases y tareas se reparten SOLO entre los modelos
  habilitados de ese agente. Es decisión del usuario: el reporte lo registra como tal
  (FR-008b). Los rankings globales (`asignacion*`) NO se recalculan filtrados — el
  filtro se aplica en la resolución de candidatos (así quitar la preferencia no exige
  re-scan).
- Si el agente preferido queda sin candidatos con cuota: fases → principal en sesión;
  tareas → `pendiente_bloqueada` con causa "configuración del usuario" (edge case del
  spec).

## 2. Asignación de fase — reporte `orchestration-report.md`

Tabla "Modelos por fase" (sección PARSEABLE) — columna nueva aditiva `Efectivo`:

```markdown
| Fase | Modelo asignado | Efectivo | Estado |
|------|-----------------|----------|--------|
| specify | kimi/kimi-for-coding | kimi/kimi-for-coding | ejecutada |
| plan | claude/fable | codex/gpt-5.6-sol | ejecutada |
| implement | (por tarea, ver Asignaciones) | — | pendiente |
```

- `Modelo asignado`: lo que decidió el triage (o editó el usuario — prevalece).
- `Efectivo`: quién la ejecutó realmente (difiere del asignado solo por fallback);
  `—` mientras `pendiente`. El principal es el único que escribe esta tabla.
- `Estado`: `pendiente | ejecutada | omitida` (sin cambios).
- Compatibilidad: los parsers deben tolerar tablas de 3 columnas (reportes viejos) y
  4 columnas (nuevos).

## 3. Despacho de fase — archivos de trabajo `specs/<feature>/.phase-dispatch/`

| Archivo | Productor | Contenido |
|---|---|---|
| `<fase>.prompt.md` | principal | Instrucciones completas de la fase para el secundario (ver contrato phase-dispatch.md) |
| `<fase>.questions.md` | secundario (despacho A) | Preguntas/hallazgos para el usuario (solo clarify/analyze) |
| `<fase>.answers.md` | principal | Respuestas del usuario, entrada del despacho B (solo clarify/analyze) |

- Los logs del despacho siguen en `orchestration-logs/` con base-name `fase-<fase>`
  (mismo contrato de logs existente: `.intentoN.out.log` / `.err.log`).
- El artefacto FINAL de cada fase es el oficial de spec-kit (spec.md, plan.md, ...) —
  los archivos de `.phase-dispatch/` son intermedios y auditables.

## 4. Resolución de candidatos de fase — `phase_candidates.py` (contrato interno)

Entrada: inventario + nombre de fase + nivel requerido (`alta` para fases de
criterio, según FR-005a) + identidad del principal.

```text
resolve_phase_candidates(inventory, fase, nivel_minimo, principal) -> [
  "cli/modelo",   # ordenados: asignacion_por_fase[fase] si existe, si no asignacion[nivel]
  ...
]
```

Reglas de filtrado (en orden):
1. Partir de `asignacion_por_fase[fase]` si existe y no está vacía; si no,
   `asignacion[nivel_minimo]`.
2. Excluir modelos de CLIs `deshabilitado` (nivel CLI) y modelos con
   `deshabilitado: true` (nivel modelo).
3. Si `preferido` presente: conservar solo candidatos de ese agente.
4. Excluir candidatos con `cuota == "agotada"` no vencida (`cuota_reset` pasado ⇒
   vuelve a ser elegible — regla existente de assign.md).
5. El principal es candidato válido pero se ejecuta en sesión, nunca por headless.

Salida vacía ⇒ la fase la ejecuta el principal en sesión (nunca bloquea).

## 5. Invocación con prompt por archivo — `invoke_secondary.py`

```text
--prompt "<texto>"        # existente, mutuamente excluyente con --prompt-file
--prompt-file <ruta>      # NUEVO: ruta a archivo UTF-8 dentro del repo
```

- Con `--prompt-file`, el prompt inline generado es un puntero corto (< 500 chars):
  identificación del despacho + instrucción de leer la ruta indicada + restricciones
  mínimas. El contenido del archivo NUNCA se sustituye en la línea de comandos.
- Validaciones: archivo existe, es legible, está dentro del repo. Error claro si
  ambos flags o ninguno.
- El JSON de salida agrega `promptFile` (ruta o null) — aditivo.

## 6. Estados y transiciones de una fase despachada

```text
pendiente ──despacho──> en_verificacion ──pasa──> ejecutada
   │                        │
   │                        └─falla─> reintento (mismo modelo, 1x)
   │                                     └─falla─> escalada (siguiente candidato ↑capacidad, 1x)
   │                                                  └─falla─> principal en sesión ──> ejecutada
   └─cuota_agotada──> reasignación (siguiente candidato) ──> despacho
                          └─sin candidatos─> principal en sesión ──> ejecutada
```

- `en_verificacion` es transitorio (no se persiste en la tabla; la tabla solo guarda
  `pendiente|ejecutada|omitida`).
- Toda reasignación/escalada/caída al principal se registra en Eventos con causa.
```
