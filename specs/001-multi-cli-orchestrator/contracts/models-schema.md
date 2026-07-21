# Contract: esquema de `.specify/models.json`

**Feature**: 001-multi-cli-orchestrator

Contrato de datos entre `/speckit-models` (productor), el usuario (editor con
prioridad) y triage/asignador/orquestador (consumidores). `update-quota.ps1` es el
único escritor automático permitido y solo sobre `cuota`, `cuota_desde`, `cuota_reset`.

## JSON Schema (draft-07)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SpecKit Multi-CLI Models Inventory",
  "type": "object",
  "required": ["clis", "asignacion"],
  "properties": {
    "clis": {
      "type": "object",
      "minProperties": 1,
      "propertyNames": { "enum": ["claude", "codex", "kimi"] },
      "additionalProperties": {
        "type": "object",
        "required": ["instalado"],
        "properties": {
          "instalado":   { "type": "boolean" },
          "autenticado": { "type": ["boolean", "string"] },
          "version":     { "type": "string" },
          "headless":    { "type": "string", "description": "Plantilla con {prompt} y opcional {modelo}" },
          "plan":        { "type": "string" },
          "cuota":       { "enum": ["ok", "agotada", "desconocido"] },
          "cuota_desde": { "type": "string", "format": "date-time" },
          "cuota_reset": { "type": ["string"], "description": "date-time ISO o 'desconocido'" },
          "modelos": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["id", "capacidad", "costo"],
              "properties": {
                "id":         { "type": "string", "minLength": 1 },
                "capacidad":  { "type": "integer", "minimum": 1, "maximum": 10 },
                "costo":      { "type": "integer", "minimum": 1, "maximum": 3 },
                "contexto_k": { "type": ["integer", "string"] },
                "nivel_origen": { "enum": ["medido", "estimado", "manual"] },
                "clasificacion": {
                  "type": "object",
                  "properties": {
                    "entrada":     { "type": "string" },
                    "rating":      { "type": "number" },
                    "publicado":   { "type": "string" },
                    "fuente_dato": { "enum": ["global", "local"] }
                  }
                },
                "fortalezas": {
                  "type": "object",
                  "additionalProperties": { "type": "integer", "minimum": 1, "maximum": 10 }
                }
              }
            }
          }
        }
      }
    },
    "asignacion_por_fase": {
      "type": "object",
      "additionalProperties": { "$ref": "#/definitions/listaCandidatos" }
    },
    "asignacion": {
      "type": "object",
      "required": ["alta", "media", "baja"],
      "properties": {
        "alta":  { "$ref": "#/definitions/listaCandidatos" },
        "media": { "$ref": "#/definitions/listaCandidatos" },
        "baja":  { "$ref": "#/definitions/listaCandidatos" }
      }
    }
  },
  "definitions": {
    "listaCandidatos": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string", "pattern": "^(claude|codex|kimi)/[A-Za-z0-9._-]+$" }
    }
  }
}
```

## Invariantes semánticos (no expresables en JSON Schema)

1. **Referencias válidas**: todo `cli/modelo` de `asignacion.*` existe en
   `clis.<cli>.modelos[].id` y ese CLI tiene `instalado: true`.
2. **No discriminación** (Constitución IV): todo CLI instalado y autenticado aparece
   en al menos una lista de `asignacion`.
3. **Orden significativo**: dentro de cada lista, el índice 0 es el candidato
   preferido; el fallback recorre en orden. Agotadas las listas del nivel, se escala
   al nivel superior (baja → media → alta).
4. **Prioridad del usuario** (FR-004): re-generar el inventario no pisa ediciones
   manuales sin confirmación; la detección solo actualiza campos que el usuario no
   tocó (se detecta por comparación con la propuesta previa del scan, guardada como
   `.specify/models.scan.json`).
5. **Selección "más capaz disponible"** (FR-006/FR-013): primer candidato de
   `asignacion.alta` con `cuota != "agotada"`; empate → orden de lista.
6. **Codificación**: el archivo se escribe siempre en UTF-8 sin BOM, con indentación
   de 2 espacios — cualquier CLI o script que lo edite debe preservar ese formato
   (tres editores distintos no deben generar diffs de codificación).
7. **Reset desconocido**: si el plan del CLI es `"desconocido"`, al agotarse la cuota
   se escribe `cuota_reset: "desconocido"` y el estado `agotada` persiste hasta reset
   manual del usuario (FR-018).
8. **Aditividad de feature 007**: los campos `nivel_origen`, `clasificacion`,
   `fortalezas` y la sección `asignacion_por_fase` son opcionales y aditivos. Un
   `models.json` sin ninguno de ellos sigue siendo válido y ningún consumidor
   existente puede requerirlos. Ver el contrato completo en
   `specs/007-arena-model-ranking/contracts/classification.md` (obtención de datos,
   almacén de la máquina y reglas de precedencia).

## Ejemplo completo válido

```json
{
  "clis": {
    "claude": {
      "instalado": true, "autenticado": true, "version": "2.1.0",
      "headless": "claude -p \"{prompt}\" --dangerously-skip-permissions --output-format json",
      "plan": "Max 5x", "cuota": "ok",
      "modelos": [
        {
          "id": "opus", "capacidad": 9, "costo": 3, "contexto_k": 200,
          "nivel_origen": "medido",
          "clasificacion": {
            "entrada": "claude-opus-4-8",
            "rating": 1507.48,
            "publicado": "2026-07-16",
            "fuente_dato": "global"
          }
        },
        { "id": "sonnet", "capacidad": 7, "costo": 2, "contexto_k": 200 }
      ]
    },
    "codex": {
      "instalado": true, "autenticado": true, "version": "0.48.0",
      "headless": "codex exec \"{prompt}\" --sandbox workspace-write --ask-for-approval never --skip-git-repo-check --json",
      "plan": "Plus", "cuota": "ok",
      "modelos": [
        { "id": "gpt-5-codex", "capacidad": 8, "costo": 2, "contexto_k": 272 },
        { "id": "gpt-5-mini",  "capacidad": 5, "costo": 1, "contexto_k": 272 }
      ]
    },
    "kimi": {
      "instalado": true, "autenticado": true, "version": "1.4.2",
      "headless": "kimi --print --yolo --final-message-only --command \"{prompt}\"",
      "plan": "free", "cuota": "agotada",
      "cuota_desde": "2026-07-18T09:30:00-03:00",
      "cuota_reset": "2026-07-19T09:30:00-03:00",
      "modelos": [
        { "id": "k2", "capacidad": 6, "costo": 1, "contexto_k": 256 }
      ]
    }
  },
  "asignacion": {
    "alta":  ["claude/opus", "codex/gpt-5-codex"],
    "media": ["codex/gpt-5-codex", "claude/sonnet", "kimi/k2"],
    "baja":  ["kimi/k2", "codex/gpt-5-mini", "claude/sonnet"]
  },
  "asignacion_por_fase": {
    "implement": ["claude/opus", "codex/gpt-5-codex"],
    "plan":      ["claude/opus"]
  }
}
```
