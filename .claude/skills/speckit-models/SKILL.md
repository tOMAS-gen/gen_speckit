---
name: "speckit-models"
description: "Genera el inventario multi-CLI (.specify/models.json): detecta CLIs instalados (claude/codex/kimi), modelos, modo headless y autenticación; pide al usuario lo no detectable (plan, cuotas) y arma el ranking de asignación por complejidad. Usar cuando el usuario invoca /speckit-models o cuando un pipeline multi-CLI necesita el inventario y no existe."
argument-hint: "[--force] [--probe-auth] [--probe-models]"
compatibility: "Requiere estructura .specify/ de spec-kit y Python 3.11+"
metadata:
  author: "gen_speckit"
user-invocable: true
disable-model-invocation: false
---

## Objetivo

Producir/actualizar `.specify/models.json` — la fuente de verdad del sistema multi-CLI
— combinando detección automática con declaración del usuario. Las correcciones
manuales del usuario SIEMPRE prevalecen (FR-004).

## Pasos

1. **Ejecutar el escaneo**:

   ```bash
   python .specify/scripts/python/scan_models.py --json
   ```

   Flags que el usuario puede pasar: `--force` (pisar ediciones manuales, solo si lo
   pidió explícitamente), `--probe-auth` (verificar autenticación con una invocación
   real mínima — consume una llamada por CLI).

   El escaneo además **descubre los modelos reales** de cada CLI (feature 006): usa el
   mecanismo de listado del catálogo (`modelos_cmd`) y los archivos de configuración
   locales (`config_hints`), marcando cada modelo con `origen`
   (`detectado-local` | `semilla`) y sus `esfuerzos` cuando el CLI los expone. Flag
   `--probe-models`: habilita mecanismos que consumen una llamada (opt-in).

   El mismo comando **enriquece cada modelo** con su nivel medido contra el leaderboard
   público (feature 007): agrega `capacidad`, `nivel_origen` (`medido`/`estimado`/`manual`)
   y `clasificacion` (entrada, rating, fecha publicada). Es best-effort: si la fuente
   externa falla, el escaneo sigue sin romperse. La salida `--json` puede incluir la
   clave `AMBIGUOS` con casos que necesitan confirmación del usuario.

   Si la salida JSON indica `"estado": "omitida"` con `"motivo": "fuente-invalida"`
   (el mecanismo propio no pudo obtener datos, a diferencia de `"sin-red"` que es una
   prohibición explícita del usuario), podés usar la navegación web como respaldo:

   - Consultar `https://arena.ai/leaderboard/text` (o
     `https://arena.ai/leaderboard/text/<categoría>` si aplica; las categorías
     específicas son `coding`, `math`, `creative_writing`, `instruction_following` y
     `multi_turn`) con WebFetch/WebSearch.
   - Extraer las filas visibles: `model_name`, `organization`, `rating`, `vote_count` y
     `leaderboard_publish_date`.
   - Armar un archivo JSON temporal con esta forma:

     ```json
     {"rows": [{"row": {"model_name": "...", "organization": "...", "rating": ..., "vote_count": ..., "leaderboard_publish_date": "..."}}, ...]}
     ```

   - Guardarlo en el directorio de scratchpad de la sesión y volver a correr:

     ```bash
     python .specify/scripts/python/classify_models.py --desde-agente RUTA_DEL_ARCHIVO --json
     ```

     El script normalizará y validará esas filas con las mismas reglas que los datos de
     la API: descartar filas incompletas, filtrar por votos mínimos y ordenar por rating.

   Este camino de respaldo es opcional: si no tenés acceso web en esta sesión o preferís
   no usarlo, el comando ya terminó con éxito (`exit 0`, estado `"omitida"`) y el flujo
   normal de la skill puede continuar sin clasificación nueva, usando lo que ya haya en
   el almacén o sin clasificación en absoluto. El comando NUNCA queda en estado de error
   por esto: tanto el camino automático como el de respaldo terminan con éxito; la única
   diferencia es si se obtiene clasificación nueva o no.

2. **Resolver el alcance global/local de la clasificación**:

   ```bash
   python .specify/scripts/python/classify_models.py --json
   ```

   Leer la salida JSON. Si la clave `preguntar_global` es `true`, es la primera
   vez que se obtiene la clasificación en esta máquina: preguntar al usuario
   **una sola vez** si quiere guardarla de forma global (compartida entre todos
   los proyectos de esta máquina).

   Al preguntar, explicar brevemente qué se comparte:
   - clasificación cacheada de modelos,
   - mapeos confirmados entre modelos del inventario y entradas del leaderboard,
   - plan/suscripción contratado por CLI.

   Y qué **NO** se comparte (FR-016):
   - rutas del proyecto,
   - credenciales o tokens,
   - estado de cuota vigente.

   Según la respuesta, volver a correr el comando para fijar la decisión sin
   volver a preguntar en el futuro:

   ```bash
   # Si acepta guardar globalmente:
   python .specify/scripts/python/classify_models.py --global si --json
   # Si prefiere solo local:
   python .specify/scripts/python/classify_models.py --global no --json
   ```

   Si `preguntar_global` es `false`, respetar la decisión guardada y continuar.

3. **Verificación oficial (best-effort, la hace el agente)**: por cada CLI del
   inventario con `fuentes_oficiales` en `.specify/clis-catalog.json`:
   - Consultar esas URLs (WebFetch/WebSearch) y extraer qué modelos publica el
     proveedor para ese CLI.
   - Cruzar con el inventario: un modelo publicado que NO esté detectado ni sembrado se
     **propone como alta** con `origen: "oficial-sin-confirmar"` y `capacidad`/`costo`
     sugeridos (marcarlos como propuesta corregible al presentar). Los ya detectados no
     cambian. NUNCA borrar modelos por ausencia oficial (el usuario decide).
   - Registrar en `clis.<cli>.verificacion_web`: `{"estado": "hecha", "fecha":
     "YYYY-MM-DD", "fuentes": [urls]}`. **Sin acceso web o fuente caída**: dejar
     `{"estado": "omitida"}` y seguir sin fallar.
   - Los modelos `oficial-sin-confirmar` **entran al ranking como cualquier otro**
     (decisión de diseño): si al despachar no están disponibles, el fallback del
     orquestador escala solo.

4. **Leer el resultado** (`.specify/models.json`) y detectar qué quedó `"desconocido"`:
   `plan`, `cuota`, `autenticado`, `contexto_k`.

5. **Preguntar al usuario SOLO lo no detectable**, en una sola tanda:

   Antes de las preguntas habituales, **resolver los casos ambiguos** que traiga la salida
   `--json` bajo la clave `AMBIGUOS`: para cada `ref` (`cli/modelo`) presentarle los
   `candidatos` y dejar que elija uno, o ninguno si ninguno corresponde. Persistir cada
   elección con `guardar_mapeo_elegido` para no volver a preguntarla:

   ```bash
   # Obtener la ruta del almacén global:
   python -c "import importlib.util; spec=importlib.util.spec_from_file_location('cm','.specify/scripts/python/classify_models.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print(m._global_path())"
   # Guardar la elección (reemplazar RUTA, CLI/MODELO y NOMBRE_ELEGIDO):
   python -c "import importlib.util; spec=importlib.util.spec_from_file_location('cm','.specify/scripts/python/classify_models.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.guardar_mapeo_elegido('RUTA', 'CLI/MODELO', 'NOMBRE_ELEGIDO')"
   ```

   Si el usuario elige "ninguno", pasar `None` como `NOMBRE_ELEGIDO` para recordar la
   decisión.

   Antes de preguntar el plan contratado de cada CLI, consultar si el almacén de
   la máquina ya tiene uno heredado:

   ```bash
   # Obtener la ruta del almacén global:
   python -c "import importlib.util; spec=importlib.util.spec_from_file_location('cm','.specify/scripts/python/classify_models.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print(m._global_path())"
   # Resolver planes heredados (reemplazar RUTA y el JSON de planes_locales):
   python -c "import importlib.util, json; spec=importlib.util.spec_from_file_location('cm','.specify/scripts/python/classify_models.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print(json.dumps(m.planes_heredados('RUTA', json.loads('PLANES_LOCALES_JSON')), ensure_ascii=False))"
   ```

   Para cada CLI, si `fuente` es `"global"`, mostrar el plan como **dato heredado
   del almacén de la máquina** en lugar de preguntar de nuevo. Permitir que el
   usuario lo corrija si no es correcto; si corrige, persistir la corrección con
   `guardar_plan_corregido` para que sobreviva en la máquina:

   ```bash
   # Reemplazar RUTA, CLI y PLAN_NUEVO:
   python -c "import importlib.util; spec=importlib.util.spec_from_file_location('cm','.specify/scripts/python/classify_models.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.guardar_plan_corregido('RUTA', 'CLI', 'PLAN_NUEVO')"
   ```

   Si `fuente` es `"ninguna"` o `"local"`, seguir con la pregunta habitual.

   Luego, en la misma tanda:
   - Plan contratado por CLI instalado (ej. "Claude Max 5x", "Kimi free").
   - Estado de cuota si lo conoce (`ok` / `agotada`).
   - Correcciones de capacidad/costo si no está de acuerdo con la siembra.
     Si corrige la capacidad de un modelo que ya tiene `clasificacion` (dato medido),
     **informar la discrepancia** entre el valor manual y el medido, aclarar que la
     corrección manual prevalece y no sobrescribir automáticamente.

   Lo que el usuario no sepa queda `"desconocido"` — NUNCA inventar valores.

6. **Aplicar las respuestas** editando `.specify/models.json` (mantener UTF-8 sin BOM,
   indentación 2). No tocar campos que el usuario no mencionó.

7. **Validar contra el contrato** (`specs/001-multi-cli-orchestrator/contracts/models-schema.md`):
   - Toda referencia `cli/modelo` de `asignacion` existe en `clis.<cli>.modelos`.
   - Ningún CLI instalado y autenticado queda fuera de todas las listas (Constitución IV).
   - JSON parseable.

   Si algo falla, corregirlo antes de terminar.

8. **Mostrar resumen**: tabla CLI → instalado/versión/autenticado/plan/cuota, los modelos con su **origen**, **esfuerzos** y **nivel_origen** (`medido`/`estimado`/`manual`), el estado de la verificación web, y el ranking `asignacion` por nivel. Para los modelos con `clasificacion`, incluir la entrada del leaderboard, el rating y la fecha de publicación. Para el plan de cada CLI, indicar también su origen: `heredado` (del almacén de la máquina), `local` (declarado en este proyecto) o `desconocido`. Recordar al usuario que puede corregir el archivo a mano y que sus ediciones sobreviven futuras re-ejecuciones.

## Reglas

- Este comando es el ÚNICO que regenera el inventario completo. El resto del sistema
  solo escribe los campos de cuota vía `update_quota.py`.
- Re-ejecución: el script compara contra `.specify/models.scan.json` y preserva las
  ediciones del usuario automáticamente; ante conflicto irresoluble, preguntar.
- Si un CLI está instalado pero no autenticado, avisar al usuario cómo autenticarlo
  (login interactivo del propio CLI) — no intentar autenticar por él.
