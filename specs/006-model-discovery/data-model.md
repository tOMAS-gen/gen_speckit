# Data Model: Descubrimiento y verificación real de modelos

**Feature**: 006-model-discovery | **Fecha**: 2026-07-18

> Todos los campos nuevos son **aditivos y opcionales** (SC-005): un inventario/catálogo
> sin ellos sigue siendo válido y se comporta como hoy.

## Catálogo (`clis-catalog.json`) — campos nuevos por CLI

| Campo | Tipo | Semántica |
|---|---|---|
| `modelos_cmd` | string? | Comando no interactivo que lista modelos (si el CLI lo ofrece). Ausente = no hay. |
| `modelos_cmd_consume` | bool? | `true` si ese comando consume llamada/cuota → solo con aprobación. Default `false`. |
| `config_hints` | dict? por SO | Rutas de archivos de config locales del CLI que enumeran modelos/aliases (mismo shape que `auth_hints`: `{windows: [...], linux: [...], macos: [...]}`). |
| `fuentes_oficiales` | list[str]? | URLs de documentación oficial del proveedor con los modelos disponibles. |

## Inventario (`models.json`) — campos nuevos

Por **modelo** (dentro de `clis.<cli>.modelos[]`):

| Campo | Tipo | Valores |
|---|---|---|
| `origen` | string? | `detectado-local` \| `semilla` \| `oficial-sin-confirmar` |
| `esfuerzos` | list[str]? | Niveles de esfuerzo/razonamiento soportados (ej. `["low","medium","high"]`, `["thinking-high"]`) |

Por **CLI** (dentro de `clis.<cli>`):

| Campo | Tipo | Semántica |
|---|---|---|
| `verificacion_web` | dict? | `{estado: "hecha"\|"omitida", fecha: "YYYY-MM-DD", fuentes: [urls consultadas]}` |

## Reglas

1. **Prioridad de detección**: `modelos_cmd` (si existe y no consume, o aprobado) →
   `config_hints` → semillas del catálogo. Lo detectado localmente marca
   `origen: detectado-local` y **pisa** la semilla equivalente (mismo `id`).
2. **Cruce oficial**: modelos publicados en `fuentes_oficiales` que no estén detectados
   ni sembrados se agregan con `origen: oficial-sin-confirmar`; los detectados que además
   figuran oficialmente conservan `detectado-local`.
3. **Ranking**: `build_asignacion` NO filtra por `origen` (los tres participan —
   Clarifications). `capacidad`/`costo` de modelos nuevos: propuestos por el agente al
   presentar el resultado, corregibles por el usuario.
4. **Merge**: `merge_preserving_user_edits` cubre los campos nuevos — una edición manual
   de `esfuerzos`, `origen`, `capacidad`, etc. sobrevive re-escaneos.
5. **Nunca inventar** (FR-005): todo modelo tiene un `origen` de los tres valores; no hay
   cuarto origen "adivinado".

## Relaciones

```
clis-catalog (modelos_cmd/config_hints/fuentes_oficiales)
      └─> scan_models.py: detect_models(cli) ─> modelos con origen/esfuerzos
                └─> merge (ediciones del usuario prevalecen) ─> models.json
skill speckit-models ─> agente consulta fuentes_oficiales (best-effort)
                └─> aplica cruce vía script ─> origen oficial-sin-confirmar + verificacion_web
models.json ─> build_asignacion (sin filtro por origen) ─> ranking alta/media/baja
```
