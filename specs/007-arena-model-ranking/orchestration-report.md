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
| implement | (por tarea, ver Asignaciones) | pendiente |

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
| T001 | baja | claude/haiku | pendiente |
| T002 | media | kimi/kimi-for-coding | pendiente |
| T003 | media | kimi/kimi-for-coding | pendiente |
| T004 | baja | claude/haiku | pendiente |
| T005 | media | kimi/kimi-for-coding | pendiente |
| T006 | media | kimi/kimi-for-coding | pendiente |
| T007 | alta | claude/fable | pendiente |
| T008 | baja | claude/haiku | pendiente |
| T009 | alta | claude/fable | pendiente |
| T010 | alta | claude/fable | pendiente |
| T011 | alta | claude/fable | pendiente |
| T012 | media | kimi/kimi-for-coding | pendiente |
| T013 | baja | claude/haiku | pendiente |
| T014 | media | kimi/kimi-for-coding | pendiente |
| T015 | alta | claude/fable | pendiente |
| T016 | media | kimi/kimi-for-coding | pendiente |
| T017 | media | kimi/kimi-for-coding | pendiente |
| T018 | media | kimi/kimi-for-coding | pendiente |
| T019 | media | kimi/kimi-for-coding | pendiente |
| T020 | media | kimi/kimi-for-coding | pendiente |
| T021 | alta | claude/fable | pendiente |
| T022 | media | kimi/kimi-for-coding | pendiente |
| T023 | media | kimi/kimi-for-coding | pendiente |
| T024 | baja | claude/haiku | pendiente |
| T025 | media | kimi/kimi-for-coding | pendiente |
| T026 | media | kimi/kimi-for-coding | pendiente |
| T027 | media | kimi/kimi-for-coding | pendiente |
| T028 | alta | claude/fable | pendiente |
| T029 | baja | claude/haiku | pendiente |
| T030 | media | kimi/kimi-for-coding | pendiente |
| T031 | media | kimi/kimi-for-coding | pendiente |
| T032 | media | kimi/kimi-for-coding | pendiente |
| T033 | media | kimi/kimi-for-coding | pendiente |
| T034 | media | kimi/kimi-for-coding | pendiente |
| T035 | media | kimi/kimi-for-coding | pendiente |
| T036 | media | kimi/kimi-for-coding | pendiente |
| T037 | baja | claude/haiku | pendiente |
| T038 | baja | claude/haiku | pendiente |
| T039 | media | kimi/kimi-for-coding | pendiente |
| T040 | alta | claude/fable | pendiente |
| T041 | baja | claude/haiku | pendiente |

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

## Métricas

<!-- Al cierre de la orquestación. -->
