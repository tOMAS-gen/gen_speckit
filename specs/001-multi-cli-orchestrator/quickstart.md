# Quickstart: validación del Orquestador Multi-CLI

**Feature**: 001-multi-cli-orchestrator | **Date**: 2026-07-18

Guía de escenarios ejecutables que prueban la feature end-to-end. Cada escenario mapea
a criterios de éxito de la spec ([spec.md](spec.md)).

## Prerequisitos

- Windows 11 + PowerShell, repo inicializado con spec-kit (`.specify/` presente).
- Al menos 2 de los 3 CLIs instalados y autenticados (`claude`, `codex`, `kimi`);
  ideal: los tres, para SC-003.
- Pester instalado para los tests de scripts: `Install-Module Pester -Force`.

## Escenario 1 — Inventario (US1, SC-007)

```powershell
# cronometrar: debe completarse (incluida la declaración manual) en < 10 min
/speckit-models
```

**Esperado**: `.specify/models.json` existe y valida contra
[contracts/models-schema.md](contracts/models-schema.md); los CLIs no instalados
figuran `instalado: false` y fuera de `asignacion`; los datos no detectables quedan
`"desconocido"` o preguntados, nunca inventados.

**Persistencia de ediciones (FR-004)**: editar a mano `capacidad` de un modelo,
re-ejecutar `/speckit-models`, verificar que la edición sobrevive o media confirmación.

## Escenario 2 — Triage y autocorrección (US2)

```powershell
# Idea simple invocada en flujo IDEAL sin bypass → debe proponer cambiar a ECO
/speckit-specify-auto "agregar un comando que imprima la versión del proyecto"

# Idea simple con bypass → cambia solo a ECO y lo informa en el reporte
/speckit-specify-auto "agregar un comando que imprima la versión del proyecto" -bypass
```

**Esperado**: el triage clasifica ANTES de ejecutar fases;
`specs/<feature>/orchestration-report.md` registra complejidad, flujo
recomendado/usado y, si aplica, escalada/degradación del punto de entrada (probar
también escribiendo la idea desde el CLI más económico disponible).

## Escenario 3 — Pipeline ECO retomable (US3, SC-001, SC-008)

```powershell
/speckit-specify-auto-eco "idea clara y chica" -bypass    # debe llegar a implement sin pausas
/speckit-specify-auto-eco "otra idea" --sin-implementar   # debe frenar tras la planificación
```

**Retomabilidad**: interrumpir una corrida después de plan; reinvocar el mismo
comando; debe detectar spec/plan existentes y continuar desde tasks sin rehacer nada.

## Escenario 4 — Asignación (US4, SC-002, SC-003)

Con un `tasks.md` generado y `models.json` válido, invocar el asignador de forma
directa (sin pipeline): pedir al CLI principal ejecutar el playbook
`.specify/orchestrator/assign.md` sobre el `tasks.md` de la feature (el playbook es
invocable standalone por contrato; también corre integrado como paso post-tasks de
los pipelines).

**Esperado**:
- Cada tarea con exactamente una `[C:]` y una `[M:]`, formato oficial intacto
  (validar con la regex de [contracts/task-labels.md](contracts/task-labels.md)).
- Toda tarea `[C:baja]` asignada a modelo económico si existe alguno con cuota (SC-002).
- Con 3 CLIs disponibles y feature mixta, los 3 reciben tareas (SC-003).
- Editar a mano una `[M:]` y verificar que la implementación la respeta.

## Escenario 5 — Orquestación con fallback (US5, SC-005)

Con un `tasks.md` etiquetado (puede ser una feature de juguete con 4–6 tareas):

```powershell
/speckit-orchestrate
```

**Esperado**:
- Cada tarea ejecutada por su CLI asignado vía headless (verificar en el reporte).
- Tareas `[P]` sin rutas compartidas corren en paralelo; con ruta compartida se
  serializan (revisar eventos del reporte).
- Solo tareas verificadas quedan `[X]` en `tasks.md`.

**Fallback (SC-005)**: simular agotamiento marcando a mano `cuota: "agotada"` en el
CLI preferido de `[C:baja]` (o usar un CLI free con cuota realmente agotada);
re-ejecutar: el 100% de sus tareas deben completarse con el siguiente candidato, sin
intervención, con eventos registrados y `models.json` actualizado
(`cuota_desde`/`cuota_reset` presentes).

## Escenario 6 — Compatibilidad (US6, SC-006)

```powershell
# Los comandos base de spec-kit deben comportarse EXACTAMENTE igual que sin las mejoras
/speckit-specify "una feature cualquiera"
/speckit-plan
/speckit-tasks
```

**Esperado**: ningún cambio de comportamiento ni de formato en los artefactos
generados por los comandos originales; las mejoras solo actúan cuando se invocan sus
comandos nuevos.

## Escenario 7 — Medición de ahorro (SC-004)

Correr la misma feature de juguete dos veces: (a) todo con el modelo más caro
(asignación manual), (b) con el orquestador. Comparar consumo (tokens/uso reportado
por cada CLI) — el consumo del modelo caro en (b) debe ser ≤ 50% del de (a). Registrar
el resultado en la sección Métricas del reporte.

## Resultados de validación

**2026-07-18 — Escenario 1 ejecutado en máquina real (Windows 11)**:

- Detección: claude 2.1.214 instalado y autenticado ✅; kimi 0.27.0 instalado
  (autenticación `"desconocido"`, sin inventar) ✅; codex AUSENTE → `instalado:false`
  y excluido de `asignacion` ✅ (aceptación 2).
- Escaneo en ~2 s; `models.json` válido contra el contrato (UTF-8 sin BOM,
  indentación 2, referencias de `asignacion` existentes) ✅.
- Persistencia de ediciones (FR-004): se editó a mano `plan` de claude ("Max 5x") y
  `capacidad` de kimi/k2 (7), se re-ejecutó el scan, ambas ediciones sobrevivieron ✅.
- Declaración manual pendiente del usuario: plan/cuota reales (quedaron editables).

**2026-07-18 — Auditoría de compatibilidad (escenario 6, parcial sin instalación
limpia)**: skills base y templates de spec-kit sin modificar (timestamps de
instalación intactos), única excepción el agregado aditivo documentado en
`tasks-template.md` (etiquetas opcionales `[C:]`/`[M:]`) ✅.

**Suite Pester**: 44/44 tests en verde (scan-models 12, get-parallel-groups 12,
invoke-secondary 12, update-quota 8).

Escenarios 2, 3, 4, 5 y 7 requieren corridas end-to-end con cuota real multi-CLI
(Paso 7 del README) — pendientes de ejecución por el usuario.

## Tests unitarios de scripts

```powershell
Invoke-Pester tests/powershell/
```

**Cobertura mínima**: parseo de etiquetas (regex del contrato), agrupación/serialización
de `[P]` con rutas compartidas, clasificación de fallos (cuota vs transitorio vs
indisponible), escritura acotada de `update-quota.ps1` (solo campos de cuota, nunca
otros), y detección de CLIs ausentes en `scan-models.ps1`.
