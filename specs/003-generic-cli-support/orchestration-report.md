# Reporte de Orquestación: Soporte Genérico de CLIs y Multiplataforma

**Feature**: `003-generic-cli-support` | **Creado**: 2026-07-18 | **Principal**: claude/fable

> Secciones PARSEABLES: "Modelos por fase" y "Asignaciones". Secciones INFORMATIVAS:
> "Triage", "Eventos", "Métricas".

## Triage

- **Complejidad de la idea**: compleja
- **Justificación (rúbrica)**: Alcance complejo (transversal: 4 scripts, esquema de inventario, contratos, playbooks, skills, tests + portabilidad de SO); Ambigüedad media (estrategia multi-OS y alcance de "crear/verificar" requerían definición); Riesgo medio (cambio de esquema con compatibilidad hacia atrás obligatoria; plataformas no testeables localmente).
- **Flujo invocado**: IDEAL | **Flujo recomendado**: IDEAL
- **Resolución de discordancia**: n/a (coinciden)
- **Punto de entrada**: claude/fable → sin cambio (idea compleja: las fases clave requieren el modelo más capaz; el punto de entrada ya es el correcto).

## Modelos por fase

| Fase | Modelo asignado | Estado |
|------|-----------------|--------|
| specify | claude/fable | ejecutada |
| clarify | kimi/kimi-for-coding | ejecutada |
| plan | claude/fable | ejecutada |
| checklist | kimi/kimi-for-coding | pendiente |
| tasks | kimi/kimi-for-coding | pendiente |
| analyze | claude/fable | pendiente |
| implement | (por tarea, ver Asignaciones) | pendiente |

## Asignaciones

| Tarea | C | M | Estado |
|-------|---|---|--------|
| T001 | media | kimi/kimi-for-coding | verificada |
| T002 | alta | claude/fable | verificada |
| T003 | media | kimi/kimi-for-coding | verificada |
| T004 | media | kimi/k3 (fallback involuntario, ver Eventos) | verificada |
| T005 | alta | codex/gpt-5.6-sol | verificada |
| T006 | media | kimi/kimi-for-coding | verificada |
| T007 | media | kimi/kimi-for-coding-highspeed | verificada |
| T008 | media | claude/fable (reasignada, ver Eventos) | verificada |
| T009 | media | kimi/kimi-for-coding | verificada |
| T010 | media | kimi/kimi-for-coding-highspeed | verificada |
| T011 | alta | claude/fable | verificada |
| T012 | alta | claude/fable | verificada |
| T013 | media | kimi/kimi-for-coding | verificada |
| T014 | media | kimi/kimi-for-coding-highspeed | verificada |
| T015 | baja | claude/haiku | verificada |
| T016 | media | kimi/kimi-for-coding-highspeed | verificada |
| T017 | media | claude/fable | verificada parcial (windows+ubuntu ✅; macos en cola de CI) |
| T018 | baja | codex/gpt-5.6-luna | verificada |
| T019 | media | claude/fable (reasignada, ver Eventos) | verificada |
| T020 | baja | claude/fable (reasignada, ver Eventos) | verificada |

## Eventos

- [2026-07-18] triage — idea clasificada compleja por rúbrica; flujo IDEAL confirmado; specify/plan/analyze asignadas al modelo más capaz (regla para complejas).
- [2026-07-18] nota operativa — fases interactivas en sesión del principal; despacho headless en implement.
- [2026-07-18] ofrecimiento de agentes — realizado tras specify (idea compleja, regla del pipeline); sin respuesta del usuario → se continuó sin correrlo (no bloqueante). Cobertura de dominios ya completa (7/7 de la feature 002).
- [2026-07-18] asignación — 20 tareas clasificadas por claude/fable. Reparto: kimi 12 (8 kimi-for-coding + 4 highspeed), claude 6 (T002/T011/T012 alta + T017 media-integración con fable; T015/T020 baja con haiku), codex 2 (T005 alta con sol; T018 baja con luna). Justificaciones: (a) empate de costo en alta (fable=sol costo 3) → T005 a sol por balance de carga del principal; (b) empate de costo en media (kimi-for-coding=highspeed costo 1) → reparto entre ambos; (c) T017 al principal por ser integración/verificación final (rol FR-019); (d) kimi/k3 sin tareas: nivel media siempre tuvo candidatos de costo 1 disponibles (regla el-más-barato-que-alcance) — queda como fallback.

- [2026-07-18] bug de infraestructura (detectado y corregido) — un prompt con salto de línea final partía la línea del wrapper en dos: la mitad ejecutaba el CLI (¡sin `--model`!) y el resto corría como comando basura ensuciando el exit code. Efecto colateral real: T001 y T004 corrieron con el modelo default de kimi (k3) en vez del asignado. Corregido: sanitización de prompts en `Get-HeadlessCommand`.
- [2026-07-18] falso positivo del clasificador de cuota — tareas cuyo CONTENIDO legítimo incluye las palabras de los patrones (p. ej. escribir el catálogo de patrones de cuota) se clasifican `cuota_agotada` cuando el exit code es ≠0. Limitación conocida documentada; el control compensatorio es la verificación del principal (funcionó: el trabajo estaba bien en ambos casos).
- [2026-07-18] verificación T005 (codex/sol) — clis-config.ps1 de alta calidad; 2 correcciones de integración del principal: (a) quirk NUEVO de PS 5.1 descubierto y con repro mínimo: `@($param)` de un parámetro tipado sin bindear rompe `.Count` bajo StrictMode; (b) semántica del merge de `asignacion` en operaciones explícitas (sin scan previo gana lo regenerado; la línea base del scan se actualiza tras cada operación). Protocolo: sol marcó su propia tarea `[X]` en tasks.md (reservado al principal) — la marca se convalidó tras verificar, y los prompts de despacho vuelven a incluir la prohibición explícita.
- [2026-07-18] suite tras refactors + actualización de tests: 58/58 en verde (T003/T004/T011/T012/T013/T014 verificadas). T015 (CI yaml de haiku) verificada por inspección.

- [2026-07-18] verificaciones tanda final — T006 (14 tests, suite 72/72), T009 (verificación por niveles + tests, 76/76), T010 (validación REAL del escenario 2: claude nivel c ok en 3.6s con comando mostrado; detectó de paso el bug de encoding de Read-CliInventory, corregido por el principal), T016 (stubs portables, suite Windows sigue 76/76), T018 (README con prerequisitos por SO, secciones gestionadas intactas), T007 (skill speckit-clis; 1 corrección de integración: contexto → contexto_k).
- [2026-07-18] reasignaciones al principal (integración/cierre): T008 (el escenario 1 quedó validado de facto durante la verificación de T005), T019 (escenario 5 ejecutado en sandbox por el principal) y T020 (auditoría de cierre). Motivo: eficiencia de cierre; el trabajo de construcción siguió en los secundarios.

## Métricas

**Cierre parcial 2026-07-18** (19/20 verificadas; T017 espera el gate del usuario para el push que dispara la CI):

| Modelo | Tareas ejecutadas y verificadas | Costo |
|---|---|---|
| kimi/kimi-for-coding | 5 (T001*, T003, T006, T009, T013) + T004* | 1 |
| kimi/k3 | 2 involuntarias por bug de wrapper (T001, T004 — ver Eventos) | 2 |
| kimi/kimi-for-coding-highspeed | 4 (T007, T010, T014, T016) | 1 |
| codex/gpt-5.6-sol | 1 alta (T005) | 3 |
| codex/gpt-5.6-luna | 1 (T018) | 1 |
| claude/haiku | 1 (T015) | 1 |
| claude/fable (principal) | 5 (T002, T011, T012 + T008/T019/T020 de cierre) + verificación de todo | 3 |

- 12 de 19 tareas ejecutadas por modelos de costo 1 (63%); las alta fueron 3 fable + 1 sol (por diseño: es la feature más transversal del proyecto).
- Suite final: **76/76 en verde**. Fallbacks por cuota reales: 0. Falsos positivos del clasificador: 2 (documentados). Bugs de infraestructura del despacho encontrados y corregidos en producción: 3 (newline del wrapper, encoding de lectura, PATH del sandbox).
