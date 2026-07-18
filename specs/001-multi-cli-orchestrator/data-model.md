# Data Model: Orquestador Multi-CLI para Spec Kit

**Feature**: 001-multi-cli-orchestrator | **Date**: 2026-07-18

Todas las entidades son archivos en el repo (no hay base de datos).

## 1. Inventario de modelos — `.specify/models.json`

Fuente de verdad para triage, asignación y fallback. Generado por `/speckit-models`,
corregible a mano; el sistema solo escribe automáticamente los campos de cuota
(FR-018). Esquema detallado en [contracts/models-schema.md](contracts/models-schema.md).

| Campo | Tipo | Reglas |
|---|---|---|
| `clis.<cli>` | objeto | `<cli>` ∈ {`claude`, `codex`, `kimi`} (v1) |
| `clis.<cli>.instalado` | bool | detectado por sondeo |
| `clis.<cli>.autenticado` | bool | detectado por invocación de prueba |
| `clis.<cli>.version` | string | detectada; `"desconocido"` si falla |
| `clis.<cli>.headless` | string | plantilla de comando con placeholder `{prompt}` y `{modelo}`; propuesta por scan, corregible |
| `clis.<cli>.plan` | string | declarado por el usuario; `"desconocido"` si no declara |
| `clis.<cli>.cuota` | `"ok"` \| `"agotada"` \| `"desconocido"` | ÚNICO campo que el sistema escribe automáticamente |
| `clis.<cli>.cuota_desde` | string ISO-8601 | presente solo si `cuota = "agotada"` |
| `clis.<cli>.cuota_reset` | string ISO-8601 \| `"desconocido"` | estimado según ventana del plan declarado |
| `clis.<cli>.modelos[]` | array | al menos 1 si instalado |
| `modelos[].id` | string | único dentro del CLI; referencia como `cli/id` |
| `modelos[].capacidad` | entero 1–10 | sembrado por scan, corregible; corrección manual prevalece |
| `modelos[].costo` | entero 1–3 | ídem |
| `modelos[].contexto_k` | entero \| `"desconocido"` | ventana en miles de tokens |
| `asignacion.alta` | array de `"cli/modelo"` | lista ordenada, primer elemento = preferido |
| `asignacion.media` | array | ídem |
| `asignacion.baja` | array | ídem |

**Reglas de validación**:
- Toda referencia `cli/modelo` en `asignacion` debe existir en `clis.<cli>.modelos`.
- Ningún CLI con `instalado: true` y `autenticado: true` puede quedar ausente de
  TODAS las listas de `asignacion` (Constitución IV).
- Re-ejecutar `/speckit-models` no pisa valores editados a mano sin confirmación
  explícita del usuario (FR-004).

**Transiciones de estado de `cuota`**:

```
ok/desconocido --(fallo clasificado cuota_agotada)--> agotada  [escribe cuota_desde, cuota_reset]
agotada --(now > cuota_reset)--> ok                            [al releer el inventario]
agotada --(reset manual del usuario)--> ok
```

## 2. Idea / Feature (triage)

Entidad transitoria evaluada por el playbook de triage; su resultado persiste en el
reporte de orquestación.

| Atributo | Valores | Efecto |
|---|---|---|
| `complejidad_idea` | `simple` \| `media` \| `compleja` | simple → flujo ECO; media/compleja → IDEAL |
| `modelos_por_fase` | mapa fase → `cli/modelo` | media: plan/analyze con modelo importante; compleja: specify/plan/analyze con modelo importante |
| `punto_entrada` | `cli/modelo` que recibió la idea | si inferior a lo requerido → escalar; si superior → degradar (FR-007) |
| `flujo_invocado` vs `flujo_recomendado` | ECO/IDEAL | discordancia → preguntar (sin `-bypass`) o cambiar e informar (con `-bypass`) (FR-008) |

## 3. Tarea etiquetada — línea de `tasks.md`

Extiende el formato oficial de spec-kit SIN modificarlo (FR-015). Gramática formal en
[contracts/task-labels.md](contracts/task-labels.md).

```
- [ ] T012 [P] [US1] [C:baja] [M:kimi/k2] Crear modelo User en src/models/user.py
      └──┬──┘ └┬┘ └─┬─┘ └──┬───┘ └───┬────┘ └────────────┬─────────────────────┘
       oficial  of.  of.  NUEVA    NUEVA               oficial (descripción + ruta)
```

| Etiqueta | Valores | Reglas |
|---|---|---|
| `[C:...]` | `baja` \| `media` \| `alta` | exactamente una por tarea tras la asignación |
| `[M:...]` | `cli/modelo` existente en `models.json` | exactamente una por tarea; editable a mano; una referencia inválida se detecta antes de despachar (edge case) |

**Ciclo de vida de una tarea en orquestación**:

```
pendiente --(despacho headless)--> en_ejecucion
en_ejecucion --(éxito + verificación FR-019 ok)--> verificada  [se marca [X]]
en_ejecucion --(fallo cuota)--> reasignada (siguiente candidato; evento en reporte)
en_ejecucion --(fallo otro, 1er intento)--> reintento (mismo modelo)
reintento --(2do fallo)--> reasignada (CLI indisponible)
en_ejecucion --(verificación falla)--> rechazada (reintento o escalada; NO se marca [X])
reasignada --(sin candidatos restantes)--> pendiente_bloqueada (pausa + reporte)
```

## 4. Reporte de orquestación — `specs/<feature>/orchestration-report.md`

Creado en triage, actualizado por fase (Clarificación S5). Secciones fijas (plantilla
en `.specify/orchestrator/report-template.md`):

| Sección | Contenido | Quién escribe |
|---|---|---|
| Triage | complejidad, flujo recomendado/usado, escalada/degradación del punto de entrada | fase triage |
| Modelos por fase | tabla fase → modelo → estado (pendiente/ejecutada) | triage + cada fase |
| Asignaciones | tabla T### → [C:] → [M:] → estado final | asignador + orquestador |
| Eventos | fallbacks, reintentos, cuotas agotadas, cambios de flujo (timestamp + causa) | cualquier fase |
| Métricas | tareas por modelo, % ejecutado por modelos económicos, estimación de ahorro (SC-004) | orquestador al cierre |

**Secciones parseables vs informativas**: "Asignaciones" y "Modelos por fase" usan
tablas Markdown de columnas fijas y son la fuente que la retomabilidad (FR-012) lee
junto a `tasks.md`; "Triage", "Eventos" y "Métricas" son informativas (prosa libre,
solo para humanos). Ninguna lógica debe depender de parsear las secciones informativas.

## 5. Puntero de feature — `.specify/feature.json`

Ya existe en spec-kit (lo escribe `/speckit-specify`); el orquestador solo lo lee para
ubicar el directorio de la feature. Sin cambios de esquema.
