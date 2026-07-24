# Quickstart: validación del despacho multi-modelo de fases

**Feature**: `008-multi-model-phase-dispatch`

## Prerequisitos

- Python ≥3.11 y `pytest` (`python -m pytest tests/python -q` debe pasar en limpio
  antes de empezar).
- `.specify/models.json` válido con ≥2 CLIs instalados y autenticados.
- Los CLIs de IA instalados solo hacen falta para el Escenario 5 (end-to-end real);
  los demás usan mocks/archivos.

## Escenario 1 — `--prompt-file` (US1, contrato prompt-file.md)

```powershell
# Crear un prompt de prueba largo (>9000 chars, con | < > y saltos de línea)
# en un archivo dentro del repo y despachar:
python .specify/scripts/python/invoke_secondary.py --cli kimi --model kimi-for-coding `
  --prompt-file specs/008-multi-model-phase-dispatch/.phase-dispatch/smoke.prompt.md `
  --models-path .specify/models.json --log-dir specs/008-multi-model-phase-dispatch/orchestration-logs `
  --log-base-name smoke
```

**Esperado**: el comando generado contiene solo el puntero corto (< 500 chars), el
JSON de salida trae `promptFile` con la ruta, y el secundario reporta haber leído el
archivo. Errores: ambos flags → exit 2; archivo fuera del repo → exit 2.

## Escenario 2 — Deshabilitar un modelo y verificar exclusión (US2, FR-008a)

```powershell
python .specify/scripts/python/clis_config.py --accion modelo-deshabilitar `
  --cli claude --modelo haiku --models-path .specify/models.json
python .specify/scripts/python/scan_models.py --json   # re-scan
```

**Esperado**: `claude/haiku` desaparece de `asignacion.*` y `asignacion_por_fase.*`;
el flag `deshabilitado: true` sobrevive al re-scan (merge por-id); `modelo-habilitar`
lo restituye.

## Escenario 3 — Agente preferido (FR-008b)

```powershell
python .specify/scripts/python/clis_config.py --accion preferido-fijar `
  --cli kimi --models-path .specify/models.json
python .specify/scripts/python/phase_candidates.py --fase plan `
  --models-path .specify/models.json --principal claude/fable
```

**Esperado**: los candidatos devueltos son solo modelos habilitados de `kimi`;
`preferido-quitar` restituye el reparto completo. Con el agente preferido sin cuota,
la lista queda vacía (⇒ fase al principal).

## Escenario 4 — Despacho de una fase con verificación (US1, contrato phase-dispatch.md)

Con una feature de juguete (spec mínimo), ejecutar el playbook
`.specify/orchestrator/dispatch-phase.md` para la fase `checklist`:

1. El principal escribe `.phase-dispatch/checklist.prompt.md` y despacha con
   `--prompt-file` al modelo asignado.
2. Verificar: existe `checklists/<nombre>.md` con ≥1 ítem checkbox (nivel 1) y es
   coherente con el spec (nivel 2).
3. La tabla "Modelos por fase" registra `Efectivo` + `ejecutada`; Eventos registra el
   despacho.

**Esperado (fallo inducido)**: si el artefacto vuelve sin secciones obligatorias, se
observa el ciclo: reintento con motivo → escalada → principal en sesión; el pipeline
nunca continúa sobre artefacto inválido.

## Escenario 5 — Pipeline end-to-end con reparto real (SC-001, SC-004)

Correr `/speckit-specify-auto "<idea simple de prueba>"` con inventario válido.

**Esperado**: ≥50% de las fases no interactivas ejecutadas por modelos distintos del
principal (SC-001, verificable en la tabla del reporte + logs `fase-*.intento1.*`);
Métricas incluye desglose de fases por modelo y % económico del trabajo total; con
una interrupción a mitad del pipeline, el retome despacha solo las fases `pendiente`
(SC-005).

## Escenario 6 — Modo clásico intacto (FR-013, Constitución I)

Renombrar temporalmente `.specify/models.json` y correr el pipeline.

**Esperado**: todas las fases en el principal, sin errores nuevos, comportamiento
idéntico al actual; `test_no_regression.py` sigue pasando.

## Tests

```powershell
python -m pytest tests/python -q
```

Nuevos: `test_prompt_file.py`, `test_phase_candidates.py`,
`test_modelo_deshabilitado.py`; ampliados: `test_invoke_secondary.py`,
`test_scan_models.py`, `test_clis_config.py`. Todos los existentes deben seguir
pasando sin modificación de asserts (cambios aditivos).
