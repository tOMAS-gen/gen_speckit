# Quickstart / Validación: Descubrimiento y verificación de modelos

**Feature**: 006-model-discovery | **Fecha**: 2026-07-18

## Escenario 1 — Detección local real (US1, SC-001/SC-002)
```bash
python .specify/scripts/python/scan_models.py --json
```
**Esperado**: los modelos de CLIs con `config_hints`/`modelos_cmd` reflejan lo real de la
máquina; cada modelo tiene `origen`; 0 inventados.

## Escenario 2 — CLI sin mecanismo de listado (edge)
CLI instalado sin `modelos_cmd` ni `config_hints` útiles → sus modelos quedan
`origen: semilla`. El escaneo no falla.

## Escenario 3 — Verificación oficial vía skill (US2, SC-004)
Correr `/speckit-models` con un agente con acceso web: los modelos publicados no
detectados aparecen `oficial-sin-confirmar` y el CLI registra `verificacion_web: hecha`.
Sin red: `verificacion_web: omitida`, sin error.

## Escenario 4 — Esfuerzos y merge (US3, SC-003)
Modelo con niveles expuestos → `esfuerzos` registrado. Editar a mano `esfuerzos` o
`capacidad`, re-escanear → la edición sobrevive.

## Escenario 5 — Contrato aditivo (SC-005)
```bash
uv run --no-project --with dist/*.whl --with pytest python -m pytest tests/python/ -q
```
**Esperado**: suite completa verde (consumidores actuales intactos) + tests nuevos de
detección/orígenes.

## Escenario 6 — Ranking con todos los orígenes (Clarifications)
Un modelo `oficial-sin-confirmar` con capacidad alta aparece en `asignacion` — y si al
despachar no está disponible, el orquestador clasifica `indisponible` y escala.

## Criterios de aceptación
- [ ] E1 detección real con origen (SC-001/002)
- [ ] E2 fallback a semillas sin fallar
- [ ] E3 verificación oficial best-effort (SC-004)
- [ ] E4 esfuerzos + merge manual (SC-003)
- [ ] E5 contrato aditivo, suite verde (SC-005)
- [ ] E6 ranking sin filtro por origen
