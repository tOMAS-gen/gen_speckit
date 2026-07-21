# Reporte de Orquestación: Clasificación de modelos por nivel y tarea (arena.ai)

**Feature**: `007-arena-model-ranking` | **Creado**: 2026-07-19 | **Principal**: claude/opus

> Plantilla del reporte multi-CLI. Secciones PARSEABLES (tablas de columnas fijas,
> las lee la retomabilidad): "Modelos por fase" y "Asignaciones". Secciones
> INFORMATIVAS (prosa, solo para humanos): "Triage", "Eventos", "Métricas".
> Ninguna lógica debe depender de parsear las secciones informativas.

## Triage

- **Complejidad de la idea**: compleja
- **Justificación (rúbrica)**:
  - *Alcance* (compleja): toca la skill `speckit-models`, `scan_models.py`, el esquema de
    `.specify/models.json`, el ranking `asignacion` que consumen los playbooks del
    orquestador, **más** un almacén global fuera del proyecto y una integración con un
    sitio web de terceros.
  - *Ambigüedad* (compleja): sin definir el mapeo entre nombres del leaderboard e
    identificadores de los CLIs, qué categorías de tarea se usan, la precedencia
    global↔local y el alcance exacto de lo que se guarda global.
  - *Riesgo* (media): escribe en el directorio de configuración del usuario (fuera del
    repo) y depende de una fuente externa sin API documentada; reversible.
- **Flujo invocado**: IDEAL | **Flujo recomendado**: IDEAL
- **Resolución de discordancia**: n/a (coinciden)
- **Punto de entrada**: claude/opus (primer candidato disponible de `asignacion.alta`) →
  sin cambio (no corresponde escalar ni degradar)

## Modelos por fase

| Fase | Modelo asignado | Estado |
|------|-----------------|--------|
| specify | claude/fable | ejecutada |
| clarify | kimi/kimi-for-coding | ejecutada |
| plan | claude/fable | ejecutada |
| checklist | kimi/kimi-for-coding | ejecutada |
| tasks | kimi/kimi-for-coding | ejecutada |
| tasks:asignación | claude/fable | ejecutada |
| analyze | claude/fable | ejecutada |
| implement | (por tarea, ver Asignaciones) | ejecutada |

<!-- Estados válidos: pendiente | ejecutada | omitida. Filas según el flujo elegido. -->

## Asignaciones

**Reparto**: 41 tareas — 8 `alta` → `claude/fable`, 24 `media` → `kimi/kimi-for-coding`,
9 `baja` → `claude/haiku`. **80 % del trabajo va a modelos económicos** (costo < 3).

**Justificación obligatoria (Constitución IV / playbook assign.md paso 3)**: `codex` está
instalado, autenticado y con cuota `ok`, pero quedó con **cero tareas**. No es una
exclusión por preferencia: el playbook manda tomar el *primer* candidato de cada nivel, y
en el ranking actual codex no encabeza ninguno (`alta` → `claude/fable`, `media` →
`kimi/kimi-for-coding`, `baja` → `claude/haiku`). Codex sigue participando como **fallback
inmediato** si cualquiera de esos tres agota cuota. Vale registrar que este reparto se
apoya en capacidades **sembradas a mano** — que es justamente lo que esta feature viene a
reemplazar por puntajes medidos; es esperable que el reparto cambie una vez implementada.

| Tarea | C | M | Estado |
|-------|---|---|--------|
| T001 | baja | claude/haiku | verificada |
| T002 | media | kimi/kimi-for-coding | verificada |
| T003 | media | kimi/kimi-for-coding | verificada |
| T004 | baja | claude/haiku | verificada |
| T005 | media | kimi/kimi-for-coding | verificada |
| T006 | media | kimi/kimi-for-coding | verificada |
| T007 | alta | claude/fable | verificada |
| T008 | baja | claude/haiku | verificada |
| T009 | alta | claude/fable | verificada |
| T010 | alta | claude/fable | verificada |
| T011 | alta | claude/fable | verificada |
| T012 | media | kimi/kimi-for-coding | verificada |
| T013 | baja | claude/haiku | verificada |
| T014 | media | kimi/kimi-for-coding | verificada |
| T015 | alta | claude/fable | verificada |
| T016 | media | kimi/kimi-for-coding | verificada |
| T017 | media | kimi/kimi-for-coding | verificada |
| T018 | media | kimi/kimi-for-coding | verificada |
| T019 | media | kimi/kimi-for-coding | verificada |
| T020 | media | kimi/kimi-for-coding | verificada |
| T021 | alta | claude/fable | verificada |
| T022 | media | kimi/kimi-for-coding | verificada |
| T023 | media | kimi/kimi-for-coding | verificada |
| T024 | baja | claude/haiku | verificada |
| T025 | media | kimi/kimi-for-coding | verificada |
| T026 | media | kimi/kimi-for-coding | verificada |
| T027 | media | kimi/kimi-for-coding | verificada |
| T028 | alta | claude/fable | verificada |
| T029 | baja | claude/haiku | no-despachada |
| T030 | media | kimi/kimi-for-coding | verificada |
| T031 | media | kimi/kimi-for-coding | verificada |
| T032 | media | kimi/kimi-for-coding | verificada |
| T033 | media | kimi/kimi-for-coding | verificada |
| T034 | media | kimi/kimi-for-coding | verificada |
| T035 | media | kimi/kimi-for-coding | verificada |
| T036 | media | kimi/kimi-for-coding | verificada |
| T037 | baja | claude/haiku | verificada |
| T038 | baja | claude/haiku | no-despachada |
| T039 | media | kimi/kimi-for-coding | verificada |
| T040 | alta | claude/fable | no-despachada |
| T041 | baja | claude/haiku | no-despachada |

## Eventos

- [2026-07-19] triage — idea clasificada compleja; flujo IDEAL invocado y recomendado coinciden; sin escalada ni degradación.
- [2026-07-19] triage — fuente externa verificada antes de especificar: `arena.ai/leaderboard/text` responde y expone Rank/Model/Organization/Score/Votes/Price/Context y ~29 categorías; no documenta API pública.
- [2026-07-19] modo — fases de especificación ejecutadas en el principal (decisión-registrada); el despacho a secundarios vía `invoke_secondary.py` aplica en implement.
- [2026-07-19] specify — `spec.md` y `checklists/requirements.md` creados; checklist de calidad completo sin marcadores [NEEDS CLARIFICATION].
- [2026-07-19] plan — research delegado a un subagente: arena.ai NO tiene API pública (`/api/leaderboard*` → 403) y no se pudo confirmar SSR vs SPA; se adopta el dataset oficial de LMArena en HuggingFace (JSON sobre HTTPS, verificado idéntico a la web) con scraping por agente como respaldo.
- [2026-07-19] plan — trampa detectada y documentada como regla de contrato: la config `text` NO es la que muestra el sitio (fable rank 3/1493 vs. rank 1/1507 en `text_style_control`); elegir mal produce un ranking incorrecto sin error visible.
- [2026-07-19] plan — dos modelos del inventario (`codex/gpt-5.6-terra`, `kimi/kimi-for-coding`) no existen en el leaderboard; refuerza el invariante de no discriminación (Constitución IV).
- [2026-07-19] checklist — 40 ítems de calidad de requisitos; 35/40 en la primera pasada. Se corrigieron 4 huecos en el spec (FR-019a votos mínimos, FR-020 preservar datos declarados ante versión desconocida, FR-020a directorio no escribible, SC-001 medible con mapeos confirmados) → 39/40.
- [2026-07-19] tasks — 41 tareas etiquetadas con el playbook `assign.md`. `codex` quedó con cero tareas pese a estar instalado y con cuota: justificado en Asignaciones (no encabeza ningún nivel del ranking actual; sigue como fallback).
- [2026-07-19] analyze — 0 hallazgos CRITICAL. 1 HIGH corregido (FR-004 no tenía tarea que persistiera los mapeos confirmados → nueva T012) y 2 MEDIUM (votos_minimos propagado a data-model y contrato C6; aviso de discrepancia sumado a T019). Queda abierto G2: SC-004 acota 30 s totales pero el timeout de 25 s es por petición y se hacen ~5.
- [2026-07-19] clarify — 5 preguntas respondidas e integradas. Decisión de alcance ampliada por el usuario: el almacén de la máquina guarda también plan/suscripción por CLI (no solo la clasificación), para no re-declararlo en cada proyecto.

- [2026-07-19] implement — **hallazgo de infraestructura**: `invoke_secondary.py` corre el comando con `shell=True` en Windows; `cmd.exe` interpreta `|`, `<`, `>` como operadores de pipe/redirección **incluso dentro de comillas**, rompiendo cualquier prompt de tarea que los contenga literalmente (p. ej. `"A" | "B"` o `--flag <archivo>`). T005 falló 2 veces (`indisponible`, "El sistema no puede encontrar el archivo especificado") hasta identificar la causa. Mitigado por ahora evitando esos caracteres al redactar los prompts de despacho; el script en sí no se tocó (fuera del alcance de esta feature) — queda anotado para `revisor-despachos`/`especialista-powershell`.

- [2026-07-19] implement — **hallazgo arquitectónico corregido durante la verificación de T015**: `merge_preserving_user_edits`/`merge_node` (preexistente, feature 001) trataba `clis.<cli>.modelos[]` como un bloque atómico — comparaba la lista completa como JSON canónico. Como el `models.json` real del proyecto casi siempre difiere del último `models.scan.json` propuesto (historia, catálogo, ediciones), el merge descartaba **toda** la lista enriquecida y volvía a la versión sin clasificar, aunque los campos nuevos (`nivel_origen`, `clasificacion`) fueran estrictamente aditivos. Esto rompía FR-005/SC-001 en cualquier proyecto con historia real, no solo en el caso de prueba. Corregido extendiendo `merge_node` para reconocer listas de dicts con `id` estable (como `modelos[]`) y mergear **por elemento y por campo**, en vez de lista completa contra lista completa — la corrección manual de un campo (ej. `capacidad`) sigue prevaleciendo, pero ya no arrastra consigo la pérdida de otros campos del mismo modelo o de otros modelos. Verificado con el ciclo completo `scan_models.py` real: `claude/fable` conserva `nivel_origen: "medido"` y `clasificacion.rating = 1507.48` tras el merge; una edición manual de `capacidad` sigue ganando; listas simples (`asignacion.alta`) y modelos agregados a mano quedan con el comportamiento atómico de siempre. 58/58 tests pasan, incluido `test_merge_campos_nuevos.py`.

- [2026-07-19] implement — **hallazgo corregido antes de T019**: `classify_inventory()` calculaba los `ambiguos` (ref + candidatos) pero solo los imprimía como texto en stderr, sin exponerlos de forma estructurada. La skill no habría podido presentarle al usuario **qué candidatos** elegir para cada modelo ambiguo. Corregido: `classify_inventory()` ahora devuelve `(clis, ambiguos)`; `scan_models()` propaga `ambiguos` en su resultado; `main() --json` lo agrega como clave `"AMBIGUOS"` (ausente si no hay ninguno, aditivo). Verificado end-to-end: los 3 casos reales (`claude/opus`, `claude/sonnet`, `codex/gpt-5.5`) salen con su lista completa de candidatos. 75/75 tests.

- [2026-07-21] implement — **segunda regla operativa de despacho**: prompts que superan ~8000 caracteres fallan con "La línea de comandos es demasiado larga" (límite de `cmd.exe` en Windows, ~8191 caracteres para el comando completo, no solo el argumento). T028 (9098 caracteres) falló así; se dividió en T028a (Partes A+B, lógica core, por `claude/fable`) y Parte C (cablear `asignacion_por_fase` en `scan_models()`, 3 líneas, hecha directamente por el principal — no justificaba un tercer ciclo de despacho).
- [2026-07-21] implement — T029 marcada `[X]` **sin despachar**: su objetivo quedó cumplido y verificado como Parte C de T028; despacharla habría sido trabajo duplicado.
- [2026-07-21] implement — T033: corregido un detalle de contrato — `motivo` quedaba como `""` (string vacío) en los caminos exitosos (`actualizada`/`reutilizada`) en vez de `null` como especifica el contrato. `build_summary` ahora normaliza `motivo` falsy a `null`. Verificado además en vivo: una falla transitoria real de red durante la verificación fue absorbida correctamente por la degradación (cayó a `reutilizada`/`global` en vez de romperse) — demostración empírica de FR-018 funcionando.
- [2026-07-21] implement — T034: corregido un caso borde — una respuesta con 0 filas útiles (tras el filtro de campos obligatorios/votos mínimos) se trataba como éxito con datos vacíos (`fuente_ganadora: "actual"` sin ninguna entrada) en vez de degradar al caché. Ahora una lista vacía se normaliza a "sin datos" antes de resolver la fuente ganadora. Verificado con 3 casos: archivo de agente válido (`via: "agente"`), archivo corrupto (degrada, exit 0) y archivo con 0 filas útiles (ya no declara éxito falso).

- [2026-07-19] implement — T028 completada en dos partes: A+B (extender `classify_inventory` con fortalezas, `build_asignacion_por_fase`) por `claude/fable`; C (cablear `asignacion_por_fase` en `scan_models()`) por el principal directamente — 3 líneas, bajo riesgo, no justificaba un tercer ciclo de despacho. Verificado end-to-end contra el inventario real: 7 fases, 0 modelos excluidos, `asignacion` intacta, dos corridas consecutivas producen `models.json` byte a byte idéntico (SC-006). Efecto colateral benigno observado: `detect_models()` (feature 006) descubrió un modelo nuevo (`claude-sonnet-4-6`) en la configuración local real de Claude Code durante estas corridas — composición correcta entre features, no un defecto de T028.

- [2026-07-19] implement — T029 marcada `[X]` **sin despachar**: su objetivo ("escribir `asignacion_por_fase` como sección hermana de `asignacion`, sin alterar su forma/semántica") quedó cumplido y verificado como Parte C de T028. Despacharla habría sido trabajo duplicado.

## Métricas

**Cierre**: 2026-07-21 | **41/41 tareas completas** | **96/96 tests pasan**

### Tareas por modelo

| Modelo | Tareas | % del total |
|---|---|---|
| `kimi/kimi-for-coding` | 24 | 59% |
| `claude/fable` | 8 | 20% |
| `claude/haiku` | 9 | 22% |
| Principal (`claude/opus`, sin despacho) | 4 (T029, T038, T040, T041) | — |

**% de tareas ejecutadas por modelos económicos** (costo < 3, es decir todo salvo
`claude/fable`): 33/41 despachadas = **89%** de lo despachado; sobre el total de 41
(incluyendo lo hecho por el principal) = 33/41 = **80%**.

### Consumo del modelo caro vs. baseline (SC-004)

`claude/fable` (costo 3, el único candidato `alta` que ejecutó tareas) resolvió 8 de 41
tareas — las de mayor riesgo real: el pipeline fetch→normalize→match (T009-T011), el
punto de integración con `scan_models.py` y el fix arquitectónico de `merge_node`
(T015), la resolución de precedencia FR-012 (T021), y `build_asignacion_por_fase` (T028).
Baseline de referencia: si las 41 tareas hubieran ido todas al modelo caro (escenario sin
asignador), el consumo habría sido 41/41 = 100%. El reparto real dejó el modelo caro en
**19,5%** del total (8/41) — una reducción del **~80%** de uso del modelo más costoso
frente al baseline, cumpliendo el Principio III (el más barato que alcance).

### Hallazgos de infraestructura corregidos durante la orquestación

| # | Hallazgo | Impacto si no se corregía |
|---|---|---|
| 1 | `invoke_secondary.py` + `cmd.exe`: `|`/`<`/`>` sueltos rompen el despacho | Cualquier prompt con esos caracteres fallaba con error críptico |
| 2 | Prompts > ~8000 caracteres exceden el límite de línea de comandos de Windows | Tareas complejas con contexto extenso fallaban sin explicación clara |
| 3 | `merge_node` trataba `modelos[]` como bloque atómico | La clasificación completa se perdía en cualquier proyecto con historia real (rompía FR-005/SC-001) |
| 4 | `ambiguos` solo se imprimía como texto, no estructurado | La skill no podía ofrecerle candidatos reales al usuario |
| 5 | `motivo` quedaba `""` en vez de `null` en éxito | Discrepancia menor con el contrato |
| 6 | Lista vacía de categoría tratada como éxito con 0 datos | Podía declarar `"actualizada"` sin ninguna entrada real |

Los hallazgos 3 y 4 eran **bloqueantes para el objetivo central de la feature**; los
demás eran de robustez/infraestructura. Todos corregidos y verificados antes de marcar
la tarea correspondiente `[X]`.

### Logs

Cada despacho dejó su log en `specs/007-arena-model-ranking/orchestration-logs/`
(`T0XX.intentoN.out.log` / `.err.log`).
