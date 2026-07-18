---

description: "Task list for feature implementation"
---

# Tasks: Orquestador Multi-CLI para Spec Kit

**Input**: Design documents from `/specs/001-multi-cli-orchestrator/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: El plan define tests Pester para los scripts PowerShell (parte del diseño, no opcionales). La conducta de skills/playbooks se valida con los escenarios de quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Extensión de tooling sobre el repo spec-kit (sin `src/` de aplicación): skills en
`.claude/skills/`, playbooks portables en `.specify/orchestrator/`, scripts en
`.specify/scripts/powershell/`, tests Pester en `tests/powershell/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Estructura de directorios y actualización de plantilla pendiente

- [x] T001 Crear directorios `.specify/orchestrator/` y `tests/powershell/` con `.gitkeep` en cada uno
- [x] T002 [P] Documentar las etiquetas aditivas `[C:baja|media|alta]` y `[M:cli/modelo]` en la sección Format de `.specify/templates/tasks-template.md` (follow-up pendiente del sync de la constitución; sin alterar el formato oficial)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Artefactos compartidos que triage, asignador y orquestador consumen

**⚠️ CRITICAL**: Ninguna historia puede completarse sin estos artefactos

- [x] T003 Crear plantilla del reporte de orquestación en `.specify/orchestrator/report-template.md` con secciones fijas según data-model.md §4 (parseables: "Asignaciones" y "Modelos por fase" como tablas de columnas fijas; informativas: "Triage", "Eventos", "Métricas")
- [x] T004 [P] Crear guía de convenciones portables en `.specify/orchestrator/README.md` (qué puede asumir un playbook: leer/escribir archivos, ejecutar scripts PowerShell, invocar comandos; prohibido depender de features exclusivas de un CLI — Constitución II)

**Checkpoint**: Foundation ready — las historias pueden implementarse

---

## Phase 3: User Story 1 - Inventario de recursos disponibles (Priority: P1) 🎯 MVP

**Goal**: `/speckit-models` detecta CLIs/modelos, incorpora declaración del usuario y genera `.specify/models.json` con ranking corregible

**Independent Test**: en una máquina con al menos un CLI, ejecutar `/speckit-models` y validar `models.json` contra `contracts/models-schema.md`; editar un valor a mano, re-ejecutar y verificar que la edición sobrevive (quickstart escenario 1)

### Implementation for User Story 1

- [x] T005 [P] [US1] Implementar detección de CLIs (instalado vía `Get-Command`, versión, autenticación por invocación de prueba con timeout, plantilla headless propuesta según contracts/headless-adapters.md) en `.specify/scripts/powershell/scan-models.ps1`
- [x] T006 [US1] Agregar a `.specify/scripts/powershell/scan-models.ps1` la tabla de siembra de modelos (capacidad 1–10, costo 1–3, contexto_k según research.md R6) y la generación de listas `asignacion` ordenadas (capacidad suficiente → menor costo → disponibilidad), incluyendo a todos los CLIs instalados (Constitución IV)
- [x] T007 [US1] Implementar en `.specify/scripts/powershell/scan-models.ps1` la preservación de ediciones manuales: guardar propuesta previa en `.specify/models.scan.json`, comparar en re-ejecuciones y pedir confirmación antes de pisar valores editados (FR-004, invariante 4 del contrato); salida siempre UTF-8 sin BOM con indentación 2
- [x] T008 [P] [US1] Escribir tests Pester en `tests/powershell/scan-models.Tests.ps1` (CLI ausente → `instalado:false` y fuera de `asignacion`; datos no detectables → `"desconocido"`, nunca inventados; edición manual sobrevive re-scan; salida valida contra el esquema)
- [x] T009 [US1] Crear skill `.claude/skills/speckit-models/SKILL.md` (correr el script, preguntar al usuario plan/cuotas/contexto no detectables, validar contra `contracts/models-schema.md`, mostrar resumen del ranking)
- [x] T010 [US1] Ejecutar y documentar el escenario 1 de `specs/001-multi-cli-orchestrator/quickstart.md` (inventario completo < 10 min, persistencia de ediciones)

**Checkpoint**: US1 funcional e independiente — existe inventario confiable

---

## Phase 4: User Story 2 - Triage de la idea y elección del flujo (Priority: P1)

**Goal**: antes de ejecutar fases, el sistema clasifica la idea con rúbrica, elige flujo ECO/IDEAL y modelos por fase, y se autoevalúa (escalar/degradar el punto de entrada)

**Independent Test**: con un `models.json` válido (puede ser de prueba), invocar el pipeline con una idea simple y una compleja; verificar clasificación, flujo recomendado y modelos por fase en el reporte, sin fases ejecutadas (quickstart escenario 2)

### Implementation for User Story 2

- [x] T011 [P] [US2] Escribir playbook de triage en `.specify/orchestrator/triage.md`: rúbrica observable (componentes tocados, claridad de criterios, riesgo — FR-005), mapeo complejidad→flujo→modelos por fase (tabla de la spec), autoevaluación del punto de entrada (escalar/degradar — FR-007), manejo de discordancia con/sin `-bypass` (FR-008), y escritura de la sección Triage del reporte usando `.specify/orchestrator/report-template.md`
- [x] T012 [US2] Integrar el triage como pre-fase en `.claude/skills/speckit-specify-auto/SKILL.md`: leer `.specify/models.json` (si falta o es inválido → ofrecer `/speckit-models`, nunca inventar), ejecutar el playbook con el primer candidato disponible de `asignacion.alta`, crear `specs/<feature>/orchestration-report.md`. NOTA (alcance por etapas): hasta que exista `invoke-secondary.ps1` (US5/T021), el triage opera en "modo decisión-solo" — registra los modelos por fase en el reporte y las fases corren en el principal; el despacho real de fases a otros CLIs se activa al integrar US5
- [ ] T013 [US2] Ejecutar y documentar el escenario 2 de `specs/001-multi-cli-orchestrator/quickstart.md` (idea simple sin/con `-bypass`, escalada y degradación registradas en el reporte)

**Checkpoint**: US1 + US2 — el sistema decide antes de gastar

---

## Phase 5: User Story 3 - Pipeline económico de una sola llamada (Priority: P2)

**Goal**: `/speckit-specify-auto-eco` ejecuta specify → plan → tasks → gate → implement con frenos solo ante dudas reales; ambos pipelines retomables

**Independent Test**: invocar el flujo ECO con una idea clara: encadena sin intervención hasta el gate; con `-bypass` llega a implement; interrumpir y reinvocar retoma desde la fase faltante (quickstart escenario 3)

### Implementation for User Story 3

- [x] T014 [US3] Crear skill `.claude/skills/speckit-specify-auto-eco/SKILL.md`: ciclo mínimo specify → plan → tasks → gate → implement, triage integrado como pre-fase (reutiliza `.specify/orchestrator/triage.md`), flags `-bypass` (salta solo el gate, nunca dudas reales — FR-011) y `--sin-implementar`
- [x] T015 [US3] Implementar retomabilidad en `.claude/skills/speckit-specify-auto-eco/SKILL.md` y `.claude/skills/speckit-specify-auto/SKILL.md`: detección de artefactos existentes por fase, artefactos incompletos/corruptos tratados como faltantes con oferta de regeneración (FR-012 + edge case), continuar sin rehacer completados
- [ ] T016 [US3] Ejecutar y documentar el escenario 3 de `specs/001-multi-cli-orchestrator/quickstart.md` (ECO con `-bypass` sin pausas, corte y retome desde tasks, `--sin-implementar` frena tras planificación)

**Checkpoint**: pipelines completos para ideas chicas y grandes

---

## Phase 6: User Story 4 - Clasificación y asignación de tareas (Priority: P2)

**Goal**: al final de la fase tasks, el modelo más capaz clasifica `[C:]` y asigna `[M:]` inline en `tasks.md` sin tocar el formato oficial

**Independent Test**: con un `tasks.md` generado y `models.json` válido, correr el asignador: cada tarea con exactamente una `[C:]` y una `[M:]` (regex del contrato), `[C:baja]` → modelo económico, los 3 CLIs reciben tareas, ediciones manuales respetadas (quickstart escenario 4)

### Implementation for User Story 4

- [x] T017 [P] [US4] Escribir playbook del asignador en `.specify/orchestrator/assign.md`: clasificación `[C:]` por alcance/contexto/dependencias/riesgo/tipo (FR-013), asignación `[M:]` = primer candidato del nivel con cuota y contexto suficiente (FR-014, reglas de `contracts/task-labels.md`), inserción de etiquetas tras las oficiales, idempotencia sobre etiquetas existentes salvo flag `-reasignar`, justificación en reporte si un CLI queda sin tareas, escritura de la sección Asignaciones del reporte. El playbook MUST ser invocable directamente (sin pipeline) sobre un `tasks.md` existente, para pruebas y para re-asignar tras una re-generación
- [x] T018 [US4] Integrar el asignador como paso post-tasks en `.claude/skills/speckit-specify-auto/SKILL.md` y `.claude/skills/speckit-specify-auto-eco/SKILL.md`, ejecutado por el primer candidato disponible de `asignacion.alta`, con advertencia de pérdida de etiquetas si se re-genera `tasks.md` (edge case)
- [ ] T019 [US4] Ejecutar y documentar el escenario 4 de `specs/001-multi-cli-orchestrator/quickstart.md` (etiquetas completas, formato oficial intacto validado con la regex, reparto entre los 3 CLIs, respeto de ediciones manuales)

**Checkpoint**: tasks.md etiquetado y listo para despacho

---

## Phase 7: User Story 5 - Orquestación de la implementación (Priority: P3)

**Goal**: el principal despacha cada tarea a su CLI asignado (paralelo con límite y serialización de conflictos), aplica fallback por cuota/indisponibilidad, verifica y marca `[X]`

**Independent Test**: con un `tasks.md` etiquetado y ≥2 CLIs, correr `/speckit-orchestrate`: cada tarea ejecutada por su CLI (o fallback), `[P]` en paralelo salvo conflicto de rutas, solo verificadas quedan `[X]`, fallback sin intervención ante cuota agotada (quickstart escenario 5)

### Implementation for User Story 5

- [x] T020 [P] [US5] Implementar `.specify/scripts/powershell/get-parallel-groups.ps1`: parseo de líneas de tarea con la regex de `contracts/task-labels.md`, extracción de rutas de la descripción, agrupación de `[P]` sin rutas compartidas, serialización de conflictos y de tareas sin rutas declaradas, límite de concurrencia configurable (default 4) (FR-017)
- [x] T021 [P] [US5] Implementar `.specify/scripts/powershell/invoke-secondary.ps1`: sustitución `{prompt}`/`{modelo}` en la plantilla headless de `models.json`, working dir = raíz del repo, timeout 15 min configurable, captura stdout/stderr a archivos por tarea bajo el directorio de la feature, clasificación de fallos (éxito / cuota_agotada por patrones del contrato / fallo_transitorio con 1 reintento / indisponible) (FR-016, FR-018, Clarificación S4)
- [x] T022 [P] [US5] Implementar `.specify/scripts/powershell/update-quota.ps1`: escritura acotada a `cuota`, `cuota_desde`, `cuota_reset` (plan desconocido → reset `"desconocido"`), preservando el resto del archivo byte a byte salvo esos campos, UTF-8 sin BOM (FR-018, invariantes 6–7 del contrato)
- [x] T023 [P] [US5] Escribir tests Pester en `tests/powershell/get-parallel-groups.Tests.ps1`, `tests/powershell/invoke-secondary.Tests.ps1` y `tests/powershell/update-quota.Tests.ps1` (regex sobre líneas válidas/sin etiquetas/con etiquetas desconocidas; serialización por conflicto y por falta de rutas; clasificación cuota vs transitorio vs indisponible con CLIs mockeados; update-quota no toca otros campos)
- [x] T024 [US5] Escribir playbook de orquestación en `.specify/orchestrator/orchestrate.md`: validación previa de etiquetas contra `models.json` (inválida → fallback del nivel o pedir corrección), despacho por grupos con los scripts, empaquetado del prompt de tarea según `contracts/headless-adapters.md`, verificación estándar con ciclo acotado (1 reintento con feedback + 1 escalada + bloqueo — FR-019), fallback y actualización de etiqueta `[M:]` en `tasks.md`, `[X]` solo verificadas, pausa ordenada (tareas en vuelo se esperan; cuota del principal agotada → persistir estado e indicar retome), secciones Eventos/Métricas del reporte
- [x] T025 [US5] Crear skill `.claude/skills/speckit-orchestrate/SKILL.md`: adaptador fino que lee `.specify/feature.json`, valida prerequisitos (`tasks.md` etiquetado, `models.json` válido) y ejecuta el playbook; retome = despachar solo tareas sin `[X]` reconstruyendo estado desde `tasks.md` + reporte (FR-012)
- [x] T026 [US5] Integrar la orquestación como fase implement de `.claude/skills/speckit-specify-auto/SKILL.md` y `.claude/skills/speckit-specify-auto-eco/SKILL.md` (gate previo respetando `-bypass`)
- [ ] T027 [US5] Ejecutar y documentar el escenario 5 de `specs/001-multi-cli-orchestrator/quickstart.md` (despacho por CLI asignado, paralelo/serialización visibles en el reporte, fallback con cuota simulada `"agotada"`, `models.json` actualizado con timestamps)

**Checkpoint**: circuito completo idea → implementación repartida

---

## Phase 8: User Story 6 - Instalación compatible con spec-kit (Priority: P4)

**Goal**: el repo se instala con el mismo gesto que spec-kit y los comandos originales no cambian

**Independent Test**: en un proyecto limpio, instalar/inicializar desde este repo; skills base intactas + skills nuevas presentes (quickstart escenario 6)

### Implementation for User Story 6

- [x] T028 [P] [US6] Actualizar `README.md`: estado real de los pasos 3–6, comandos nuevos (`/speckit-models`, `/speckit-specify-auto-eco`, `/speckit-orchestrate`), instrucciones de instalación desde este repo y nota de compatibilidad
- [x] T029 [US6] Verificar la instalación en un proyecto de prueba limpio según el escenario 6 de `specs/001-multi-cli-orchestrator/quickstart.md`: gesto de instalación equivalente al original, estructura `.specify/` estándar, skills base sin cambios de comportamiento, skills nuevas disponibles; documentar el resultado en el README si hay pasos adicionales
- [x] T033 [P] [US6] Crear los puntos de entrada nativos para Codex y Kimi como principal (FR-020): `.codex/prompts/speckit-orchestrate.md` (o entrada equivalente en `AGENTS.md`) y el equivalente de Kimi CLI, cada uno como adaptador fino que instruye leer y ejecutar los playbooks de `.specify/orchestrator/` (mismo contrato que la skill de Claude, sin lógica duplicada); validar la aceptación 5 del escenario 5 del quickstart desde al menos un CLI no-Claude

**Checkpoint**: distribuible

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: validación integral y medición del objetivo de ahorro

- [x] T030 [P] Ejecutar la suite completa `Invoke-Pester tests/powershell/` y corregir todo fallo en los scripts de `.specify/scripts/powershell/`
- [ ] T031 Ejecutar el escenario 7 de `specs/001-multi-cli-orchestrator/quickstart.md` (feature de juguete con y sin orquestador, medir SC-004 ≥ 50% de ahorro del modelo caro) y registrar las métricas en la sección Métricas del reporte de la corrida
- [x] T032 [P] Auditoría final de compatibilidad aditiva (Constitución I): revisar que ningún archivo base de spec-kit (`.specify/templates/`, skills base, scripts existentes) haya cambiado de comportamiento; corregir o documentar cualquier desvío en `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: tras Setup — BLOQUEA todas las historias
- **US1 (Phase 3)**: tras Foundational; no depende de otras historias
- **US2 (Phase 4)**: tras Foundational; usa `models.json` (US1) en producción, pero se prueba con inventario de prueba — independiente
- **US3 (Phase 5)**: tras Foundational; reutiliza el playbook de triage (T011) para T014
- **US4 (Phase 6)**: tras Foundational; independiente (consume `tasks.md` + `models.json` existentes)
- **US5 (Phase 7)**: tras Foundational; consume salidas de US4 en producción, pero se prueba con `tasks.md` etiquetado a mano — independiente
- **US6 (Phase 8)**: última historia — empaqueta lo anterior
- **Polish (Phase 9)**: tras las historias deseadas

### User Story Dependencies

- Orden de entrega recomendado: US1 → US2 → US3 → US4 → US5 → US6
- Dependencia real de integración: T012/T014 referencian el playbook de T011; T018 y T026 editan las mismas skills que T014/T015 (serializar entre sí)

### Within Each User Story

- Scripts antes que skills que los invocan; playbooks antes que su integración en pipelines; validación de quickstart al final de cada historia

### Parallel Opportunities

- T002 ∥ T001; T004 ∥ T003
- US1: T005 ∥ T008 (script y tests en archivos distintos); T009 tras T005–T007
- US2: T011 puede arrancar en paralelo con toda US1 (archivos distintos)
- US5: T020 ∥ T021 ∥ T022 ∥ T023 (cuatro archivos distintos), luego T024 → T025 → T026
- US6: T028 ∥ T033 (README y adaptadores nativos, archivos distintos)
- Historias completas en paralelo si hay capacidad: US1 ∥ US2 (payloads distintos), US4 ∥ US5 (scripts) — cuidando los archivos de skills compartidos (T012, T015, T018, T026 tocan `speckit-specify-auto/SKILL.md`: serializar)

---

## Parallel Example: User Story 5

```bash
# Lanzar los cuatro archivos independientes de US5 juntos:
Task: "Implementar get-parallel-groups.ps1"       # T020
Task: "Implementar invoke-secondary.ps1"          # T021
Task: "Implementar update-quota.ps1"              # T022
Task: "Escribir tests Pester de los 3 scripts"    # T023
# Luego, en secuencia: T024 (playbook) → T025 (skill) → T026 (integración) → T027 (validación)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 (Setup) + Phase 2 (Foundational)
2. Phase 3 (US1): `/speckit-models` funcionando
3. **PARAR y VALIDAR**: quickstart escenario 1 — inventario real de la máquina
4. Con inventario confiable, todo lo demás tiene fundamento

### Incremental Delivery

1. US1 (inventario) → demo: `models.json` real ✅
2. US2 (triage) → demo: el sistema decide flujo y modelos antes de gastar ✅
3. US3 (pipeline ECO) → demo: idea chica de punta a punta con una llamada ✅
4. US4 (asignador) → demo: `tasks.md` etiquetado ✅
5. US5 (orquestador) → demo: implementación repartida entre CLIs con fallback ✅
6. US6 (distribución) → demo: instalable en proyecto limpio ✅

### Notes

- Verificar el checkpoint de cada historia antes de avanzar
- T012/T015/T018/T026 editan `speckit-specify-auto/SKILL.md` — no paralelizar entre sí
- Commit después de cada tarea o grupo lógico
