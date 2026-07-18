# Contract: etiquetas de tareas en `tasks.md`

**Feature**: 001-multi-cli-orchestrator

Contrato entre el asignador (productor), el usuario (editor con prioridad) y el
orquestador (consumidor). Las etiquetas son ADITIVAS al formato oficial de spec-kit;
ninguna herramienta de este proyecto reordena ni reescribe las partes oficiales
(Constitución I, FR-015).

## Gramática

Línea oficial de spec-kit (sin cambios):

```
- [ ] T### [P]? [US#]? <descripción con ruta(s)>
```

Línea etiquetada (tras el asignador):

```
- [ ] T### [P]? [US#]? [C:<nivel>] [M:<cli>/<modelo>] <descripción con ruta(s)>
```

- `<nivel>` ∈ `baja` | `media` | `alta`
- `<cli>` ∈ `claude` | `codex` | `kimi`
- `<modelo>` = id existente en `models.json.clis.<cli>.modelos[].id`
- Las etiquetas nuevas van SIEMPRE después de las oficiales (`[P]`, `[US#]`) y antes
  de la descripción, separadas por espacios.

## Regex de referencia (parseo tolerante)

Detección de etiquetas en una línea de tarea:

```regex
^\s*- \[[ xX]\] +(T\d{3,}) +(?:(\[P\]) +)?(?:(\[US\d+\]) +)?(?:\[C:(baja|media|alta)\] +)?(?:\[M:([a-z]+)/([A-Za-z0-9._-]+)\] +)?(.+)$
```

- Grupos: 1=id, 2=[P], 3=[US#], 4=complejidad, 5=cli, 6=modelo, 7=descripción.
- Una línea sin `[C:]`/`[M:]` es válida (estado pre-asignación); el orquestador NO
  despacha tareas sin `[M:]` — las reporta como sin asignar.
- Etiquetas desconocidas adicionales se preservan como parte de la descripción (no
  romper herramientas de terceros).

## Reglas del asignador

1. Corre al final de la fase tasks, ejecutado por el modelo más capaz disponible
   (FR-013; invariante 5 de models-schema.md).
2. Clasifica `[C:]` considerando: alcance, contexto necesario, dependencias, riesgo
   y tipo de tarea.
3. Asigna `[M:]` = primer candidato de `asignacion.<nivel>` con cuota disponible y
   `contexto_k` suficiente para la tarea (FR-014).
4. En una feature con varios niveles de complejidad y varios CLIs disponibles, el
   resultado debe repartir trabajo entre todos los CLIs disponibles (Constitución IV;
   SC-003) — si un CLI quedó sin tareas, el asignador lo justifica en el reporte.
5. Idempotencia: re-ejecutar el asignador sobre un `tasks.md` ya etiquetado NO cambia
   etiquetas existentes (respeto a ediciones manuales — FR-016) salvo pedido explícito
   del usuario (`-reasignar`).

## Reglas del orquestador (consumo)

1. Antes de despachar, valida cada `[M:]` contra `models.json`: CLI instalado, modelo
   existente. Etiqueta inválida → aplicar fallback del ranking del nivel `[C:]` de la
   tarea e informar, o pedir corrección si no hay candidatos (edge case de la spec).
2. `[P]` habilita paralelismo SOLO entre tareas sin rutas compartidas
   (`get-parallel-groups.ps1`); conflicto de ruta → serializar (FR-017).
3. Solo el principal marca `[X]`, y solo tras la verificación estándar (FR-019).
4. Al reasignar por fallback, el orquestador actualiza la etiqueta `[M:]` en
   `tasks.md` y registra el evento en el reporte (trazabilidad).

## Ejemplos

```markdown
- [ ] T012 [P] [US1] [C:baja] [M:kimi/k2] Crear modelo User en src/models/user.py
- [ ] T019 [US2] [C:alta] [M:claude/opus] Integrar pasarela de pagos en src/services/payments.py
- [x] T007 [P] [C:media] [M:codex/gpt-5-codex] Configurar linting en .eslintrc.json
- [ ] T031 [US3] Actualizar docs de despliegue en docs/deploy.md   <!-- válida: aún sin asignar -->
```
