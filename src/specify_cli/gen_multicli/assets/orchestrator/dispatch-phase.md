# Playbook: Despacho de una fase del pipeline

> Lógica portable (cualquier CLI principal la ejecuta). Entrada: una fase a ejecutar
> (specify, plan, checklist, tasks, analyze — o los medios despachos de clarify y
> analyze), la tabla "Modelos por fase" del reporte de la feature, y un
> `.specify/models.json` válido. El CLI que ejecuta este playbook es el **principal**:
> empaqueta, despacha, verifica y es el ÚNICO que escribe estado (tabla del reporte,
> Eventos). Los secundarios producen artefactos de fase y NUNCA tocan `tasks.md`
> (checkboxes), el reporte, `models.json` ni `feature.json`.
>
> Contrato de detalle: `specs/008-multi-model-phase-dispatch/contracts/phase-dispatch.md`.

## Paso 0 — Precondiciones y resolución del modelo

1. Sin `.specify/models.json` válido → NO ejecutar este playbook: la fase corre en el
   principal (modo clásico, FR-013). Igual si el usuario pidió modo clásico.
2. Leer la tabla "Modelos por fase" del reporte (`specs/<feature>/orchestration-report.md`).
   La fila de la fase da el **modelo asignado** (editable por el usuario — prevalece).
   Si la fase ya está `ejecutada` u `omitida`, no hay nada que hacer (retome).
3. Resolver los candidatos de fallback:

   ```
   python .specify/scripts/python/phase_candidates.py --fase <fase> \
       --models-path .specify/models.json --principal <cli/modelo-principal> \
       --nivel <alta|media|baja>
   ```

   - Nivel mínimo: `alta` para fases de criterio — **clarify, analyze y el paso de
     asignación de tasks** (FR-005a) — y el nivel que el triage decidió para el resto.
   - El script ya aplica: `asignacion_por_fase` si existe, exclusión de CLIs/modelos
     deshabilitados, restricción `preferido` y cuota. Si hay una restricción del
     usuario activa (`preferido`, deshabilitados), registrarla en Eventos la primera
     vez que aplica (FR-008b).
4. Si el modelo asignado no está entre los candidatos (deshabilitado, sin cuota,
   fuera del preferido), usar el primer candidato y registrar la reasignación.
5. **Si el modelo resuelto ES el principal** → ejecutar la fase en sesión (nunca
   auto-invocarse por headless) y saltar al Paso 4 con `Efectivo = principal`.
6. Lista de candidatos vacía → la fase la ejecuta el principal en sesión (el pipeline
   nunca queda bloqueado por el reparto de fases); registrar la causa en Eventos.

## Paso 1 — Empaquetar el prompt de fase

Escribir `specs/<feature>/.phase-dispatch/<fase>.prompt.md` con:

1. **Identificación**: feature, fase, y el/los artefactos a producir con ruta exacta.
2. **Instrucciones**: el cuerpo de la skill base de la fase (`speckit-specify`,
   `speckit-plan`, ...) adaptado a headless — sin pasos interactivos, sin hooks, sin
   escritura de estado del pipeline. Incluir la entrada de la fase (la idea, o las
   respuestas del usuario en un medio despacho B).
3. **Contexto por referencia**: rutas de los artefactos previos (spec.md, plan.md,
   `.specify/memory/constitution.md`, template de la fase) — el secundario los lee
   del disco; NUNCA pegar contenido completo.
4. **Restricciones**: operar solo dentro del repo; escribir SOLO los artefactos
   declarados; no tocar `tasks.md`, reporte, `models.json`, `feature.json`; reportar
   al final la lista de archivos escritos.

## Paso 2 — Despachar

```
python .specify/scripts/python/invoke_secondary.py --cli <cli> --model <modelo> \
    --prompt-file specs/<feature>/.phase-dispatch/<fase>.prompt.md \
    --models-path .specify/models.json \
    --log-dir specs/<feature>/orchestration-logs --log-base-name fase-<fase>
```

Interpretar `clasificacion` como siempre:

| Resultado | Acción |
|---|---|
| `exito` | Verificar (Paso 3) |
| `cuota_agotada` | `update_quota.py --cli <cli> --estado agotada`; siguiente candidato de la lista; evento; re-despachar. Sin candidatos → principal en sesión |
| `indisponible` | Igual pero SIN tocar el inventario |

## Paso 3 — Verificación del principal (obligatoria)

**Nivel 1 — estructural**: el artefacto existe y contiene las secciones obligatorias
de su template (tabla por fase en el contrato phase-dispatch.md; p. ej. spec.md exige
`## User Scenarios & Testing`, `## Requirements`, `## Success Criteria`).

**Nivel 2 — de contenido**: leer el artefacto y confirmar coherencia con la entrada
de la fase (tema correcto, secciones con contenido real, sin contradicciones con
decisiones ya tomadas). No re-ejecutar la fase.

Fallo en cualquiera de los dos niveles → ciclo acotado (FR-003):

```
1 reintento al MISMO modelo (prompt + motivo del rechazo)
  → 1 escalada al siguiente candidato de MAYOR capacidad
    → el principal ejecuta la fase en sesión
```

NUNCA continuar el pipeline sobre un artefacto no verificado.

## Fases con interacción: patrón de dos despachos (clarify, analyze)

- **Despacho A**: el secundario analiza y escribe
  `.phase-dispatch/<fase>.questions.md` (clarify: ≤5 preguntas con opciones; analyze:
  hallazgos con severidad). El principal lo verifica.
- **Conversación**: el principal presenta las preguntas/hallazgos al usuario en su
  sesión y escribe las respuestas en `.phase-dispatch/<fase>.answers.md`.
- **Despacho B**: el mismo modelo recibe las respuestas (referenciando el archivo) e
  integra los cambios en el artefacto de la fase (spec.md con `## Clarifications`,
  correcciones de analyze). El principal verifica de nuevo.

El trabajo analítico completo (incluida la integración) queda en el modelo asignado;
el principal solo conversa y verifica (FR-005). Sin preguntas/hallazgos → no hay
despacho B.

## Paso 4 — Cierre de la fase (solo el principal)

1. Tabla "Modelos por fase": columna `Efectivo` = modelo que realmente ejecutó
   (o `principal`), `Estado` = `ejecutada`.
2. Eventos: despacho, reintentos, escaladas, reasignaciones por cuota, caída al
   principal — cada uno con causa; las restricciones de configuración del usuario
   (`preferido`, modelos deshabilitados) registradas explícitamente como decisión
   del usuario según FR-008b.
3. Los intermedios quedan en `.phase-dispatch/` (auditables); el artefacto final de
   la fase es siempre el oficial de spec-kit.

## Retome

Al reanudar un pipeline: releer la tabla "Modelos por fase" y ejecutar solo las filas
`pendiente`, reutilizando los archivos de `.phase-dispatch/` existentes (un
`<fase>.questions.md` verificado no se re-genera; se continúa desde la conversación o
el despacho B).
