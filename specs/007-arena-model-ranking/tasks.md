---

description: "Task list for feature 007 — clasificación de modelos por nivel y tarea"
---

# Tasks: Clasificación de modelos por nivel y tarea desde leaderboard público

**Input**: Design documents from `/specs/007-arena-model-ranking/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/classification.md](./contracts/classification.md), [quickstart.md](./quickstart.md)

**Tests**: incluidos. No los pidió el spec explícitamente, pero la Constitución (§Flujo de
Trabajo) exige validar toda skill o script nuevo, el proyecto ya tiene suite pytest, y el
quickstart define 9 escenarios de validación. Los tests **nunca** tocan la red.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: user story de spec.md (US1–US4)
- Rutas exactas incluidas en cada descripción

## Path Conventions

Proyecto Python de un solo árbol: scripts en `.specify/scripts/python/`, espejos
shippeables en `src/specify_cli/gen_multicli/assets/`, tests en `tests/python/`.

**Regla que aplica a casi toda tarea de código**: cada archivo tocado en
`.specify/scripts/python/` o `.claude/skills/` tiene un espejo en
`src/specify_cli/gen_multicli/assets/`; ambos se actualizan **en la misma tarea**, o
`test_product_delivery.py` falla.

---

## Phase 1: Setup

**Purpose**: configuración declarativa y utilidades de plataforma que todo lo demás usa

- [ ] T001 [P] [C:baja] [M:claude/haiku] Agregar el bloque `clasificacion` (dataset_url, dataset, config `text_style_control`, split, url_web, frescura_dias 7, votos_minimos 500, timeout_s 25, escala {piso 950, paso 56}, categorias_por_fase, alias) en `.specify/clis-catalog.json` y su espejo `src/specify_cli/gen_multicli/assets/clis-catalog.json`, según §E6 de data-model.md
- [ ] T002 [P] [C:media] [M:kimi/kimi-for-coding] Agregar `user_config_dir()` en `.specify/scripts/python/platform_helper.py` y su espejo: resuelve `%APPDATA%\gen-speckit` / `~/Library/Application Support/gen-speckit` / `${XDG_CONFIG_HOME:-~/.config}/gen-speckit`, con override por variable de entorno `GEN_SPECKIT_GLOBAL_DIR` (R2 de research.md)
- [ ] T003 [C:media] [M:kimi/kimi-for-coding] Agregar `write_json_atomic()` en `.specify/scripts/python/platform_helper.py` y su espejo: escribe a temporal en el **mismo directorio** y hace `os.replace()`, preservando UTF-8 sin BOM e indentación 2 (R3, FR-017). Depende de T002 por tocar el mismo archivo
- [ ] T004 [P] [C:baja] [M:claude/haiku] Crear `tests/python/test_platform_global_dir.py`: `user_config_dir()` por familia de SO, respeto del override, y que `write_json_atomic()` no deja archivo parcial ante excepción a mitad de escritura

---

## Phase 2: Foundational (bloqueante para todas las historias)

**Purpose**: el esqueleto del script nuevo y el acceso al almacén de la máquina. Sin
esto ninguna historia puede completarse.

**⚠️ Ninguna tarea de Phase 3+ puede empezar antes de terminar esta fase.**

- [ ] T005 [C:media] [M:kimi/kimi-for-coding] Crear `.specify/scripts/python/classify_models.py` y su espejo con el esqueleto de CLI del contrato §1: flags `--json`, `--refrescar`, `--desde-agente`, `--sin-red`, `--global si|no`, `--olvidar-global`, `--repo-root`; códigos de salida 0/2/3; salida JSON con la forma exacta documentada
- [ ] T006 [C:media] [M:kimi/kimi-for-coding] Implementar en `classify_models.py` la lectura del almacén de la máquina: parseo tolerante que ante JSON inválido o `version` desconocida avisa y sigue **sin pisar el archivo**, preservando `planes` y `mapeos` declarados por el usuario (FR-020, contrato §5.7)
- [ ] T007 [C:alta] [M:claude/fable] Implementar en `classify_models.py` la escritura del almacén vía `write_json_atomic()`, con validación previa de que no contiene claves prohibidas (rutas, tokens, `headless`, `cuota*`) (FR-016, contrato §3). Depende de T006
- [ ] T008 [P] [C:baja] [M:claude/haiku] Crear `tests/python/test_classify_store.py`: almacén ausente, válido, corrupto y de versión desconocida; que los `planes` sobreviven a una versión no reconocida; que el validador rechaza claves prohibidas

**Checkpoint**: el script existe, responde `--json` y maneja el almacén sin romperse.

---

## Phase 3: User Story 1 — Modelos clasificados con evidencia externa (P1) 🎯 MVP

**Goal**: que cada modelo del inventario con correspondencia en el leaderboard quede con
su nivel derivado del puntaje real, y que el resto conserve el suyo.

**Independent Test**: correr el script con red y verificar en `models.json` que los
modelos matcheados traen `nivel_origen: "medido"` y `clasificacion.rating`, y que los no
matcheados conservan su nivel y siguen en `asignacion` (quickstart V1, V5).

- [ ] T009 [US1] [C:alta] [M:claude/fable] Implementar `fetch_dataset()` en `.specify/scripts/python/classify_models.py` con `urllib.request`: GET a datasets-server con `config=text_style_control`, timeout del catálogo, sin cookies ni credenciales; una petición por categoría del mapeo más `overall` (contrato §2, reglas C1/C4/C5)
- [ ] T010 [US1] [C:alta] [M:claude/fable] Implementar `normalize_rows()` en `classify_models.py`: descarta filas sin `model_name`/`organization`/`rating`/`leaderboard_publish_date`, descarta las que no llegan a `votos_minimos`, **ordena por `rating` descendente ignorando `rank`** (regla C2), y toma la fecha de `leaderboard_publish_date` (regla C3, FR-002, FR-019a)
- [ ] T011 [US1] [C:alta] [M:claude/fable] Implementar `match_models()` en `classify_models.py`: normaliza identificadores del inventario contra `model_name`, aplica los `alias` del catálogo, resuelve solo lo inequívoco y devuelve el resto en `ambiguos[]` **sin elegir por similitud** (FR-003, FR-004a, contrato §5.5)
- [ ] T012 [US1] [C:media] [M:kimi/kimi-for-coding] Implementar en `classify_models.py` la **persistencia de los mapeos**: antes de reportar una ambigüedad, consultar `mapeos` del almacén de la máquina; tras la elección del usuario, guardarla con `modo: "usuario"` para que no se vuelva a preguntar en ninguna corrida ni en ningún proyecto (FR-004, §E1 de data-model.md, contrato §3)
- [ ] T013 [US1] [C:baja] [M:claude/haiku] Implementar `rating_a_capacidad()` en `classify_models.py`: `clamp(1, 10, floor((rating - piso) / paso) + 1)` con piso/paso del catálogo, y marcado de `nivel_origen` en `medido`/`estimado` (FR-005, R4)
- [ ] T014 [US1] [C:media] [M:kimi/kimi-for-coding] Implementar en `classify_models.py` la aplicación al inventario: escribe `capacidad`, `nivel_origen`, `clasificacion` y `fortalezas` en `clis.<cli>.modelos[]` de `.specify/models.json` conservando el nivel previo de los modelos sin dato externo (FR-005, FR-010, §E4 de data-model.md)
- [ ] T015 [US1] [C:alta] [M:claude/fable] Enganchar la clasificación en `.specify/scripts/python/scan_models.py` y su espejo: aplicarla sobre `proposed` **antes** de `build_asignacion()`, de modo que `merge_preserving_user_edits()` haga valer la corrección manual sin código nuevo (R7, FR-006)
- [ ] T016 [P] [US1] [C:media] [M:kimi/kimi-for-coding] Crear `tests/python/test_classify_fetch.py` con respuestas HTTP mockeadas: que se pide `text_style_control` y nunca `text`; que el orden sale de `rating` y no de `rank`; que se respeta el timeout; que una fila sin campos obligatorios se descarta
- [ ] T017 [P] [US1] [C:media] [M:kimi/kimi-for-coding] Crear `tests/python/test_classify_match.py`: casos reales del research — `fable`→`claude-fable-5` y `k3`→`kimi-k3` inequívocos; `opus`/`sonnet`/`gpt-5.5` ambiguos; `gpt-5.6-terra` y `kimi-for-coding` **inexistentes** deben quedar sin `clasificacion` y **seguir en `asignacion`** (Constitución IV)
- [ ] T018 [P] [US1] [C:media] [M:kimi/kimi-for-coding] Extender `tests/python/test_scan_models.py`: una `capacidad` editada a mano sobrevive al refresco con `nivel_origen: "manual"` (FR-006, SC-007, quickstart V4)
- [ ] T019 [US1] [C:media] [M:kimi/kimi-for-coding] Actualizar `.claude/skills/speckit-models/SKILL.md` y su espejo `src/specify_cli/gen_multicli/assets/skills-multicli/speckit-models/SKILL.md`: paso de clasificación, confirmación de mapeos ambiguos dentro de la tanda de preguntas existente, resumen con el origen del nivel de cada modelo, y **aviso de discrepancia** cuando el nivel corregido a mano difiere del puntaje medido —informado, nunca aplicado— (FR-004a, FR-006, SC-005)

**Checkpoint**: US1 entregable por sí sola — el inventario ya tiene niveles medidos.

---

## Phase 4: User Story 2 — Lo que es de la máquina se declara una sola vez (P1)

**Goal**: clasificación y plan/suscripción se declaran una vez por máquina y se heredan
en cualquier proyecto nuevo.

**Independent Test**: aceptar el guardado global en el proyecto A y verificar en un
proyecto B que no hay consulta a la red ni preguntas (quickstart V2).

- [ ] T020 [US2] [C:media] [M:kimi/kimi-for-coding] Implementar en `.specify/scripts/python/classify_models.py` el guardado de `clasificacion` en el almacén de la máquina cuando `compartir == "si"`, incluyendo `fuente`, `via`, `publicado`, `obtenido` y `escala` (§E2 de data-model.md)
- [ ] T021 [US2] [C:alta] [M:claude/fable] Implementar en `classify_models.py` la resolución por precedencia de FR-012 (edición manual → local → global → catálogo) y reportar en la salida `--json` qué fuente ganó para cada modelo
- [ ] T022 [US2] [C:media] [M:kimi/kimi-for-coding] Implementar en `classify_models.py` la herencia de `planes` por CLI desde el almacén, con marcado de "dato heredado" y persistencia de la corrección del usuario de vuelta al almacén (FR-016a)
- [ ] T023 [US2] [C:media] [M:kimi/kimi-for-coding] Implementar en `classify_models.py` los flags `--global si|no` y `--olvidar-global`, y la señal `preguntar_global` que emite el script cuando `compartir` aún no está definido (FR-013, FR-015)
- [ ] T024 [US2] [C:baja] [M:claude/haiku] Implementar en `classify_models.py` la degradación cuando el directorio de configuración no es escribible: avisar y seguir guardando solo en el proyecto (FR-020a)
- [ ] T025 [P] [US2] [C:media] [M:kimi/kimi-for-coding] Crear `tests/python/test_classify_global.py`: la pregunta se emite una sola vez; `compartir: "no"` no escribe el almacén; segundo proyecto resuelve sin red; precedencia de FR-012 con los cuatro orígenes; directorio no escribible degrada sin fallar
- [ ] T026 [US2] [C:media] [M:kimi/kimi-for-coding] Actualizar `.claude/skills/speckit-models/SKILL.md` y su espejo: formular la pregunta global/local una única vez a partir de `preguntar_global`, explicando qué se guarda y qué no, y mostrar en el resumen los datos heredados del almacén (FR-013, FR-016)

**Checkpoint**: US1 + US2 — el usuario no vuelve a declarar nada en proyectos nuevos.

---

## Phase 5: User Story 3 — Reparto por tipo de tarea (P2)

**Goal**: cada fase recibe primero al modelo fuerte en la categoría que esa fase necesita.

**Independent Test**: verificar que `asignacion_por_fase` existe, que `implement` puede
encabezar con un modelo distinto al de `plan`, y que `asignacion` quedó intacta
(quickstart V6).

- [ ] T027 [US3] [C:media] [M:kimi/kimi-for-coding] Implementar en `.specify/scripts/python/classify_models.py` el cálculo de `fortalezas` por modelo: aplicar la misma escala al `rating` de cada categoría del mapeo (`coding`, `math`, `creative_writing`, `instruction_following`) (§E4 de data-model.md)
- [ ] T028 [US3] [C:alta] [M:claude/fable] Implementar `build_asignacion_por_fase()` en `.specify/scripts/python/scan_models.py` y su espejo: ordena por `fortalezas[categoria]` descendente, desempata por `costo` ascendente y luego orden de aparición; incluye a los modelos sin fortalezas ordenados por `capacidad` (FR-009, FR-010, FR-011, §E5)
- [ ] T029 [US3] [C:baja] [M:claude/haiku] Escribir `asignacion_por_fase` como sección hermana de `asignacion` en `.specify/models.json`, sin alterar la forma ni la semántica de `asignacion` (contrato §5.1–5.2)
- [ ] T030 [P] [US3] [C:media] [M:kimi/kimi-for-coding] Crear `tests/python/test_asignacion_por_fase.py`: que `asignacion` no cambia respecto de la corrida previa; que todo CLI instalado y autenticado aparece en al menos una lista por fase; que dos corridas idénticas producen listas idénticas (SC-006, FR-011)
- [ ] T031 [US3] [C:media] [M:kimi/kimi-for-coding] Documentar en `.specify/orchestrator/assign.md` y su espejo cómo cruzar `asignacion` (filtro por complejidad) con `asignacion_por_fase` (orden por fortaleza), dejando claro que `asignacion_por_fase` puede faltar y el playbook debe seguir funcionando

---

## Phase 6: User Story 4 — Sin red y sin sorpresas (P2)

**Goal**: que una fuente externa caída nunca deje al usuario sin inventario.

**Independent Test**: con la fuente inaccesible, el comando termina con éxito, avisa el
motivo y usa lo guardado si existe (quickstart V3, V8).

- [ ] T032 [US4] [C:media] [M:kimi/kimi-for-coding] Implementar en `.specify/scripts/python/classify_models.py` el control de frescura: `obtenido` más viejo que `frescura_dias` dispara refresco; con red caída se usa igual informando la antigüedad; `--refrescar` ignora la frescura (FR-019, R5)
- [ ] T033 [US4] [C:media] [M:kimi/kimi-for-coding] Implementar en `classify_models.py` el manejo de fallo de la fuente: timeout, error de red, HTTP no-200 o JSON inválido producen `estado: "omitida"` con `motivo`, exit 0 y el inventario intacto (FR-018, SC-003)
- [ ] T034 [US4] [C:media] [M:kimi/kimi-for-coding] Implementar en `classify_models.py` el camino de respaldo `--desde-agente <archivo>`: lee filas obtenidas por el agente y las somete a **las mismas validaciones** que las de la API, marcando `via: "agente"` (FR-005a, contrato §2)
- [ ] T035 [P] [US4] [C:media] [M:kimi/kimi-for-coding] Crear `tests/python/test_classify_degradacion.py`: timeout, HTTP 500, JSON inválido, `--sin-red` sin dato previo y con dato previo; todos deben terminar en exit 0 con `models.json` válido
- [ ] T036 [US4] [C:media] [M:kimi/kimi-for-coding] Actualizar `.claude/skills/speckit-models/SKILL.md` y su espejo: cuando el script informa fallo de la fuente, la skill ofrece el camino por agente (consultar `arena.ai/leaderboard/<categoria>` y pasarlo con `--desde-agente`) y nunca deja el comando en error

---

## Phase 7: Polish & Cross-Cutting

- [ ] T037 [P] [C:baja] [M:claude/haiku] Extender `tests/python/test_product_delivery.py` para que `install_product` entregue `classify_models.py` y el bloque `clasificacion` del catálogo
- [ ] T038 [P] [C:baja] [M:claude/haiku] Verificar no-regresión completa con `uv run pytest tests/python/ -q`, prestando atención a `test_no_regression.py` y `test_merge_campos_nuevos.py` (son los que garantizan la aditividad)
- [ ] T039 [P] [C:media] [M:kimi/kimi-for-coding] Actualizar `specs/001-multi-cli-orchestrator/contracts/models-schema.md` con los campos aditivos nuevos (`nivel_origen`, `clasificacion`, `fortalezas`, `asignacion_por_fase`), marcados como opcionales
- [ ] T040 [C:alta] [M:claude/fable] Ejecutar el quickstart completo (V1–V9) contra la máquina real y registrar el resultado en `specs/007-arena-model-ranking/quickstart.md`, con atención especial a V1 (`rating` ≈1507, no ≈1493) y V5 (modelos inexistentes que siguen en el ranking)
- [ ] T041 [P] [C:baja] [M:claude/haiku] Actualizar `README.md` con la nueva capacidad (niveles medidos + configuración global de máquina) vía `/speckit-readme`

---

## Dependencies

```
Phase 1 (T001–T004)  ─┐
                      ├─▶ Phase 2 (T005–T008) ─┬─▶ US1 (T009–T019) ─┬─▶ US3 (T027–T031)
                      │                        │                    │
                      │                        └─▶ US2 (T020–T026)  │
                      │                                             │
                      └─────────────────────────────────────────────┴─▶ US4 (T032–T036) ─▶ Polish (T037–T041)
```

- **US1 y US2 son independientes entre sí** una vez terminada la Phase 2: US1 toca el
  pipeline de clasificación; US2, el almacén y la precedencia. Pueden ir en paralelo por
  personas distintas, aunque comparten archivo (`classify_models.py`), así que **no** son
  `[P]` entre sí para un despacho automático.
- **US3 depende de US1** (necesita `fortalezas`, que sale de los datos por categoría).
- **US4 depende de US1** (envuelve el fetch) y se beneficia de US2 (reutiliza lo guardado).
- T003 depende de T002 (mismo archivo). T007 depende de T006 (mismo archivo).

## Parallel Opportunities

Todas las tareas de test son `[P]` entre sí y respecto de otras historias: T004, T008,
T016, T017, T018, T025, T030, T035, T037.

En Phase 1, T001 y T002 son `[P]` (catálogo vs. helper). En Polish, T037/T038/T039/T041
son `[P]`.

**Advertencia sobre paralelismo real**: las tareas T009–T015, T020–T024, T027, T032–T034
tocan todas `classify_models.py`. No están marcadas `[P]` a propósito — despacharlas en
paralelo produciría conflictos de escritura sobre el mismo archivo.

## Implementation Strategy

**MVP = Phase 1 + Phase 2 + US1 (T001–T019)**. Con eso el inventario ya tiene niveles
medidos con evidencia pública en lugar de semillas a ojo, que es el corazón del pedido.

Incrementos siguientes, cada uno entregable por separado:

1. **+US2** — deja de repetirse la configuración en cada proyecto (el segundo pedido
   explícito del usuario).
2. **+US4** — blinda el comando contra la caída de la fuente. *Conviene subirlo antes que
   US3 si la feature va a usarse en serio: sin US4, una caída del sitio degrada la
   experiencia de todos los proyectos.*
3. **+US3** — refina el reparto por tipo de fase.

**Regla de corte**: si algo se cae, US1 sola ya justifica la feature; US3 es la única que
puede quedar afuera sin romper la promesa hecha al usuario.
