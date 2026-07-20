# Implementation Plan: Clasificación de modelos por nivel y tarea desde leaderboard público

**Branch**: `007-arena-model-ranking` | **Date**: 2026-07-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-arena-model-ranking/spec.md`

## Summary

Que el nivel de cada modelo del inventario deje de salir de semillas escritas a mano y
salga de **evidencia pública comparable**, y que eso —más el plan contratado de cada
CLI— se declare **una sola vez por máquina** en lugar de por proyecto.

Tres piezas:

1. **`classify_models.py`** (script nuevo, stdlib): obtiene el ranking, lo normaliza a
   `capacidad` 1–10 y a fortalezas por categoría, lo cachea en un almacén de la máquina y
   propone el resultado al inventario.
2. **`scan_models.py`** (extensión mínima): aplica la clasificación **antes** de
   `build_asignacion()` y agrega `asignacion_por_fase`. La prioridad del usuario sale
   gratis del merge que ya existe.
3. **`speckit-models` SKILL.md**: la pregunta única global/local, la confirmación de
   mapeos ambiguos, el camino de respaldo por agente y el resumen con el origen de cada
   nivel.

**El hallazgo de research que define el enfoque**: **arena.ai no tiene API pública** —
`/api/leaderboard*` devuelve **403** y no se pudo confirmar si el HTML es SSR o SPA, así
que scrapearlo sería una apuesta. Pero los datos que muestra ese sitio son los del dataset
oficial de LMArena publicado en HuggingFace, accesible como **JSON sobre HTTPS sin
autenticación** y verificado como idéntico a la web (`claude-fable-5` = 1507.48, rank 1).
Se consume esa fuente, con el scraping por agente como respaldo.

**La trampa que este plan existe para evitar**: el dataset tiene dos configs, `text` y
`text_style_control`. La que parece obvia por el nombre (`text`) **no es** la que muestra
el sitio: da rank 3 / 1493 para el mismo modelo que el sitio pone rank 1 / 1507. Elegir
mal produce un ranking distinto **sin ningún error visible**. Queda como regla C1 del
contrato y como aserción en V1 del quickstart.

## Technical Context

**Language/Version**: Python ≥3.11, solo stdlib (`urllib.request`, `json`, `os`,
`datetime`). Skill en Markdown.

**Primary Dependencies**: ninguna nueva. Se descartó `pyarrow`/`pandas` (Parquet) y
`platformdirs` por no justificar dependencias para 400 filas y una ruta por SO.

**Storage**:
- nuevo: `<config_dir>/gen-speckit/global.json` (fuera del repo, ver R2);
- extendidos de forma aditiva: `.specify/models.json`, `.specify/clis-catalog.json`;
- sin cambios de semántica: `.specify/models.scan.json`.

**Testing**: pytest en `tests/python/` (nuevo `test_classify_models.py` + extensión de
`test_scan_models.py` y `test_product_delivery.py`). La red se mockea siempre: ningún
test toca internet.

**Target Platform**: Windows / Linux / macOS, solo Python (Constitución v1.1.0).

**Project Type**: extensión de scripts de soporte + skill + contrato de datos.

**Performance Goals**: la clasificación agrega ≤30 s al comando (SC-004), con timeout
duro de 25 s; el camino "reutilizada" es puramente local (sin red).

**Constraints**: aditividad estricta (Principio I); corrección manual siempre gana
(FR-006); nunca excluir un modelo por falta de dato (Constitución IV); resultado
reproducible (SC-006); sin enviar nada del usuario a la fuente (FR-021).

**Scale/Scope**: 1 script nuevo (~250 líneas), 1 script extendido, 1 función nueva en
`platform_helper.py`, 1 skill actualizada, catálogo extendido, ~10 tests, 4 documentos de
diseño. ~380 modelos en el leaderboard, ~13 en el inventario típico.

## Constitution Check

*GATE: debe pasar antes de Phase 0 y re-verificarse tras Phase 1.*

| Principio | Cumplimiento | Verificación |
|---|---|---|
| **I. Compatibilidad aditiva** | Todos los campos nuevos son opcionales; `asignacion` no cambia de forma ni semántica; un `models.json` de hoy sigue siendo válido. | `test_no_regression.py`, invariante 1–2 del contrato |
| **II. Portabilidad multi-CLI** | La obtención vive en un **script Python**, no en una herramienta de un CLI. Un principal sin WebFetch clasifica igual. El respaldo por agente es opcional, no requisito. | FR-005a, V3 del quickstart |
| **III. El más barato que alcance** | Mejora la materia prima del reparto (niveles medidos en vez de estimados a ojo) sin consumir ni una llamada de modelo: la fuente es HTTP público. | R1 |
| **IV. Nunca discriminar** | Prohibido filtrar por ausencia de dato externo. Verificado con dos casos reales: `gpt-5.6-terra` y `kimi-for-coding` **no existen** en el leaderboard y deben seguir en el ranking. | Invariante 4, V5 del quickstart |
| **V. Decisiones caras al más capaz** | El triage y el asignador no cambian; reciben mejores datos. `asignacion_por_fase` es insumo, no reemplazo del criterio. | E5 de data-model |
| **VI. Mínima intervención** | Una sola pregunta por máquina (global sí/no) y solo los mapeos genuinamente ambiguos. El resto se resuelve solo y se cachea 7 días. | FR-013, R5 |

**Gate inicial**: PASA. **Re-verificación post-diseño**: PASA — el diseño no introdujo
violaciones nuevas; el punto más expuesto (Principio IV) quedó cubierto con un invariante
explícito y un caso de prueba con datos reales.

## Project Structure

### Documentation (this feature)

```text
specs/007-arena-model-ranking/
├── plan.md                      # Este archivo
├── spec.md · research.md · data-model.md · quickstart.md
├── checklists/requirements.md
├── contracts/classification.md  # CLI, fuente externa, esquema global, extensión de models.json
├── orchestration-report.md
└── tasks.md                     # (/speckit-tasks)
```

### Source Code (repository root)

```text
.specify/scripts/python/classify_models.py    # NUEVO: fetch → normalizar → cachear → proponer
.specify/scripts/python/platform_helper.py    # + user_config_dir(), write_json_atomic()
.specify/scripts/python/scan_models.py        # + hook de clasificación previo a build_asignacion();
                                              #   + build_asignacion_por_fase()
.specify/clis-catalog.json                    # + bloque "clasificacion" (fuente, escala, categorías, alias)
.claude/skills/speckit-models/SKILL.md        # + pregunta global/local, mapeos ambiguos, respaldo, resumen
src/specify_cli/gen_multicli/assets/          # espejos shippeables de los cuatro anteriores
tests/python/test_classify_models.py          # NUEVO: fetch mockeado, escala, mapeo, atomicidad, degradación
tests/python/test_scan_models.py              # + integración de la clasificación en el inventario
tests/python/test_product_delivery.py         # + el script nuevo se entrega con install_product
```

**Structure Decision**: la obtención y normalización viven en un script Python
autónomo — no en la skill — porque el Principio II exige que cualquier CLI principal
pueda clasificar, incluso sin herramienta web propia. La skill queda a cargo de lo único
que un script no puede hacer: **conversar** (la pregunta global/local, los mapeos
ambiguos) y **navegar como respaldo**. La configuración de la fuente vive en el catálogo,
no en el código, para absorber cambios del sitio sin un release.

Cada archivo tocado tiene un espejo shippeable en `src/specify_cli/gen_multicli/assets/`;
ambas copias se actualizan juntas (lo verifica `test_product_delivery.py`).

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Config equivocada (`text` vs `text_style_control`) da un ranking plausible pero incorrecto | Regla C1 del contrato + aserción numérica en V1 (`rating` ≈1507, no ≈1493) |
| El campo `rank` del dataset no coincide con el del sitio | Regla C2: ordenar por `rating` descendente; `rank_dataset` se guarda solo como referencia |
| La datasets-server API cambia o se cae | Respaldo por agente sobre las páginas del sitio (FR-005a); ante ambas fallas, `estado: "omitida"` y éxito (FR-018) |
| Nombres del leaderboard con sufijos de inferencia (`-thinking`, `-xhigh`) rompen el mapeo exacto | Normalización + confirmación del usuario para lo ambiguo (FR-004a); alias sembrados en el catálogo |
| Escribir el archivo global desde dos proyectos a la vez | Temporal en el mismo directorio + `os.replace()` (R3) |
| Pisar la configuración real del usuario al testear | `GEN_SPECKIT_GLOBAL_DIR` obligatorio en tests |

## Complexity Tracking

> Sin violaciones constitucionales. No aplica.
