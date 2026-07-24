---
name: "speckit-clis"
description: "Configura CLIs genéricos de IA en .specify/models.json: registra, edita, verifica y da de baja cualquier CLI del inventario."
argument-hint: "registrar | editar | verificar | dar-de-baja [nombre]"
metadata:
  author: "gen_speckit"
user-invocable: true
---

## Objetivo

Administrar entradas individuales de `.specify/models.json` sin regenerar el inventario
completo. Esta skill trabaja sobre un CLI a la vez y respeta las ediciones manuales del
usuario.

## REGISTRAR

1. **Pedir al usuario**:
   - `nombre`: kebab-case (`^[a-z][a-z0-9-]*$`).
   - `headless`: plantilla de invocación headless que contenga el placeholder `{prompt}`.
     Si se declaran más de un modelo, la plantilla debe contener `{modelo}` o aceptar el
     default `--model`.
   - `modelos`: array de al menos uno. Cada modelo necesita:
     - `id`: único dentro del CLI.
     - `capacidad`: entero 1–10.
     - `costo`: entero 1–3.
     - `contexto_k`: ventana de contexto en miles de tokens (entero) o `"desconocido"`.
   - Opcionalmente `patrones_cuota`: lista de expresiones regulares válidas.
   - Opcionalmente `version_cmd`: comando para consultar la versión.

2. **Mostrar resumen** con todos los valores antes de ejecutar.

3. **Ejecutar**:

   ```bash
   python .specify/scripts/python/clis_config.py \
     --accion agregar \
     --models-path ".specify/models.json" \
     --cli "<nombre>" \
     --headless "<plantilla>" \
     --modelos '[{"id":"<id>","capacidad":<1-10>,"costo":<1-3>,"contexto_k":<entero en miles de tokens o "desconocido">}]' \
     [--patrones-cuota "<regex>" ...] \
     [--version-cmd "<comando>"]
   ```

4. Si el script rechaza la definición, **mostrar los mensajes de validación tal cual**
   aparecen en el error (lista de problemas V1–V6) y no modificar el inventario.

## EDITAR

1. **Pedir al usuario** el nombre del CLI existente.
2. **Pedir solo los campos que quiere cambiar**. No enviar los campos que no se tocan.
3. **Ejecutar** con `--accion editar` pasando únicamente los campos modificados:

   ```bash
   python .specify/scripts/python/clis_config.py \
     --accion editar \
     --models-path ".specify/models.json" \
     --cli "<nombre>" \
     [--headless "<nueva plantilla>"] \
     [--modelos '[{"id":"...","capacidad":...,"costo":...,"contexto_k":...}]'] \
     [--patrones-cuota "..."] \
     [--version-cmd "..."]
   ```

4. El script valida el resultado final con las mismas reglas que el alta. Si falla,
   mostrar el error tal cual y dejar el inventario sin cambios.

## DAR DE BAJA

1. **Obtener las advertencias** de etiquetas `[M:<nombre>/...]` activas en
   `specs/*/tasks.md`. El script expone esta información mediante
   `get_active_cli_task_labels`; por ejemplo:

   ```bash
   python -c "import importlib.util as u, pathlib; s=u.spec_from_file_location('cc', '.specify/scripts/python/clis_config.py'); m=u.module_from_spec(s); s.loader.exec_module(m); print(m.get_active_cli_task_labels('.specify/models.json', '<nombre>'))"
   ```

2. **Mostrar cada tarea activa** (archivo, línea y texto) al usuario. Si no hay
   advertencias, indicarlo.

3. **Pedir confirmación explícita**: el usuario debe responder afirmativamente; sin
   confirmación no se ejecuta la baja.

4. **Recién entonces ejecutar**:

   ```bash
   python .specify/scripts/python/clis_config.py \
     --accion eliminar \
     --models-path ".specify/models.json" \
     --cli "<nombre>" \
     --confirmado
   ```

5. **Efecto**:
   - Si el CLI es de `origen: catalogo`, queda marcado como `deshabilitado: true`
     (el catálogo es inmutable; eliminarlo haría que el próximo escaneo lo recree).
   - Si el CLI es de `origen: registrado`, se elimina del inventario.

## VERIFICAR

1. **Pedir al usuario** el nombre del CLI a verificar (debe existir en
   `.specify/models.json`).

2. **Ejecutar primero sin prueba real** para mostrar el diagnóstico por niveles:

   ```bash
   python .specify/scripts/python/clis_config.py \
     --accion verificar \
     --models-path ".specify/models.json" \
     --cli "<nombre>"
   ```

   Interpretar el resultado:
   - **Nivel a**: resolución del ejecutable (`ok` / `fallo`).
   - **Nivel b**: autenticación detectable por hints del SO (`ok` / `fallo` /
     `ok` sin verificación).
   - **Nivel c**: invocación de prueba real. Por defecto queda **omitido**
     para no gastar cuota.

3. **Si el nivel c está omitido**, explicar al usuario que ese nivel **consume
   UNA llamada del CLI** y solo se ejecuta si lo aprueba explícitamente. Antes
   de ejecutarlo, **mostrar el comando exacto** que se usará: reemplazar en la
   plantilla `headless` del CLI el primer modelo disponible y el prompt
   `'responde solo: ok'`. Pedir confirmación explícita.

4. **Si el usuario aprueba**, repetir con `--aprobar-prueba`:

   ```bash
   python .specify/scripts/python/clis_config.py \
     --accion verificar \
     --models-path ".specify/models.json" \
     --cli "<nombre>" \
     --aprobar-prueba
   ```

   El diagnóstico del nivel c mostrará el comando renderizado, la clasificación
   (`exito` / `fallo` / `cuota`), el código de salida y la latencia en segundos.

5. **Efecto en el inventario**: el script actualiza **solo los campos
   detectables** (`instalado`, `autenticado`, `version`). Los campos del usuario
   (`headless`, `modelos`, `patrones_cuota`, `plan`, `cuota`, etc.) quedan
   intactos.

## MODELOS Y AGENTE PREFERIDO

### Deshabilitar un modelo

1. **Obtener las advertencias** de tareas pendientes que etiquetan ese modelo:

   ```bash
   python -c "import importlib.util as u, pathlib; s=u.spec_from_file_location('cc', '.specify/scripts/python/clis_config.py'); m=u.module_from_spec(s); s.loader.exec_module(m); print(m.get_active_cli_task_labels('.specify/models.json', '<nombre>'))"
   ```

   Mostrar al usuario cualquier tarea pendiente (`[ ]`) que contenga `[M:<nombre>/<modelo_id>]`.
   Advertir: "Estas tareas se reasignaran al despachar (se excluira este modelo
   del reparto)".

2. **Ejecutar**:

   ```bash
   python .specify/scripts/python/clis_config.py \
     --accion modelo-deshabilitar \
     --models-path ".specify/models.json" \
     --cli "<nombre>" \
     --modelo "<modelo_id>"
   ```

3. **Efecto**: el modelo queda marcado con `deshabilitado: true` en `modelos[]`;
   no aparecera en asignaciones ni en fallbacks de fases o tareas.

### Habilitar un modelo

1. **Ejecutar**:

   ```bash
   python .specify/scripts/python/clis_config.py \
     --accion modelo-habilitar \
     --models-path ".specify/models.json" \
     --cli "<nombre>" \
     --modelo "<modelo_id>"
   ```

2. **Efecto**: el modelo vuelve a participar en asignaciones y fallbacks.

### Fijar agente preferido

1. **Advertencias**:
   - Si el CLI esta deshabilitado (`deshabilitado: true` a nivel CLI): advertir
     "El CLI preferido esta deshabilitado; solo el agente principal ejecutara fases".
   - Si el CLI no tiene modelos habilitados: advertir "El CLI preferido no tiene
     modelos habilitados; solo el agente principal ejecutara fases".

2. **Ejecutar**:

   ```bash
   python .specify/scripts/python/clis_config.py \
     --accion preferido-fijar \
     --models-path ".specify/models.json" \
     --cli "<nombre>"
   ```

3. **Efecto**: el campo raiz `preferido` se establece a `<nombre>`; el reparto de
   fases y tareas se restringe a los modelos habilitados de ese agente.

### Quitar agente preferido

1. **Ejecutar**:

   ```bash
   python .specify/scripts/python/clis_config.py \
     --accion preferido-quitar \
     --models-path ".specify/models.json"
   ```

2. **Efecto**: se elimina el campo `preferido`; el reparto vuelve al modo sin
   restriccion (todos los CLIs y modelos habilitados son candidatos).

## Reglas

- Las ediciones manuales del usuario en `.specify/models.json` siempre prevalecen; no
  sobrescribir campos que no se estén modificando.
- Los campos `deshabilitado` (nivel modelo) y `preferido` (nivel raiz) son de
  control del usuario: nunca se generan, modifican ni borran por procesos
  automáticos (escaneo, ranking, merge). Un re-scan de modelos nunca toca
  estos campos, aunque actualice la lista de modelos disponibles.
- La baja **jamás** borra o deshabilita sin confirmación explícita del usuario.
- Estas operaciones **no gastan cuota**: solo leen/escriben `.specify/models.json` y
  escanean `tasks.md`.
