# Contract: despacho de fase (`dispatch-phase.md` + archivos de trabajo)

**Feature**: `008-multi-model-phase-dispatch`

Contrato entre el playbook `.specify/orchestrator/dispatch-phase.md` (lo ejecuta el
principal) y los secundarios que producen artefactos de fase.

## Entrada del despacho

| Elemento | Fuente |
|---|---|
| Fase a ejecutar | pipeline (specify, plan, checklist, tasks, analyze, clarify-A/B, analyze-A/B) |
| Modelo asignado | tabla "Modelos por fase" del reporte (editable por el usuario — prevalece) |
| Candidatos de fallback | `phase_candidates.py` (ranking ∩ habilitados ∩ preferido ∩ cuota) |
| Instrucciones | `specs/<feature>/.phase-dispatch/<fase>.prompt.md` escrito por el principal |

## Estructura del prompt de fase (`<fase>.prompt.md`)

1. **Identificación**: feature, fase, artefacto(s) a producir con ruta exacta.
2. **Instrucciones de la fase**: el CUERPO de la skill base correspondiente
   (speckit-specify, speckit-plan, ...) adaptado a ejecución headless: sin pasos
   interactivos, sin hooks, sin escritura de estado del pipeline.
3. **Contexto por referencia**: rutas de los artefactos previos (spec.md, plan.md,
   constitution.md, templates) — el secundario los lee del disco; NUNCA contenido
   pegado (regla existente de headless-adapters).
4. **Restricciones**: operar solo dentro del repo; escribir SOLO el/los artefactos
   declarados en (1); NO tocar `tasks.md` (checkboxes), reporte, `models.json` ni
   `feature.json`; reportar al final la lista de archivos escritos.

## Invocación

```
python .specify/scripts/python/invoke_secondary.py \
  --cli <cli> --model <modelo> \
  --prompt-file specs/<feature>/.phase-dispatch/<fase>.prompt.md \
  --models-path .specify/models.json \
  --log-dir specs/<feature>/orchestration-logs \
  --log-base-name fase-<fase>
```

- El principal NUNCA se auto-invoca: si el modelo resuelto es el principal, la fase
  se ejecuta en sesión y la tabla registra `Efectivo = principal`.
- Clasificación de resultado: la existente (`exito | cuota_agotada | indisponible`).

## Verificación del principal (obligatoria antes de `ejecutada`)

**Nivel 1 — estructural**: el artefacto declarado existe y contiene las secciones
obligatorias de su template:

| Fase | Artefacto | Secciones obligatorias |
|---|---|---|
| specify | `spec.md` | `## User Scenarios & Testing`, `## Requirements`, `## Success Criteria` |
| plan | `plan.md` (+ research/data-model/contracts/quickstart según la skill decida) | `## Summary`, `## Technical Context`, `## Constitution Check`, `## Project Structure` |
| checklist | `checklists/<nombre>.md` | título `# Checklist:` + ≥1 ítem `- [ ]`/`- [x]` |
| tasks | `tasks.md` | `# Tasks:`, ≥1 línea `- [ ] T### ...` con formato oficial |
| analyze (A) | `.phase-dispatch/analyze.questions.md` | hallazgos con severidad por ítem |
| clarify (A) | `.phase-dispatch/clarify.questions.md` | ≤5 preguntas, cada una con opciones o formato de respuesta corta |
| clarify/analyze (B) | artefacto de la fase actualizado | `## Clarifications` con sesión del día (clarify) / correcciones aplicadas (analyze) |

**Nivel 2 — de contenido**: el principal lee el artefacto y confirma coherencia con
la entrada de la fase (idea/spec/plan previos). No re-ejecuta la fase; busca
incoherencia grosera (tema equivocado, secciones vacías, contradicciones con
decisiones ya tomadas).

## Ciclo de recuperación (FR-003)

```
falla verificación → 1 reintento MISMO modelo (prompt + motivo del rechazo)
                   → 1 escalada al siguiente candidato de MAYOR capacidad
                   → el principal ejecuta la fase en sesión
```

- `cuota_agotada` en cualquier punto: `update_quota.py --estado agotada`, siguiente
  candidato de la lista, evento registrado. Sin candidatos → principal en sesión.
- El pipeline NUNCA continúa sobre un artefacto no verificado y NUNCA queda
  bloqueado por el reparto de fases.

## Escritura de estado (solo el principal)

- Tabla "Modelos por fase": `Efectivo` + `Estado` al cerrar cada fase.
- Eventos: cada despacho, reintento, escalada, reasignación por cuota, caída al
  principal, y toda restricción activa del usuario (`preferido`, deshabilitados).
- Métricas al cierre del pipeline: desglose fases-por-modelo y % del trabajo total
  (fases + tareas) ejecutado por modelos económicos (costo < 3).

## Invariantes

- I1: un secundario nunca escribe `tasks.md`, el reporte, `models.json` ni
  `feature.json`.
- I2: el artefacto final de cada fase es el oficial de spec-kit; `.phase-dispatch/`
  contiene solo intermedios.
- I3: toda fila `ejecutada` tiene `Efectivo` no vacío y pasó ambos niveles de
  verificación.
- I4: con inventario ausente/inválido el playbook no se ejecuta (modo clásico,
  FR-013).
