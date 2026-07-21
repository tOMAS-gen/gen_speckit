# Research: Descubrimiento y verificación real de modelos por CLI

**Feature**: 006-model-discovery | **Fecha**: 2026-07-18

## Decisión 1 — Cómo detectar modelos localmente (sin inventar)

- **Hecho verificado** (sondeo local `--help`, sin cuota): claude 2.1.214, codex 0.144.5
  y kimi 0.27.0 **no exponen** un comando headless de listado de modelos — solo el flag
  `--model` para elegir uno.
- **Decisión**: cadena de detección por CLI, declarada en el catálogo (genérica, sin
  nombres en el código):
  1. `modelos_cmd` (si el CLI lo tiene — vacío para los 3 actuales, listo para terceros);
  2. `config_hints`: parsear archivos de configuración locales del CLI que enumeren
     modelos/aliases (TOML/JSON; `tomllib` y `json` de stdlib) — gratis;
  3. semillas del catálogo (comportamiento actual) como piso.
- **Rationale**: máxima evidencia real con costo cero; extensible a CLIs que sí listen.
- **Alternativas**: sondeo por error (`--model invalido` para que el CLI liste válidos) —
  descartado como default (comportamiento no garantizado y puede consumir); queda
  cubierto por el sondeo opt-in.

## Decisión 2 — Sondeo con consumo (opt-in)

- **Decisión**: flag `--probe-models` en el escaneo: una invocación mínima por CLI para
  confirmar que el modelo responde (paridad con `--probe-auth`). Nunca por defecto
  (FR-006).

## Decisión 3 — Verificación oficial (la hace el agente)

- **Decisión**: el catálogo declara `fuentes_oficiales` (URLs de docs del proveedor) por
  CLI. La skill `speckit-models` instruye al **agente** (quien sí navega) a consultarlas
  best-effort, cruzar con lo detectado y aplicar el resultado usando el propio script
  (respetando el merge). Sin red → se omite declarándolo (FR-004, SC-004).
- **Rationale**: los scripts no navegan; el agente es portable (cualquier CLI principal).

## Decisión 4 — Contrato aditivo y ranking

- **Decisión**: cada modelo gana campos opcionales `origen`
  (`detectado-local` | `semilla` | `oficial-sin-confirmar`) y `esfuerzos` (lista de
  niveles, ej. `["low","medium","high"]`), más un bloque de metadatos del escaneo
  (`verificacion_web`: hecha/omitida + fecha). Consumidores actuales ignoran los campos
  nuevos (aditivo, SC-005).
- **Ranking**: los tres orígenes participan por igual (Clarifications, opción B del
  usuario); `build_asignacion` no filtra por origen. El fallback del orquestador absorbe
  indisponibles reales.

## Riesgos / puntos abiertos

- Ubicación y formato exactos de los config files por CLI (kimi `config.toml`, codex
  `config.toml`, claude settings): confirmarlos al implementar y declararlos en
  `config_hints` con parseo tolerante (archivo ausente/formato nuevo → seguir sin él).
- Fuentes oficiales cambian de URL/estructura: por eso viven en el catálogo (datos, no
  código) y la verificación es best-effort.
- Merge de campos nuevos: reutiliza `merge_preserving_user_edits` existente (las
  ediciones manuales de `esfuerzos`/`origen` sobreviven re-escaneos).
