# Contract: campos nuevos del inventario (`.specify/models.json`)

**Feature**: `008-multi-model-phase-dispatch`

Extensión ADITIVA del esquema de la feature 001/003/007. Un `models.json` sin estos
campos sigue siendo válido y se comporta como hoy.

## 1. `clis.<cli>.modelos[].deshabilitado` (booleano, opcional)

- Ausente o `false` ⇒ el modelo participa normalmente.
- `true` ⇒ el modelo NO aparece en `asignacion`, `asignacion_por_fase` ni en la
  resolución de candidatos; no recibe despachos ni fallbacks de fases ni de tareas.
- Origen: SIEMPRE decisión del usuario (edición manual o skill `speckit-clis`).
  Ningún proceso automático lo escribe.
- Preservación: cubierto por el merge por-id de `modelos[]` — un re-scan nunca lo
  borra ni lo agrega.
- Relación con `clis.<cli>.deshabilitado` (nivel CLI, existente): el nivel CLI
  excluye todos los modelos del CLI; el nivel modelo es granular. Ambos pueden
  coexistir; la exclusión es la unión.

## 2. `preferido` (string, opcional, nivel raíz)

- Valor: clave existente de `clis` (ej. `"opencode"`). Valor inexistente ⇒ el
  consumidor lo ignora con advertencia (no rompe el inventario).
- Presente ⇒ el reparto de fases y tareas se restringe a los modelos habilitados de
  ese agente. El reporte DEBE registrar la restricción como decisión del usuario en
  Eventos la primera vez que aplica en un pipeline.
- Ausente ⇒ sin restricción (comportamiento actual).
- Escritura: usuario a mano o skill `speckit-clis` (acción "fijar/quitar preferido").
  El merge lo trata como valor escalar de usuario (prevalece ante re-scans).
- No modifica los rankings persistidos: `asignacion*` se calculan sin la
  preferencia; el filtro se aplica en la resolución de candidatos. Quitar la
  preferencia no requiere re-scan.

## 3. Operaciones nuevas de `clis_config.py`

```
--accion modelo-deshabilitar  --cli <cli> --modelo <id>
--accion modelo-habilitar     --cli <cli> --modelo <id>
--accion preferido-fijar      --cli <cli>
--accion preferido-quitar
```

Validaciones:
- V-M1: `<cli>` existe en el inventario; `<id>` existe en sus `modelos[]`.
- V-M2: `modelo-deshabilitar` advierte (sin bloquear) si el modelo aparece en
  etiquetas `[M:cli/modelo]` de tareas pendientes (reutiliza
  `get_active_cli_task_labels`).
- V-M3: `preferido-fijar` advierte si el CLI está deshabilitado o sin modelos
  habilitados.
- Salida JSON: `{ ok, cambios, advertencias[] }` — consistente con las acciones
  existentes.

## 4. Efecto sobre los rankings (`build_asignacion`, `build_asignacion_por_fase`)

- Ambas funciones excluyen modelos con `deshabilitado: true` (además del filtro
  existente por CLI deshabilitado/no instalado).
- `preferido` NO afecta estas funciones (ver punto 2).
- Un nivel de `asignacion` que queda vacío tras el filtrado conserva el fallback
  existente (todos los elegibles ordenados por capacidad) — aplicado sobre los
  habilitados; si no queda ninguno habilitado, la lista queda vacía y los
  consumidores caen al principal (fases) o `pendiente_bloqueada` (tareas).

## 5. Agentes multi-modelo (patrón, sin cambios de esquema)

Un agente tipo OpenCode/Hermes se registra por el flujo existente (`speckit-clis` /
`clis_config.py --accion agregar`) con:

- `headless` con `{prompt}` y `{modelo}` (V2/V3 existentes exigen selección de
  modelo si hay >1);
- `modelos[]` con un elemento por modelo expuesto (`id`, `capacidad`, `costo`,
  `contexto_k` — detectados, clasificados por feature 007, o declarados);
- opcionalmente `patrones_cuota`, `version_cmd`.

Un agente sin selección de modelo en su headless participa con un único modelo
efectivo (su default) — regla FR-008 — y se registra con `modelos[]` de un elemento.
