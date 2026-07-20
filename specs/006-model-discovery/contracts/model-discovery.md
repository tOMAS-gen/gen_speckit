# Contrato: descubrimiento y verificación de modelos

**Feature**: 006-model-discovery

## Script (`scan_models.py`) — interfaz extendida

| Flag nuevo | Comportamiento |
|---|---|
| `--probe-models` | Habilita mecanismos que consumen llamada/cuota (`modelos_cmd_consume: true` y sondeo mínimo). Sin el flag, solo detección gratuita. |

Comportamiento nuevo del escaneo (aditivo):

1. Por cada CLI instalado: `detect_models(cli)` según la cadena del data-model
   (`modelos_cmd` → `config_hints` → semillas). Salida: lista de modelos con `origen` y
   `esfuerzos` cuando se conozcan.
2. `models.json` resultante: cada modelo con `origen`; CLI con `verificacion_web`
   (estado `omitida` si el script corre solo — la marca `hecha` la aplica la skill).
3. Parseo tolerante: config ausente/corrupta o salida no parseable → continuar con el
   siguiente eslabón de la cadena, avisando; **nunca** abortar el escaneo por esto.

## Skill (`speckit-models`) — flujo extendido

1. Correr el script (como hoy).
2. **Verificación oficial (agente, best-effort)**: por cada CLI con `fuentes_oficiales`
   en el catálogo, consultar las URLs; cruzar modelos publicados vs. inventario;
   proponer altas `oficial-sin-confirmar` (con `capacidad`/`costo` sugeridos y
   marcados como propuesta corregible); registrar `verificacion_web` (hecha + fecha +
   fuentes). Sin red → registrar `omitida` y seguir.
3. Presentar al usuario la tabla por CLI con **origen y esfuerzos** de cada modelo, y
   recordar que sus correcciones manuales prevalecen.

## Notas de implementación (ajustes de implement)

- Id plausible de modelo: además del shape, debe contener **un dígito o un guion**
  (anti-ruido: excluye claves como `lastusedat`/`usagecount` de los configs).
- Extracción de config: bajo una clave que contiene "model" se toman solo las claves
  **inmediatas** como ids (un nivel); los campos internos no son modelos. Si la entrada
  declara una clave con "effort", se captura como `esfuerzos`.
- Matching semilla↔detectado: **exacto primero**, substring como respaldo sobre
  candidatos libres (evita que `kimi-for-coding` capture `...-highspeed`).
- Detectado sin semilla: se agrega con `capacidad 5` / `costo 2` (propuesta corregible).

## Invariantes

- Contrato vigente intacto: consumidores actuales (asignador, orquestador,
  invoke_secondary, update_quota) funcionan sin cambios (SC-005).
- 0 modelos inventados: `origen` ∈ {detectado-local, semilla, oficial-sin-confirmar}.
- Ranking sin filtro por origen (decisión del usuario).
- Sin consumo de cuota por defecto; `--probe-models` es la única puerta.
