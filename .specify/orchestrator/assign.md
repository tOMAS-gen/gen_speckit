# Playbook: Clasificación y asignación de tareas

> Lógica portable. Entrada: `specs/<feature>/tasks.md` + `.specify/models.json`
> válidos. Salida: cada tarea con etiquetas `[C:...]` y `[M:...]` inline, sección
> "Asignaciones" del reporte actualizada. Invocable de dos formas: integrado como paso
> post-tasks de los pipelines, o DIRECTO sobre un tasks.md existente (para pruebas o
> para re-asignar tras una re-generación).

## Quién asigna

El **modelo más capaz disponible** (primer candidato de `asignacion.alta` con cuota).
Equivocar el reparto es caro; ejecutar una tarea simple, no.

## Reglas de oro (contrato task-labels.md)

1. El formato oficial de spec-kit NO se toca: checkbox, `T###`, `[P]`, `[US#]` y la
   descripción con ruta quedan byte a byte como estaban.
2. Las etiquetas nuevas van DESPUÉS de las oficiales y antes de la descripción:
   `- [ ] T012 [P] [US1] [C:baja] [M:kimi/k2] Crear modelo...`
3. **Idempotencia**: una tarea que YA tiene `[C:]`/`[M:]` no se toca (respeto a
   ediciones manuales), salvo que el usuario pida `-reasignar` explícitamente.
4. Etiquetas desconocidas de terceros se preservan como parte de la descripción.

## Paso 1 — Clasificar complejidad `[C:]`

Para cada tarea sin clasificar, evaluar:

| Dimensión | baja | media | alta |
|---|---|---|---|
| Alcance | 1 archivo, cambio localizado | 2–4 archivos relacionados | Transversal, muchos archivos o diseño nuevo |
| Contexto necesario | La descripción alcanza | Requiere leer el plan/spec | Requiere entender el sistema completo |
| Dependencias | Ninguna o triviales | Depende de 1–2 tareas | Nudo de dependencias o bloqueante de historia |
| Riesgo | Reversible, sin datos | Toca persistencia o APIs | Migraciones, seguridad, pagos, difícil de revertir |
| Tipo | Boilerplate, config, docs | Lógica de negocio estándar | Algoritmos, integración compleja, arquitectura |

Clasificación = nivel MÁXIMO alcanzado en cualquier dimensión (una tarea trivial en
todo menos riesgo alto es `alta`).

## Paso 2 — Asignar modelo `[M:]`

Para cada tarea, recorrer `asignacion.<nivel>` EN ORDEN y elegir el primer candidato
que cumpla:

1. `cuota != "agotada"` en su CLI (si `cuota_reset` ya venció, tratarla como `ok`).
2. `contexto_k` suficiente para la tarea (estimar: tarea + archivos que toca + spec
   relevante; ante la duda con `contexto_k` desconocido, asumir que alcanza).

Si ningún candidato del nivel califica → escalar al nivel superior (baja→media→alta) y
registrar el motivo en Eventos. Si tampoco → dejar la tarea SIN `[M:]` y reportarla
como no asignable (el orquestador la bloqueará hasta que haya cuota o corrección).

## Refinamiento por fase (opcional)

Si `.specify/models.json` tiene `asignacion_por_fase`, usarla para ordenar los
candidatos YA calificados del Paso 2, no para filtrarlos:

- Las tareas de historias de usuario van a la fase `implement`, salvo que su
  descripción indique otra fase del pipeline (`plan`, `analyze`, `tasks`,
  `specify`, `clarify`, `checklist`).
- Las tareas de Setup/Foundational no tienen fase de pipeline asociada; usar
  directamente el orden de `asignacion.<nivel>`.
- Para la fase detectada, ordenar los candidatos que pasaron los filtros del
  Paso 2 según su posición en `asignacion_por_fase.<fase>`; el primero de esa
  lista que también esté calificado en el nivel es el elegido.
- Si la fase no está en `asignacion_por_fase`, volver al orden normal de
  `asignacion.<nivel>`.

Este refinamiento es opcional. `asignacion.<nivel>` sigue decidiendo qué
candidatos califican por complejidad, cuota y contexto. `asignacion_por_fase`
solo altera el orden de preferencia entre ellos cuando está disponible.

Si `asignacion_por_fase` no existe en `models.json`, ejecutar el Paso 2 tal cual:
sin advertencias, sin cambios de comportamiento.

## Paso 3 — Verificar el reparto (Constitución IV, SC-003)

Tras asignar todo:

- Si algún CLI instalado y autenticado quedó con CERO tareas: verificar si es
  legítimo (la feature no tiene tareas de su nivel) y JUSTIFICARLO en la sección
  Asignaciones del reporte. No excluir por preferencia — solo por capacidad/cuota.
- Verificar con la regex del contrato que ninguna línea oficial se alteró.

## Paso 4 — Persistir

1. Escribir las etiquetas inline en `tasks.md` (edición mínima por línea).
2. Actualizar la sección "Asignaciones" del reporte (tabla parseable): una fila por
   tarea con C, M y estado `pendiente`.
3. Resumen en consola: tareas por nivel, tareas por modelo, no-asignables si las hay.
4. Recordar al usuario: puede editar cualquier `[M:]` a mano antes de implementar, y
   si re-genera `tasks.md` (re-ejecuta `/speckit-tasks`) las etiquetas se pierden y
   hay que re-asignar (este playbook, modo directo).
