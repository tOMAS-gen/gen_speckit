# Research: Orquestador Multi-CLI para Spec Kit

**Feature**: 001-multi-cli-orchestrator | **Date**: 2026-07-18

Incógnitas extraídas del Technical Context y resueltas. No quedan NEEDS CLARIFICATION.

## R1 — Modo headless de cada CLI

**Decision**: comandos base por CLI (plantilla que `scan-models.ps1` propone y el
usuario puede corregir en `models.json.clis.<cli>.headless`):

| CLI | Comando headless | Notas |
|---|---|---|
| Claude Code | `claude -p "<prompt>" --dangerously-skip-permissions --output-format json` | `-p` = print/no interactivo; el flag de permisos implementa la Clarificación S2 (sin confirmaciones) |
| Codex CLI | `codex exec "<prompt>" --sandbox workspace-write --ask-for-approval never --skip-git-repo-check --json` | `--full-auto` está deprecado; sandbox `workspace-write` limita escritura al workspace (alineado con "no operar fuera del repo") |
| Kimi CLI | `kimi --print --yolo --command "<prompt>" --final-message-only` | `--print` es el modo no interactivo; `--yolo` auto-aprueba (equivalente a S2) |

**Rationale**: los tres CLIs soportan ejecución no interactiva con auto-aprobación,
que es el requisito de FR-016. Codex además restringe escritura al workspace por
sandbox, y en Claude/Kimi la restricción "dentro del repo" se refuerza por prompt (la
tarea despachada instruye operar solo sobre rutas del repo) + verificación del
principal (FR-019).

**Alternatives considered**: `codex exec --full-auto` (deprecado, imprime warning);
usar APIs/SDKs de cada proveedor en lugar de CLIs (rechazado: rompe el modelo de
suscripción/planes de los CLIs y duplica autenticación); MCP entre CLIs (rechazado:
feature no universal — viola Constitución II).

**Sources**:
- [Codex non-interactive mode (OpenAI Developers)](https://developers.openai.com/codex/noninteractive)
- [Codex exec headless guide (Developers Digest)](https://www.developersdigest.tech/blog/codex-exec-ci-headless-guide)
- [Kimi CLI `kimi` command reference (Moonshot)](https://moonshotai.github.io/kimi-cli/en/reference/kimi-command.html)
- [Kimi CLI command-line options (DeepWiki)](https://deepwiki.com/MoonshotAI/kimi-cli/2.3-command-line-options-reference)

## R2 — Detección de CLIs, versiones y modelos

**Decision**: `scan-models.ps1` detecta por sondeo: `Get-Command <cli>` (instalado),
`<cli> --version` (versión), y prueba de invocación headless mínima e inocua para
confirmar autenticación (p. ej. prompt trivial con timeout corto). Los modelos por CLI
se siembran desde una tabla estática incluida en el script (corregible), porque ningún
CLI expone un listado de modelos consultable de forma uniforme. Plan y cuota son
siempre declarados por el usuario (FR-002); lo no declarado queda `"desconocido"`.

**Rationale**: el sondeo cubre lo detectable sin depender de features exclusivas; la
tabla estática da un punto de partida útil que el usuario corrige una sola vez
(FR-004: sus correcciones prevalecen).

**Alternatives considered**: parsear config files internos de cada CLI (frágil,
formatos privados que cambian); llamar APIs de los proveedores para listar modelos
(requiere API keys que el usuario de suscripción no necesariamente tiene).

## R3 — Portabilidad de la lógica orquestadora

**Decision**: la lógica core (triage, asignación, orquestación, formato de reporte)
vive en playbooks Markdown neutrales en `.specify/orchestrator/`. Las skills de
`.claude/skills/` son adaptadores finos que solo dicen "leé y ejecutá el playbook X".
Cualquier CLI que actúe como principal ejecuta los mismos playbooks; ningún playbook
referencia herramientas o features propias de un CLI (solo: leer/escribir archivos,
ejecutar scripts PowerShell, invocar comandos).

**Rationale**: Constitución II exige comportamiento equivalente desde cualquier CLI.
Markdown interpretado por el LLM + scripts PowerShell es el mínimo común denominador
de los tres CLIs.

**Alternatives considered**: duplicar la lógica en las carpetas de skills/prompts de
cada CLI (rechazado: triple mantenimiento, deriva garantizada); implementar el
orquestador como programa standalone (rechazado: pierde el juicio del LLM principal
para verificación e integración, y agrega un runtime a distribuir).

## R4 — Despacho paralelo y conflictos de archivos

**Decision**: el despacho de tareas `[P]` usa `Start-Job` de PowerShell, una job por
tarea, con stdout/stderr capturados a archivos por tarea bajo el directorio de la
feature. Antes de despachar, `get-parallel-groups.ps1` agrupa las tareas: extrae las
rutas declaradas en cada descripción de tarea y serializa (mismo grupo secuencial)
las que comparten ruta, aunque estén marcadas `[P]` (FR-017). El principal espera los
jobs del grupo, verifica cada resultado (FR-019) y recién entonces despacha el grupo
siguiente.

**Rationale**: `Start-Job` es nativo de Windows PowerShell (sin dependencias), y la
captura a archivos deja evidencia auditable para el reporte y la verificación.

**Alternatives considered**: `ForEach-Object -Parallel` (requiere PowerShell 7 —
restringiría la compatibilidad con Windows PowerShell 5.1); despacho secuencial puro
(rechazado: desperdicia el paralelismo `[P]` que spec-kit ya declara).

## R5 — Detección reactiva de agotamiento de cuota

**Decision**: `invoke-secondary.ps1` clasifica cada fallo de invocación: si el
stderr/salida matchea patrones de límite de uso (p. ej. "rate limit", "usage limit",
"quota", "límite de uso", códigos 429) se clasifica `cuota_agotada`; cualquier otro
fallo se reintenta 1 vez (Clarificación S4) y al segundo fallo se clasifica
`indisponible`. Ante `cuota_agotada`, `update-quota.ps1` persiste en `models.json`:
`cuota = "agotada"` + `cuota_desde` (timestamp ISO) + `cuota_reset` estimado según la
ventana declarada del plan (Clarificación S3). Ambas clasificaciones disparan fallback
al siguiente candidato del ranking (FR-018).

**Rationale**: los CLIs no exponen consulta proactiva de cuota de forma uniforme; la
detección reactiva por patrones es el único mecanismo portable. La tabla de patrones
por CLI vive en `contracts/headless-adapters.md` y es extensible.

**Alternatives considered**: consultar dashboards/APIs de uso por proveedor
(no uniforme, requiere credenciales extra); contadores locales de tokens estimados
(imprecisos y se desincronizan con el consumo real fuera del orquestador).

## R6 — Siembra de capacidad/costo relativos

**Decision**: la tabla estática de R2 incluye valores iniciales de `capacidad` (1–10)
y `costo` (1–3) por modelo conocido (ej.: claude/opus 9/3, claude/sonnet 7/2,
codex/gpt-5-codex 8/2, codex/gpt-5-mini 5/1, kimi/k2 6/1), y `scan-models.ps1` genera
las listas `asignacion` ordenando por: capacidad suficiente para el nivel, luego menor
costo, luego mayor disponibilidad. El usuario corrige a gusto; sus valores prevalecen.

**Rationale**: FR-003 exige valores comparables; una siembra razonable evita arrancar
de cero y el diseño ya contempla la corrección manual como fuente de verdad.

**Alternatives considered**: pedir todos los valores al usuario (fricción alta,
contradice SC-007 < 10 min); benchmarks automáticos (costosos — quemarían la cuota
que se quiere ahorrar).

## R7 — Formato y ciclo de vida del reporte de orquestación

**Decision**: `specs/<feature>/orchestration-report.md`, creado por el triage y
actualizado por cada fase (asignación, implementación) con secciones fijas definidas
en `.specify/orchestrator/report-template.md`: decisión de triage, modelos por fase,
tabla de asignaciones, eventos (fallbacks, escaladas, reintentos), estado final por
tarea y métricas de ahorro (SC-004). Cada fase además imprime un resumen en consola
(Clarificación S5).

**Rationale**: persistir junto a los artefactos de la feature lo hace auditable y
retomable (FR-012: el pipeline detecta el estado desde el reporte + artefactos).

**Alternatives considered**: solo consola (se pierde auditoría y la medición de
SC-004); JSON puro (menos legible para el usuario; el reporte es para humanos y las
métricas duras igual quedan en secciones estructuradas parseables).
