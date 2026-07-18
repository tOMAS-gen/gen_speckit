# Contract: adaptadores headless por CLI

**Feature**: 001-multi-cli-orchestrator

Contrato entre el orquestador (`invoke-secondary.ps1`) y cada CLI secundario. El
comando concreto SIEMPRE se lee de `models.json.clis.<cli>.headless` (plantilla con
placeholders); esta tabla define los valores por defecto que propone el scan y las
reglas de interpretación de resultados.

## Plantillas por defecto

| CLI | Plantilla `headless` | Selección de modelo |
|---|---|---|
| claude | `claude -p "{prompt}" --dangerously-skip-permissions --output-format json` | `--model {modelo}` se agrega si la tarea lo especifica |
| codex | `codex exec "{prompt}" --sandbox workspace-write --ask-for-approval never --skip-git-repo-check --json` | `--model {modelo}` |
| kimi | `kimi -p "{prompt}" --yolo --model kimi-code/{modelo}` | alias calificado `kimi-code/<id>` (config.toml de Kimi Code); el placeholder ya está en la plantilla |

Reglas de sustitución:
- `{prompt}` — texto de la tarea empaquetada (ver "Prompt de tarea" abajo). Escapar
  comillas dobles internas según reglas de PowerShell antes de sustituir.
- `{modelo}` — id del modelo de la etiqueta `[M:cli/modelo]`.
- La invocación corre con working directory = raíz del repo.

## Prompt de tarea (lo que recibe el secundario)

El orquestador empaqueta cada tarea con este contenido mínimo:

1. Identificación: `T###`, descripción literal de la tarea y ruta(s) declaradas.
2. Contexto: rutas de `spec.md`, `plan.md` y artefactos relevantes de la feature
   (el secundario los lee del disco — nunca se pega el contenido completo para no
   quemar contexto).
3. Restricciones: operar SOLO dentro del repositorio; no tocar archivos fuera de las
   rutas de la tarea salvo necesidad declarada; no marcar checkboxes en `tasks.md`
   (eso lo hace el principal tras verificar); reportar al final un resumen de qué
   archivos tocó.

## Interpretación de resultados

| Señal | Clasificación | Acción del orquestador |
|---|---|---|
| Exit code 0 + salida coherente | `exito` | Verificación FR-019 (diff vs tarea + validaciones del proyecto) |
| Salida/stderr matchea patrones de cuota (ver tabla) | `cuota_agotada` | `update-quota.ps1` persiste estado; fallback inmediato al siguiente candidato |
| Otro fallo (exit ≠ 0, timeout, salida vacía) — 1er intento | `fallo_transitorio` | 1 reintento con el mismo modelo (Clarificación S4) |
| Otro fallo — 2do intento consecutivo | `indisponible` | Fallback al siguiente candidato; evento en reporte |

**Timeout por tarea**: 15 min por defecto (configurable por invocación); al expirar se
mata el job y cuenta como fallo del intento en curso.

## Patrones de detección de cuota agotada (extensibles)

| CLI | Patrones (regex, case-insensitive, sobre stdout+stderr) |
|---|---|
| claude | `usage limit`, `rate limit`, `quota`, `limit reached`, `429` |
| codex | `rate limit`, `usage`, `quota exceeded`, `429`, `plan limit` |
| kimi | `rate limit`, `quota`, `429`, `insufficient.*balance` |

Un match en cualquier intento (incluido el reintento) reclasifica el fallo como
`cuota_agotada` — el reintento de S4 NO aplica a fallos de cuota.

## Portabilidad del principal (Constitución II)

Cualquier CLI puede ser principal. El contrato del principal es: saber leer los
playbooks de `.specify/orchestrator/`, ejecutar scripts PowerShell y editar archivos.
Los tres CLIs soportados cumplen ese mínimo. El principal NUNCA se auto-invoca por
headless: sus propias tareas asignadas las ejecuta en sesión.
