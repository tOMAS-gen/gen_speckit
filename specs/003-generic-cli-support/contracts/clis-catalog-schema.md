# Contract: catálogo de CLIs (`.specify/clis-catalog.json`)

**Feature**: 003-generic-cli-support

Datos versionados en el repo. Solo lectura en runtime. Productor: el proyecto (y el
usuario que lo corrige). Consumidores: `scan-models.ps1`, `invoke-secondary.ps1`,
`clis-config.ps1`, skill `speckit-clis`.

## JSON Schema (draft-07)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SpecKit Multi-CLI Known CLIs Catalog",
  "type": "object",
  "required": ["version", "clis"],
  "properties": {
    "version": { "type": "integer", "minimum": 1 },
    "patrones_cuota_genericos": {
      "type": "array", "items": { "type": "string" }, "minItems": 1
    },
    "clis": {
      "type": "object",
      "propertyNames": { "pattern": "^[a-z][a-z0-9-]*$" },
      "additionalProperties": {
        "type": "object",
        "required": ["headless"],
        "properties": {
          "headless":       { "type": "string", "pattern": "\\{prompt\\}" },
          "version_cmd":    { "type": "string" },
          "auth_hints": {
            "type": "object",
            "properties": {
              "windows": { "type": "array", "items": { "type": "string" } },
              "linux":   { "type": "array", "items": { "type": "string" } },
              "macos":   { "type": "array", "items": { "type": "string" } }
            }
          },
          "patrones_cuota": { "type": "array", "items": { "type": "string" } },
          "modelos_semilla": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["id", "capacidad", "costo"],
              "properties": {
                "id":         { "type": "string", "minLength": 1 },
                "capacidad":  { "type": "integer", "minimum": 1, "maximum": 10 },
                "costo":      { "type": "integer", "minimum": 1, "maximum": 3 },
                "contexto_k": { "type": ["integer", "string"] }
              }
            }
          },
          "quirks": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

## Invariantes

1. **Solo lectura en runtime**: ningún script escribe el catálogo; los cambios llegan
   por versionado (git) o edición manual.
2. **Resolución de datos**: para cualquier dato de un CLI, la precedencia es
   `models.json` (usuario) > catálogo > defaults genéricos
   (`patrones_cuota_genericos`; `version_cmd: "--version"`).
3. **Rutas en `auth_hints` portables**: pueden usar `~` y variables (`$HOME`,
   `%USERPROFILE%`); `platform.ps1` las expande según el SO.
4. **Catálogo ausente o inválido**: el sistema sigue funcionando con el inventario +
   defaults genéricos, avisando (nunca es fatal — el inventario es la fuente de
   verdad operativa).
5. **Codificación**: UTF-8 sin BOM, indentación 2 (igual que el inventario).
