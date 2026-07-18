# Contract: operaciones de configuración de CLIs

**Feature**: 003-generic-cli-support

Semántica de las operaciones de la skill `speckit-clis` (implementadas en
`clis-config.ps1`, funciones testeables). Todas operan sobre `.specify/models.json`.

## Registrar (Add-CliDefinition)

Entrada: nombre, plantilla headless, modelos[], patrones_cuota[] (opcional),
version_cmd (opcional).

Validación de alta — TODAS deben pasar o el registro se RECHAZA completo con la lista
de problemas (FR-003):

| # | Regla | Mensaje ante fallo |
|---|---|---|
| V1 | nombre cumple `^[a-z][a-z0-9-]*$` | formato de nombre inválido (kebab-case) |
| V2 | nombre no existe en el inventario | duplicado: ofrecer editar el existente |
| V3 | `headless` contiene `{prompt}` | plantilla sin placeholder de prompt |
| V4 | si hay >1 modelo, `headless` contiene `{modelo}` o se acepta el default `--model` | no se puede seleccionar modelo |
| V5 | ≥1 modelo con id único, capacidad 1–10, costo 1–3 | modelo inválido (detalle por campo) |
| V6 | cada regex de `patrones_cuota` compila | patrón N no es una regex válida |

Efecto: entrada nueva en `clis` con `origen: "registrado"`, `instalado`/`autenticado`
por detección inmediata (niveles a–b de verificación, sin gasto), `cuota:
"desconocido"`; `asignacion` se regenera respetando ediciones manuales.

## Editar (Edit-CliDefinition)

Misma validación que el alta sobre el resultado final; los campos no mencionados no se
tocan. Editar un CLI de `origen: catalogo` solo modifica el inventario (el catálogo es
inmutable en runtime).

## Verificar (Invoke-CliVerification)

Niveles acumulativos a→b→c (data-model §4). Regla dura: el nivel c exige el parámetro
explícito de aprobación y MUESTRA el comando renderizado antes de ejecutar (FR-007,
SC-006). Salida: diagnóstico estructurado `{nivel, resultado, detalle, correccion}`
por nivel ejecutado. Actualiza solo campos detectables (FR-008).

## Dar de baja (Remove-CliDefinition)

1. Buscar etiquetas `[M:<cli>/...]` en `specs/*/tasks.md` con tareas sin `[X]` →
   advertirlas (el orquestador les aplicará fallback — regla existente).
2. Confirmación explícita del usuario.
3. CLI de `origen: registrado` → se elimina la entrada. CLI de `origen: catalogo` →
   se marca `deshabilitado: true` (si se eliminara, el próximo escaneo lo re-crearía);
   el escaneo y el ranking respetan `deshabilitado`.
4. `asignacion` se regenera; el reporte de la operación lista qué cambió.

## Reglas transversales

- Escrituras siempre UTF-8 sin BOM, indentación 2, preservando las garantías de
  ediciones manuales (`models.scan.json`).
- Toda operación es invocable desde cualquier CLI principal (skill portable +
  script — Constitución II).
- Cero menciones de nombres de CLI concretos en `clis-config.ps1` (SC-003).
