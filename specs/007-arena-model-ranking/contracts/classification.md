# Contract: clasificación de modelos (feature 007)

**Feature**: 007-arena-model-ranking

Contrato entre `classify_models.py` (productor), el usuario (editor con prioridad),
`scan_models.py` / `/speckit-models` (integradores) y triage/asignador (consumidores).
Extiende el contrato [`models-schema.md`](../../001-multi-cli-orchestrator/contracts/models-schema.md)
de forma **estrictamente aditiva**: un `models.json` de hoy sigue siendo válido.

## 1. Interfaz de línea de comandos

```
python .specify/scripts/python/classify_models.py [opciones]
```

| Flag | Efecto |
|---|---|
| `--json` | Imprime el resumen en JSON (para consumo de la skill). |
| `--refrescar` | Ignora la frescura y vuelve a consultar la fuente. |
| `--desde-agente <archivo>` | Camino de respaldo: lee filas ya obtenidas por el agente y las normaliza. Implica no tocar la red. |
| `--sin-red` | Prohíbe cualquier salida a la red; usa solo lo guardado. |
| `--global si\|no` | Fija `compartir` sin preguntar (la skill lo pasa tras consultar al usuario). |
| `--olvidar-global` | Borra el almacén de la máquina (FR-015). |
| `--repo-root <ruta>` | Igual que el resto de los scripts. |

**Códigos de salida**: `0` éxito (incluye "clasificación omitida por falta de red" —
FR-018 exige que no falle); `2` error de uso; `3` almacén global ilegible **y** no
recuperable (se informa y se sigue sin él, ver §5).

### Salida `--json`

```json
{
  "estado": "actualizada" | "reutilizada" | "omitida",
  "motivo": "sin-red" | "fuente-invalida" | "fresca" | null,
  "via": "dataset" | "agente" | null,
  "publicado": "2026-07-16",
  "obtenido": "2026-07-19T11:02:44-03:00",
  "global": { "usado": true, "ruta": "C:\\Users\\x\\AppData\\Roaming\\gen-speckit\\global.json" },
  "modelos": { "medidos": 5, "estimados": 2, "ambiguos": 3 },
  "ambiguos": [
    { "ref": "claude/opus", "candidatos": ["claude-opus-4-8", "claude-opus-4-8-thinking"] }
  ],
  "preguntar_global": true
}
```

`preguntar_global: true` es la única señal que hace que la skill formule la pregunta de
FR-013. El script **nunca** interactúa por sí mismo.

## 2. Contrato con la fuente externa

**Petición** (única forma soportada en el camino principal):

```
GET https://datasets-server.huggingface.co/filter
    ?dataset=lmarena-ai%2Fleaderboard-dataset
    &config=text_style_control
    &split=latest
    &where="category"='<categoria>'
    &orderby="rating" DESC
    &offset=0&length=<n>
```

**Restricciones obligatorias** (violarlas produce un ranking incorrecto sin error visible):

| # | Regla | Motivo |
|---|---|---|
| C1 | `config` DEBE ser `text_style_control`. **Nunca** `text`. | `text` da otro ranking (fable rank 3/1493 vs. rank 1/1507). |
| C2 | El orden DEBE derivarse de `rating` descendente. **Nunca** de `rank`. | El `rank` del dataset no coincide con el del sitio. |
| C3 | La fecha del snapshot DEBE leerse de `leaderboard_publish_date`. | Difiere por arena; no hay fecha global. |
| C4 | La petición DEBE ser GET, sin cookies, sin credenciales y sin cuerpo. | FR-021: no se envía nada del usuario ni del proyecto. |
| C5 | DEBE haber timeout (`clasificacion.timeout_s`, 25 s por defecto). | FR-018 / SC-004: nunca colgarse. |
| C6 | Las filas con `vote_count` menor a `clasificacion.votos_minimos` (500 por defecto) DEBEN descartarse y tratarse como "sin dato externo". | FR-019a: una muestra chica produce un puntaje inestable que movería el reparto sin causa real. |

**Respuesta mínima aceptable**: objeto con `rows[]`, cada uno con `row` que contenga
`model_name`, `organization`, `rating` y `leaderboard_publish_date`. Falta alguno de esos
cuatro ⇒ la fila se descarta; si se descartan **todas**, `estado: "omitida"`,
`motivo: "fuente-invalida"` y se conserva lo guardado (FR-018).

**Camino de respaldo** (`--desde-agente`): archivo JSON con la misma forma
(`{"rows": [{"row": {...}}]}`), producido por el agente a partir de
`https://arena.ai/leaderboard/text/<categoria>`. Se le aplican exactamente las mismas
validaciones — el respaldo no es una puerta trasera para datos peor validados.

## 3. Esquema del almacén de la máquina

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "gen_speckit global store",
  "type": "object",
  "required": ["version"],
  "properties": {
    "version": { "const": 1 },
    "compartir": { "enum": ["si", "no"] },
    "planes": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["plan"],
        "properties": {
          "plan": { "type": "string" },
          "declarado": { "type": "string", "format": "date" }
        }
      }
    },
    "mapeos": {
      "type": "object",
      "propertyNames": { "pattern": "^[a-z0-9_-]+/[A-Za-z0-9._-]+$" },
      "additionalProperties": {
        "type": "object",
        "required": ["entrada", "modo"],
        "properties": {
          "entrada": { "type": ["string", "null"] },
          "modo": { "enum": ["auto", "usuario"] },
          "confianza": { "enum": ["alta", "media"] }
        }
      }
    },
    "clasificacion": {
      "type": "object",
      "required": ["fuente", "publicado", "obtenido", "entradas"],
      "properties": {
        "fuente": { "type": "string" },
        "via": { "enum": ["dataset", "agente"] },
        "publicado": { "type": "string", "format": "date" },
        "obtenido": { "type": "string", "format": "date-time" },
        "escala": {
          "type": "object",
          "properties": {
            "piso": { "type": "number" },
            "paso": { "type": "number", "exclusiveMinimum": 0 }
          }
        },
        "entradas": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["model_name", "rating"],
            "properties": {
              "model_name":   { "type": "string", "minLength": 1 },
              "organization": { "type": "string" },
              "rating":       { "type": "number" },
              "rank_dataset": { "type": "integer" },
              "vote_count":   { "type": "integer" },
              "categorias": {
                "type": "object",
                "additionalProperties": {
                  "type": "object",
                  "properties": {
                    "rating": { "type": "number" },
                    "rank":   { "type": "integer" }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

**Prohibido en este archivo** (FR-016): rutas de proyecto, tokens, credenciales,
comandos `headless`, `cuota`, `cuota_desde`, `cuota_reset`. Un validador debe rechazar el
archivo si aparece cualquiera de esas claves.

## 4. Extensión de `models.json`

Campos nuevos, todos opcionales:

```json
{
  "clis": {
    "claude": {
      "modelos": [
        {
          "id": "fable", "capacidad": 10, "costo": 3, "contexto_k": "desconocido",
          "nivel_origen": "medido",
          "clasificacion": {
            "entrada": "claude-fable-5",
            "rating": 1507.48,
            "publicado": "2026-07-16",
            "fuente_dato": "global"
          },
          "fortalezas": { "coding": 9, "math": 10, "creative_writing": 10, "instruction_following": 9 }
        }
      ]
    }
  },
  "asignacion": { "alta": ["claude/fable"], "media": ["..."], "baja": ["..."] },
  "asignacion_por_fase": {
    "implement": ["claude/fable", "codex/gpt-5.6-sol"],
    "plan":      ["claude/fable"],
    "specify":   ["claude/fable"]
  }
}
```

| Campo | Tipo | Requerido |
|---|---|---|
| `modelos[].nivel_origen` | `"medido"` \| `"estimado"` \| `"manual"` | no |
| `modelos[].clasificacion` | objeto (ver arriba) | no — ausente ⇒ sin dato externo |
| `modelos[].fortalezas` | objeto categoría→int 1–10 | no |
| `asignacion_por_fase` | objeto fase→lista `cli/modelo` | no |

## 5. Invariantes semánticos

1. **Aditividad** (Principio I): un `models.json` sin ninguno de estos campos es válido y
   se comporta igual que hoy. Ningún consumidor puede *requerir* `asignacion_por_fase`.
2. **`asignacion` intacta**: la clasificación cambia el **valor** de `capacidad`, nunca la
   forma ni la semántica de `asignacion`. Los playbooks existentes no se tocan.
3. **Prioridad del usuario** (FR-006, SC-007): el nivel se propone dentro del `proposed`
   que consume `merge_preserving_user_edits`; una `capacidad` editada a mano difiere de la
   propuesta previa y prevalece **sin código nuevo**. `nivel_origen: "manual"` es
   absorbente.
4. **No discriminación** (Constitución IV, FR-010): un modelo sin entrada en el
   leaderboard conserva su `capacidad` previa y sigue apareciendo en `asignacion` y en
   `asignacion_por_fase`. Está **prohibido** filtrar por ausencia de dato externo.
5. **Sin adivinar mapeos** (FR-004a): si un `cli/modelo` matchea más de una entrada y
   ninguna es exacta tras normalizar, `clasificacion` queda ausente y el caso se reporta
   en `ambiguos[]`. Está **prohibido** elegir por similitud.
6. **Determinismo** (FR-011, SC-006): mismo `global.json` + mismo `models.json` ⇒ mismo
   `asignacion_por_fase`, byte a byte. Desempates: `costo` ascendente, luego orden de
   aparición en el inventario. Prohibido usar `set` sin ordenar o iterar dicts sin
   `sorted()`.
7. **Degradación** (FR-018/FR-020): fuente caída, timeout, JSON inválido, `version`
   desconocida o archivo global corrupto ⇒ aviso + `estado: "omitida"` + éxito. Está
   **prohibido** sobrescribir un global ilegible sin avisar.
8. **Atomicidad** (FR-017): toda escritura del global va a un temporal en el mismo
   directorio + `os.replace()`.
9. **Codificación**: UTF-8 sin BOM, indentación 2, igual que `models.json`.
10. **Privacidad** (FR-021, FR-016): la petición no lleva datos del usuario; el archivo
    global no guarda nada del proyecto.
