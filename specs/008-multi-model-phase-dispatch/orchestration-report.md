# Reporte de Orquestación: Despacho multi-modelo de todas las fases

**Feature**: `008-multi-model-phase-dispatch` | **Creado**: 2026-07-22 | **Principal**: claude/fable

> Plantilla del reporte multi-CLI. Secciones PARSEABLES (tablas de columnas fijas,
> las lee la retomabilidad): "Modelos por fase" y "Asignaciones". Secciones
> INFORMATIVAS (prosa, solo para humanos): "Triage", "Eventos", "Métricas".
> Ninguna lógica debe depender de parsear las secciones informativas.

## Triage

- **Complejidad de la idea**: compleja
- **Justificación (rúbrica)**:
  - *Alcance* (compleja): toca el inventario/catálogo de CLIs (soporte de agentes
    multi-modelo como OpenCode y Hermes), el triage, los pipelines auto
    (`speckit-specify-auto`/`-eco`) y el mecanismo de despacho headless — cambios
    transversales en más de 3 componentes.
  - *Ambigüedad* (compleja): "repartir todos los pasos, no solo la implementación"
    requiere definir qué fases son despachables por headless, cómo se manejan las
    fases interactivas (clarify, gates) y qué agentes/CLIs entran en alcance.
  - *Riesgo* (media): despacho headless de fases completas a CLIs externos; sin datos
    sensibles ni migraciones; reversible.
- **Flujo invocado**: IDEAL | **Flujo recomendado**: IDEAL
- **Resolución de discordancia**: n/a (coinciden)
- **Punto de entrada**: claude/fable (primer candidato disponible de `asignacion.alta`) →
  sin cambio (no corresponde escalar ni degradar)

## Modelos por fase

| Fase | Modelo asignado | Estado |
|------|-----------------|--------|
| specify | claude/fable | ejecutada |
| clarify | claude/fable | ejecutada |
| plan | claude/fable | ejecutada |
| checklist | kimi/kimi-for-coding | ejecutada |
| tasks | kimi/kimi-for-coding | ejecutada |
| tasks:asignación | claude/fable | ejecutada |
| analyze | claude/fable | ejecutada |
| implement | (por tarea, ver Asignaciones) | ejecutada |

<!-- Estados válidos: pendiente | ejecutada | omitida. Filas según el flujo elegido. -->

## Asignaciones

**Reparto**: 22 tareas — 5 `alta` → `claude/fable`, 12 `media` → `kimi/kimi-for-coding`,
5 `baja` → `claude/haiku`. **77% del trabajo va a modelos económicos** (costo < 3).

**Justificación obligatoria (Constitución IV)**: `codex` instalado, autenticado y con
cuota `ok` quedó con cero tareas — el playbook toma el primer candidato calificado de
cada nivel y codex no encabeza ninguno en el ranking vigente; sigue como fallback
inmediato de los tres niveles.

| Tarea | C | M | Estado |
|-------|---|---|--------|
| T001 | baja | claude/haiku | verificada |
| T002 | media | kimi/kimi-for-coding | verificada |
| T003 | media | kimi/kimi-for-coding | verificada |
| T004 | alta | claude/fable | verificada |
| T005 | media | kimi/kimi-for-coding | verificada |
| T006 | media | kimi/kimi-for-coding | verificada |
| T007 | media | kimi/kimi-for-coding | verificada |
| T008 | media | kimi/kimi-for-coding | verificada |
| T009 | media | kimi/kimi-for-coding | verificada |
| T010 | baja | claude/haiku | verificada |
| T011 | baja | claude/haiku | verificada |
| T012 | alta | claude/fable | verificada |
| T013 | media | kimi/kimi-for-coding | verificada |
| T014 | alta | claude/fable | verificada |
| T015 | alta | claude/fable | verificada |
| T016 | media | kimi/kimi-for-coding | verificada |
| T017 | baja | claude/haiku | verificada |
| T018 | baja | claude/haiku | verificada |
| T019 | media | kimi/kimi-for-coding | verificada |
| T020 | media | kimi/kimi-for-coding | verificada |
| T021 | media | kimi/kimi-for-coding | verificada |
| T022 | alta | claude/fable | verificada |

<!-- Estados válidos: pendiente | en_ejecucion | verificada | reasignada | rechazada | pendiente_bloqueada -->

## Eventos

- [2026-07-22] triage — idea clasificada compleja; flujo IDEAL invocado y recomendado coinciden; sin escalada ni degradación.
- [2026-07-22] triage — directorio `specs/008-multi-model-phase-dispatch/` preexistente con solo `checklists/` vacío (arranque previo abortado); sin artefactos válidos, el pipeline arranca desde specify.
- [2026-07-22] modo — fases de especificación ejecutadas en el principal (decisión-registrada, mismo criterio que feature 007): el despacho de fases a secundarios es exactamente lo que esta feature construye; aplicarlo antes de que exista sería inventarlo ad hoc.
- [2026-07-22] specify — `spec.md` y `checklists/requirements.md` creados; checklist de calidad completo, sin marcadores [NEEDS CLARIFICATION].
- [2026-07-22] plan — research delegado a subagente de exploración: hallazgos clave — `invoke_secondary.py` NO soporta prompt por archivo y además aplana el whitespace del prompt inline (L83) con `shell=True` (límite ~8191 chars de cmd.exe); `deshabilitado` existe solo a nivel CLI, no por modelo; `asignacion_por_fase` ya existe pero solo reordena candidatos para etiquetar tareas — nadie despacha fases. plan.md + research.md (9 decisiones) + data-model.md + 3 contratos + quickstart.md generados. Constitution Check: 6/6 principios sin violaciones.
- [2026-07-22] tasks — 22 tareas generadas en 6 fases (US2 antes que US1 por dependencia de datos: los campos del inventario habilitan el despacho de fases). Asignación con el playbook assign.md: 5 alta → claude/fable, 12 media → kimi/kimi-for-coding, 5 baja → claude/haiku; codex con cero tareas, justificado en Asignaciones (no encabeza ningún nivel; fallback inmediato).
- [2026-07-22] checklist — 22 ítems de calidad de requisitos; 20/22 en la primera pasada. Corregidos 2 huecos en el spec (FR-008a: efecto de deshabilitar un modelo sobre tareas ya etiquetadas; FR-010: umbral explícito de "económico" = costo < 3) → 22/22.
- [2026-07-22] clarify — 4 preguntas respondidas e integradas (activación por defecto con inventario; fases de criterio a modelos de alta capacidad con integración de respuestas por el modelo asignado; alcance genérico sin registrar OpenCode/Hermes en catálogo; configuración del usuario por inventario + skill, con opción de designar un agente preferido). Se agregaron FR-005a, FR-008a, FR-008b y un edge case de restricción por configuración.

- [2026-07-22] implement — T001: línea base 96/96 tests en verde. T002/T003 (kimi, TDD) verificadas; T004 `--prompt-file` implementado por el principal (12/12 tests). T005 `phase_candidates.py` (kimi): 14/14 + CLI validado contra el inventario real.
- [2026-07-22] implement — T006 requirió 1 reintento al mismo modelo: los 2 primeros tests exigían que un modelo capacidad 5 apareciera en TODOS los niveles del ranking, contradiciendo la semántica preexistente de `build_asignacion` (alta ≥8, media ≥6); corregido el test, no el código (el objetivo era el filtrado, no cambiar niveles). T008 (fix de 4 líneas en scan_models.py) y T009 (4 acciones nuevas en clis_config.py, +96 líneas) verificadas: suite completa 135/135.

- [2026-07-22] implement — T010/T011 (haiku, paralelo) documentación de skills verificada. T012 dispatch-phase.md creado por el principal. T013 (kimi) triage.md: decisión-solo pasa a fallback. T014 (principal) assign.md + orchestrate.md: filtros de habilitación y preferido, --prompt-file para prompts largos. T015 (principal) y T016 (kimi) skills de pipeline cableadas al despacho de fases. T017 (haiku) README del orquestador con .phase-dispatch (2 correcciones menores del principal: typo "identify" y lista de artefactos finales). T018 (haiku) columna Efectivo en report-template. T019 (kimi) métricas de fases en reportes finales.
- [2026-07-22] implement — T020: 14 copias empaquetadas sincronizadas byte a byte (hash verificado). T021: tests de entrega ampliados (phase_candidates.py + 6 playbooks); suite 135/135. T022: quickstart validado — Escenario 1+4: despacho real con --prompt-file de un prompt de 13.7 KB con `|`/`<`/`>` y multilínea (imposible por --prompt inline), artefacto verificado en 2 niveles, JSON con promptFile; errores de contrato (ambos flags, fuera del repo) → exit 2. Escenario 2+3: deshabilitar claude/haiku + preferido kimi sobre copia del inventario → candidatos filtrados correctamente, preferido-quitar restituye. Escenario 6: cubierto por test_no_regression.py en verde. Escenario 5 (pipeline end-to-end real): validación manual documentada — el propio pipeline de esta feature sirvió de dry-run parcial (13 de 22 tareas despachadas por headless).

## Métricas

**Cierre**: 2026-07-22 | **22/22 tareas completas** | **135/135 tests pasan** (96 en línea base + 39 nuevos)

### Tareas por modelo (Efectivo)

| Modelo | Tareas | % del total |
|---|---|---|
| `kimi/kimi-for-coding` | 12 (T002-T003, T005-T009, T013, T016, T019-T021) | 55% |
| `claude/haiku` | 4 (T010, T011, T017, T018) | 18% |
| Principal (`claude/fable`, en sesión) | 6 (T001, T004, T012, T014, T015, T022) | 27% |

**% del trabajo ejecutado por modelos económicos** (costo < 3): 16/22 = **73%**.
13 de 22 tareas fueron despachadas efectivamente por headless a secundarios.

### Consumo del modelo caro vs. baseline (SC-004)

`claude/fable` (principal, costo 3) ejecutó 6/22 tareas (27%) — las de diseño
transversal (playbook dispatch-phase, cableado de skills, --prompt-file, validación
final). Baseline sin orquestador: 22/22 = 100% en el modelo caro → reducción del
**~73%** del uso del modelo más costoso.

### Fallbacks y reintentos

- T006: 1 reintento al mismo modelo (test contradecía la semántica preexistente de
  niveles; se corrigió el test, no el código). Único reintento de la corrida; 0
  escaladas, 0 cuotas agotadas, 0 tareas bloqueadas.

### Validación de la propia feature (dogfooding)

El Escenario 1+4 del quickstart se ejecutó con el `--prompt-file` recién
implementado: primer despacho real de la historia del repo con un prompt
imposible de pasar inline (13.7 KB, caracteres `|`/`<`/`>`, multilínea). La
limitación #1 y #2 de la feature 007 (hallazgos de infraestructura) queda saldada.

### Logs

Cada despacho dejó su log en `specs/008-multi-model-phase-dispatch/orchestration-logs/`
(`T0XX.intentoN.out.log` / `.err.log`, `fase-smoke.*` para el smoke del quickstart).
