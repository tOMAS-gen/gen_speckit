# Research: Despacho multi-modelo de todas las fases

**Feature**: `008-multi-model-phase-dispatch` | **Date**: 2026-07-22

## R1 — Cómo transferir prompts largos de fase al secundario

**Decision**: agregar `--prompt-file <ruta>` a `invoke_secondary.py`, mutuamente
excluyente con `--prompt`. El script lee el archivo (UTF-8) y construye un prompt
inline CORTO que es un puntero: "Leé tus instrucciones completas en `<ruta>` y
ejecutalas" + identificación de la fase. El contenido largo nunca viaja por la línea
de comandos.

**Rationale**: hallazgos duros del código actual: (a) `get_headless_command` aplana
todo el whitespace del prompt a un espacio (invoke_secondary.py L83) — las
instrucciones de fase son multilínea con estructura; (b) `run_process` usa
`shell=True` → `cmd.exe` en Windows con límite ~8191 chars, ya golpeado en la feature
007 (T028, 9098 chars, falló); (c) el contrato headless-adapters ya establece el
patrón "referencias a archivos del disco, no contenido pegado" para spec.md/plan.md —
extenderlo al propio prompt es coherente. Pasar la ruta (no el contenido) mantiene el
comando corto sin importar el tamaño de las instrucciones.

**Alternatives considered**: (1) leer el archivo y sustituir el contenido en
`{prompt}` — reintroduce el límite de línea y el aplanado, descartado; (2) stdin —
`run_process` conecta stdin a DEVNULL y no todos los CLIs headless leen prompt por
stdin, cambio invasivo multiplataforma; (3) dividir prompts a mano como en 007 —
es exactamente la deuda que esta feature paga.

## R2 — Dónde vive la lógica de despacho de fase: playbook vs. script

**Decision**: playbook Markdown nuevo `.specify/orchestrator/dispatch-phase.md`
(lógica de juicio: empaquetado del prompt de fase, verificación de artefacto, ciclo
de recuperación) + script Python nuevo `phase_candidates.py` (lógica determinista:
resolver la lista ordenada de candidatos efectivos de una fase desde el inventario).

**Rationale**: el contrato de portabilidad del orquestador (README) exige que
cualquier principal pueda ejecutar la lógica; la verificación de un artefacto de fase
("¿este spec.md cumple el template y es coherente con la idea?") requiere juicio de
LLM → playbook. La resolución de candidatos (ranking ∩ habilitados ∩ preferido ∩
cuota) es determinista y necesita tests → script. Mismo patrón ya validado por
triage/assign/orchestrate + get_parallel_groups/update_quota.

**Alternatives considered**: todo en playbook (no testeable, cada principal
reimplementa el filtrado con riesgo de divergencia); todo en script (la verificación
de contenido no es programable de forma robusta).

## R3 — Cómo se despacha una fase con interacción (clarify, analyze)

**Decision**: patrón de dos despachos con estado en archivos, decidido en clarify
(sesión 2026-07-22, Q2): despacho A produce el análisis/las preguntas como artefacto
(`specs/<feature>/.phase-dispatch/<fase>.questions.md`); el principal conduce la
conversación con el usuario en su sesión; despacho B recibe las respuestas (archivo
`<fase>.answers.md`) e integra los cambios en el artefacto de la fase. El principal
verifica tras cada despacho.

**Rationale**: FR-005/FR-005a — el trabajo analítico completo (incluida la
integración) queda en el modelo asignado (de `alta` para fases de criterio); el
principal solo conversa y verifica. Los archivos intermedios hacen el flujo retomable
(FR-012) y auditable, y viajan bien por `--prompt-file`.

**Alternatives considered**: un solo despacho con integración por el principal
(el principal caro paga la edición — contradice el objetivo); sesión interactiva del
secundario (los modos headless son one-shot; no portable).

## R4 — Modelo de datos para habilitado/deshabilitado y preferido

**Decision**: dos campos aditivos en `.specify/models.json`:
(a) `deshabilitado: true` opcional **por modelo** dentro de `clis.<cli>.modelos[]`
(hoy solo existe a nivel CLI); (b) `preferido: "<cli>"` opcional a nivel raíz
(hermano de `asignacion`), designando el único agente entre cuyos modelos habilitados
se reparte el trabajo.

**Rationale**: `merge_node` ya mergea `modelos[]` por elemento y por campo (fix de la
feature 007), así que un flag por modelo se preserva ante re-scans sin trabajo extra;
`deshabilitado` reutiliza el nombre y la semántica ya establecidos a nivel CLI
(clis_config.py L234–236, scan_models.py L336) — un solo concepto, dos alcances.
`preferido` a nivel raíz porque es una decisión global del usuario, no un atributo de
un CLI. Los consumidores (`build_asignacion`, `build_asignacion_por_fase`,
`phase_candidates.py`, playbooks assign/orchestrate) filtran modelos deshabilitados y
aplican `preferido` si está presente. Constitución IV intacta: el sistema no excluye;
el usuario sí puede, y el reporte lo registra como decisión del usuario.

**Alternatives considered**: lista `deshabilitados: ["cli/modelo"]` a nivel raíz
(segunda fuente de verdad, riesgo de desincronización con `modelos[]`); archivo de
preferencias separado (fragmenta el inventario; el merge existente ya resuelve la
preservación).

## R5 — Qué fases se despachan y cuáles no

**Decision**: despachables: specify, plan, checklist, tasks (generación), analyze —
y en clarify/analyze el patrón de dos despachos de R3. NUNCA se despachan: el triage
(lo ejecuta el principal por definición — es quien decide), el paso de asignación de
tasks cuando el asignado es el principal (caso típico: es el más capaz), los gates de
confirmación y toda conversación con el usuario. Si el modelo asignado a una fase ES
el principal, la ejecuta en sesión (regla existente de no auto-invocación).

**Rationale**: mapa directo de FR-001/FR-005/FR-011 sobre el pipeline de 7 fases.
El triage es barato y es la raíz de decisión: despacharlo crearía un ciclo
(¿quién decide quién decide?).

**Alternatives considered**: despachar también el triage a `alta` cuando el principal
es económico — ya cubierto por la regla de escalada existente del playbook triage
(el triage lo ejecuta "el modelo más capaz disponible", escalando si hace falta).

## R6 — Verificación de artefactos de fase por el principal

**Decision**: verificación de dos niveles definida en el contrato
`phase-dispatch.md`: (1) estructural — el artefacto existe, parsea como Markdown y
contiene las secciones obligatorias de su template (lista por fase declarada en el
contrato); (2) de contenido — el principal lee el artefacto y confirma coherencia con
la entrada de la fase (la idea/spec previo), sin re-hacer el trabajo. Fallo → ciclo
FR-003: 1 reintento al mismo modelo con el motivo → 1 escalada al siguiente candidato
de mayor capacidad → el principal ejecuta la fase en sesión.

**Rationale**: espeja la "verificación estándar" de tareas (orchestrate.md Paso 4)
adaptada a artefactos de documentación: ahí el criterio es diff+tests, acá es
template+coherencia. El tercer escalón (principal en sesión) garantiza que el
pipeline nunca queda bloqueado por el reparto de fases (FR-003, edge case del spec).

**Alternatives considered**: verificación solo estructural (deja pasar artefactos
válidos-pero-incoherentes — edge case explícito del spec); re-ejecución completa por
el principal como verificación (duplica el costo, anula el ahorro).

## R7 — Registro en el reporte: asignado vs. efectivo

**Decision**: extender la tabla "Modelos por fase" del `report-template.md` con una
columna `Efectivo` (modelo que realmente ejecutó la fase; igual al asignado salvo
fallback) manteniendo las columnas actuales. Los fallbacks se registran además en
Eventos, y Métricas suma el desglose fases-por-modelo y el % del trabajo total
(fases + tareas) en modelos económicos (FR-010).

**Rationale**: la tabla es sección PARSEABLE (la lee la retomabilidad) — una columna
nueva al final es aditiva y los reportes viejos siguen siendo válidos (parser
tolerante a 3 o 4 columnas). Alternativa de anotar el efectivo entre paréntesis en la
misma celda rompería el parseo simple por columnas.

**Alternatives considered**: sección nueva separada (duplica estado, riesgo de
divergencia con la tabla existente).

## R8 — Inventario de agentes multi-modelo (OpenCode, Hermes)

**Decision**: sin cambios de esquema del catálogo. Un agente multi-modelo se registra
por el flujo existente de `speckit-clis` (validación V1–V6 ya exige `{prompt}` y
selección de modelo si hay >1 modelo), declarando su plantilla `headless` con
`{modelo}` y su lista de modelos. Esta feature solo (a) documenta el patrón en el
contrato `inventory-fields.md`, (b) añade la gestión de habilitado por modelo y
preferido a `clis_config.py`/skill `speckit-clis`, y (c) valida el caso con un agente
multi-modelo simulado en tests. Registrar OpenCode/Hermes concretos queda fuera del
alcance (clarify Q3: capacidad genérica, el usuario los registra después).

**Rationale**: la feature 003 ya entregó el registro genérico por datos; duplicarlo
sería re-implementación. El gap real es la granularidad (modelo individual) y la
preferencia — exactamente lo que agrega R4.

**Alternatives considered**: incluir entradas de catálogo para OpenCode/Hermes —
descartado por decisión del usuario en clarify (Q3: opción B).

## R9 — Activación y retomabilidad del despacho de fases

**Decision**: el despacho de fases se activa cuando `.specify/models.json` existe y
es válido (clarify Q1); el "modo decisión-solo" del playbook triage pasa de ser el
comportamiento efectivo a ser el fallback (sin inventario, sin candidatos, o modo
clásico pedido por el usuario). Retomabilidad: el estado por fase ya vive en la tabla
"Modelos por fase" del reporte (`pendiente|ejecutada|omitida`); al retomar, el
pipeline relee la tabla y despacha solo las fases `pendiente`, reutilizando los
archivos de `.phase-dispatch/` si existen.

**Rationale**: reutiliza el mecanismo de estado que la retomabilidad ya parsea;
ningún estado nuevo fuera del reporte + archivos intermedios versionables.

**Alternatives considered**: archivo de estado JSON dedicado (segunda fuente de
verdad frente al reporte; innecesario).
