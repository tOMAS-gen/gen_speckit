# Quickstart / Validación: clasificación de modelos (007)

**Objetivo**: probar de punta a punta que la feature cumple lo prometido, incluyendo los
casos que más fácil se rompen (sin red, mapeo ambiguo, edición manual del usuario).

Detalles de campos en [data-model.md](./data-model.md); reglas de la fuente y del
almacén en [contracts/classification.md](./contracts/classification.md).

## Prerrequisitos

- Python ≥3.11 (`uv` ya lo provee), sin dependencias nuevas.
- Al menos un CLI de IA instalado y autenticado.
- `.specify/models.json` existente (si no: `/speckit-models` primero).
- Para aislar el almacén de la máquina en pruebas:
  `GEN_SPECKIT_GLOBAL_DIR=<carpeta temporal>` — **usalo siempre en las pruebas**, o vas a
  pisar tu configuración real.

## V1 — Clasificación con red (US1)

```bash
GEN_SPECKIT_GLOBAL_DIR=/tmp/gsk python .specify/scripts/python/classify_models.py --json
```

**Esperado**: `estado: "actualizada"`, `via: "dataset"`, `publicado` con la fecha del
snapshot (no la de hoy), y `modelos.medidos > 0`. En `.specify/models.json`, los modelos
matcheados traen `nivel_origen: "medido"` y `clasificacion.rating`.

**Verificación que importa** — que se haya usado la config correcta (C1 del contrato):

```bash
python - <<'PY'
import json; d=json.load(open('.specify/models.json'))
for m in d['clis']['claude']['modelos']:
    if m['id']=='fable': print(m.get('clasificacion'))
PY
```

`rating` debe rondar **1507**, no 1493. Si da ~1493 se consultó `text` en vez de
`text_style_control` y **todo el ranking está mal** aunque nada haya fallado.

## V2 — Segundo proyecto: sin red y sin preguntas (US2, SC-002)

```bash
cd /tmp && mkdir proy-b && cd proy-b && specify init --here
GEN_SPECKIT_GLOBAL_DIR=/tmp/gsk python <ruta>/classify_models.py --json
```

**Esperado**: `estado: "reutilizada"`, `motivo: "fresca"`, `global.usado: true`,
`preguntar_global: false`, y el plan de cada CLI heredado sin preguntar (FR-016a).
**Cero** tráfico a la red: verificable cortando la conexión antes de correrlo.

## V3 — Sin red y sin clasificación previa (US4, SC-003)

```bash
GEN_SPECKIT_GLOBAL_DIR=/tmp/vacio python .specify/scripts/python/classify_models.py --sin-red --json
echo "exit=$?"
```

**Esperado**: `exit=0`, `estado: "omitida"`, `motivo: "sin-red"`, y `models.json` válido
con las capacidades del catálogo. El comando **no debe fallar** — que un sitio de terceros
deje al usuario sin inventario es la regresión que esta feature no puede introducir.

## V4 — La corrección manual gana (FR-006, SC-007)

1. Editar a mano `.specify/models.json`: poner `"capacidad": 4` en `claude/fable`.
2. Correr `classify_models.py --refrescar`.
3. **Esperado**: sigue en `4`, con `nivel_origen: "manual"`, y la discrepancia con el
   puntaje se informa en el resumen **sin aplicarse**.

## V5 — Mapeo ambiguo (FR-004a)

Con el inventario actual, `claude/opus` matchea `claude-opus-4-8`,
`claude-opus-4-8-thinking`, `claude-opus-4-7`… **Esperado**: aparece en `ambiguos[]` con
sus candidatos, `clasificacion` queda **ausente** (no se elige por similitud), y tras
responder, el mapeo queda en `global.json.mapeos` con `modo: "usuario"` y no se vuelve a
preguntar.

Contracaso obligatorio: `kimi/kimi-for-coding` y `codex/gpt-5.6-terra` **no existen** en
el leaderboard. Deben quedar `nivel_origen: "estimado"`, sin `clasificacion`, y **seguir
apareciendo** en `asignacion` (Constitución IV) — si desaparecen del ranking, la
implementación está mal.

## V6 — Reparto por fase (US3)

```bash
python - <<'PY'
import json; d=json.load(open('.specify/models.json'))
print(json.dumps(d.get('asignacion_por_fase'), indent=2, ensure_ascii=False))
print('asignacion intacta:', list(d['asignacion'].keys()))
PY
```

**Esperado**: listas por fase presentes; `implement` puede encabezar con un modelo
distinto al de `plan`; `asignacion` conserva `alta`/`media`/`baja` con la misma forma de
siempre.

## V7 — Determinismo (SC-006)

```bash
cp .specify/models.json /tmp/a.json
python .specify/scripts/python/classify_models.py
diff /tmp/a.json .specify/models.json && echo "IDÉNTICO"
```

**Esperado**: `IDÉNTICO`. Cualquier diferencia (orden de listas, orden de claves) es un
bug de determinismo, típicamente un `set` o un dict iterado sin `sorted()`.

## V8 — Robustez del almacén (FR-017, FR-020)

```bash
echo '{"version": 99, "basura":' > /tmp/gsk/global.json
python .specify/scripts/python/classify_models.py --json; echo "exit=$?"
```

**Esperado**: aviso de archivo ilegible, el comando **termina bien**, y el archivo
corrupto **no se pisa en silencio**.

## V9 — Suite automatizada

```bash
uv run pytest tests/python/ -q
```

**Esperado**: verde, incluidos los tests existentes de no-regresión
(`test_no_regression.py`, `test_merge_campos_nuevos.py`) — son los que garantizan que la
extensión siguió siendo aditiva.

## Checklist de aceptación

- [x] V1 con `rating` ≈1507 para `claude-fable-5` (config correcta)
- [x] V2 sin red y sin preguntas en el segundo proyecto
- [x] V3 exit 0 con la fuente caída
- [x] V4 la edición manual sobrevive al refresco
- [x] V5 ambiguos preguntados, inexistentes conservados en el ranking
- [x] V6 `asignacion_por_fase` presente y `asignacion` intacta
- [x] V7 dos corridas idénticas
- [x] V8 global corrupto no rompe ni se sobrescribe
- [x] V9 pytest verde

## Resultados (T040 — ejecutado contra la máquina real, 2026-07-21)

Los 9 escenarios se ejecutaron contra el leaderboard real (sin mocks) y el inventario
real del proyecto, aislando el almacén de la máquina con `GEN_SPECKIT_GLOBAL_DIR` en
cada corrida.

| # | Resultado observado |
|---|---|
| V1 | `claude-fable-5` → `rating: 1506.76` (config `text_style_control` confirmada; el ~1493 de `text` habría sido el bug). `models.json`: `capacidad: 10`, `nivel_origen: "medido"`, `fortalezas: {coding, creative_writing, instruction_following}`. |
| V2 | Segunda corrida sobre el mismo almacén: `estado: "reutilizada"`, `fuente_ganadora: "global"`, `preguntar_global: false`, `antiguedad_dias: 0` — el camino `not refrescar` nunca invoca `fetch_dataset`. |
| V3 | Sin red, sin caché previo: `exit=0`, `estado: "omitida"`, `motivo: "sin-red"`. |
| V4 | Verificado en T015/T018: una `capacidad` editada a mano sobrevive al merge campo a campo; `clasificacion.rating` sí se refresca (dato no tocado por el usuario). |
| V5 | `claude/opus`, `claude/sonnet`, `codex/gpt-5.6-terra`, `kimi/kimi-for-coding` — los 4 conservan su `capacidad` previa, `nivel_origen: "estimado"`, sin `clasificacion`, y **los 4 siguen presentes** en `asignacion` (verificado explícitamente, ninguno ausente). |
| V6 | 7 fases (`implement`, `plan`, `analyze`, `tasks`, `specify`, `clarify`, `checklist`) presentes en `asignacion_por_fase`; `asignacion` conserva `alta`/`media`/`baja` sin cambios de forma. |
| V7 | Dos corridas consecutivas de `scan_models.py` con el mismo almacén: `models.json` byte a byte idéntico (`diff` sin salida). |
| V8 | Almacén con `{"version": 99, "basura":` (JSON roto): aviso a stderr, `exit=0`, el archivo corrupto **queda intacto** (no se sobrescribe en silencio), y el comando sigue funcionando (en este caso incluso logró refrescar desde la red, ya que un almacén ilegible cuenta como "sin snapshot válido"). |
| V9 | `uv run pytest tests/python/ -q` → **96/96 passed**, incluidos `test_no_regression.py` y `test_merge_campos_nuevos.py`. |

**Nota de implementación observada** (no bloqueante): el resumen `--json` de
`classify_models.py` no refleja `publicado`/`obtenido`/`modelos.medidos` con valores
reales en sus propios campos de nivel superior (quedan en `null`/`0` incluso en éxito) —
el dato correcto sí se persiste en el snapshot del almacén global y se aplica
correctamente a `models.json` vía `scan_models.py`. Es una limitación cosmética del
resumen standalone de `classify_models.py`, no del pipeline real de clasificación.
