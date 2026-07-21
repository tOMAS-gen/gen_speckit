# Data Model: Clasificación de modelos por nivel y tarea (007)

**Fecha**: 2026-07-19 | **Spec**: [spec.md](./spec.md) | **Research**: [research.md](./research.md)

Tres almacenes, con una regla de precedencia entre ellos (FR-012).

```
┌─ almacén de la máquina ──────────────┐   ┌─ proyecto ───────────────────────┐
│ <config_dir>/gen-speckit/global.json │   │ .specify/models.json      (final)│
│  · clasificacion (snapshot + filas)  │──▶│ .specify/models.scan.json (base) │
│  · mapeos confirmados                │   │ .specify/clis-catalog.json (cfg) │
│  · planes por CLI                    │   └──────────────────────────────────┘
│  · decisión global/local             │
└──────────────────────────────────────┘
```

## E1 — `global.json` (almacén de la máquina)

Archivo nuevo. Fuera del repo. Escritura atómica (R3). **Solo datos de la máquina**
(FR-016): nada de rutas de proyecto, credenciales ni estado de cuota.

| Campo | Tipo | Descripción |
|---|---|---|
| `version` | int | Versión del formato. Un valor no reconocido ⇒ se ignora el archivo con aviso (FR-020). |
| `compartir` | `"si"` \| `"no"` | Respuesta del usuario a la pregunta única (FR-013). Su presencia es lo que evita repreguntar. |
| `clasificacion` | objeto \| ausente | Ver E2. |
| `mapeos` | objeto | `"<cli>/<modelo>"` → `{ "entrada": "<model_name>", "modo": "auto"\|"usuario", "confianza": "alta"\|"media" }` (FR-004). |
| `planes` | objeto | `"<cli>"` → `{ "plan": "Max 5x (5h)", "declarado": "2026-07-19" }` (FR-016a). |

## E2 — `clasificacion` (snapshot del leaderboard)

| Campo | Tipo | Descripción |
|---|---|---|
| `fuente` | string | URL efectivamente consultada (FR-002). |
| `via` | `"dataset"` \| `"agente"` | Qué camino la obtuvo (R1). Diagnóstico, no lógica. |
| `publicado` | string `YYYY-MM-DD` | `leaderboard_publish_date` del snapshot. **No** la fecha de descarga. |
| `obtenido` | string ISO-8601 | Cuándo se descargó. Es lo que compara la frescura (R5). |
| `escala` | objeto | `{ "piso": 950, "paso": 56 }` — la escala usada, guardada junto al dato para que un cambio de escala sea visible y reproducible (SC-006). |
| `entradas` | array | Ver E3. |

## E3 — `entradas[]` (una fila del leaderboard)

| Campo | Tipo | Origen |
|---|---|---|
| `model_name` | string | Nombre publicado, tal cual (`claude-fable-5`, `gpt-5.6-sol-xhigh`). Es la clave de mapeo. |
| `organization` | string | Desempata homónimos entre proveedores. |
| `rating` | float | Puntaje. **Es lo que ordena** — nunca `rank` (R1, condición 2). |
| `rank_dataset` | int | Se guarda solo como referencia; no se usa para ordenar. |
| `vote_count` | int | Entradas por debajo de `clasificacion.votos_minimos` (500 por defecto) se descartan: una muestra chica da un puntaje inestable que movería el reparto sin motivo real (FR-019a). |
| `categorias` | objeto | `"coding"`/`"math"`/`"creative_writing"`/`"instruction_following"`/`"multi_turn"` → `{ "rating": float, "rank": int }`. Ausente si la categoría no trae a ese modelo. |

**Invariante**: una entrada sin `rating` en `overall` no se guarda — sin puntaje general
no hay nivel que derivar.

## E4 — Cambios en `.specify/models.json` (aditivos, Principio I)

Sobre `clis.<cli>.modelos[]`, que hoy tiene `id`/`capacidad`/`costo`/`contexto_k`
(+ `origen`/`esfuerzos` de la feature 006):

| Campo nuevo | Tipo | Descripción |
|---|---|---|
| `capacidad` | int 1–10 | **Existente.** Ahora puede provenir del puntaje (FR-005). El rango y el significado no cambian ⇒ ningún consumidor actual se entera. |
| `nivel_origen` | `"medido"` \| `"estimado"` \| `"manual"` | De dónde salió `capacidad` (FR-005). |
| `clasificacion` | objeto \| ausente | `{ "entrada": "claude-fable-5", "rating": 1507.48, "publicado": "2026-07-16", "fuente_dato": "global"\|"local" }`. Ausente ⇒ "sin dato externo". |
| `fortalezas` | objeto \| ausente | `"coding"`/`"math"`/… → int 1–10, derivado del rating por categoría con la misma escala. Alimenta E5. |

Sección nueva de primer nivel, hermana de `asignacion` (FR-009):

```json
"asignacion_por_fase": {
  "implement": ["claude/fable", "codex/gpt-5.6-sol", "..."],
  "plan":      ["..."],
  "specify":   ["..."]
}
```

`asignacion` (alta/media/baja) **no cambia de forma ni de semántica**: los playbooks que
hoy la leen siguen funcionando sin tocarlos.

## E5 — Orden de candidatos por fase

Derivado, no declarado por el usuario. Para cada fase del mapeo (R6): tomar los modelos
de CLIs instalados y habilitados, ordenar por `fortalezas[categoria]` descendente y, ante
empate, por `costo` ascendente y luego orden estable del inventario (FR-011). Un modelo
sin `fortalezas` entra igual, ordenado por `capacidad` general (FR-010).

**Invariante (Constitución IV)**: todo CLI instalado y autenticado aparece en al menos
una lista de `asignacion_por_fase`, igual que ya se exige para `asignacion`.

## E6 — Cambios en `.specify/clis-catalog.json` (aditivos)

Bloque nuevo de primer nivel, único lugar donde vive la configuración de la fuente:

```json
"clasificacion": {
  "dataset_url": "https://datasets-server.huggingface.co/filter",
  "dataset": "lmarena-ai/leaderboard-dataset",
  "config": "text_style_control",
  "split": "latest",
  "url_web": "https://arena.ai/leaderboard/text",
  "frescura_dias": 7,
  "votos_minimos": 500,
  "timeout_s": 25,
  "escala": { "piso": 950, "paso": 56 },
  "categorias_por_fase": {
    "implement": ["coding"],
    "plan": ["math"], "analyze": ["math"], "tasks": ["math"],
    "specify": ["creative_writing", "instruction_following"],
    "clarify": ["instruction_following"], "checklist": ["instruction_following"]
  },
  "alias": { "claude/fable": "claude-fable-5" }
}
```

`alias` es la salida de escape declarativa: siembra mapeos conocidos para que el usuario
no tenga que confirmarlos.

## Reglas de resolución (FR-012)

Por cada dato compartido, gana el primero que exista:

1. **Edición manual en el proyecto** — detectada por el merge ya existente: si el valor
   en `models.json` difiere del que propuso el scan anterior (`models.scan.json`), es del
   usuario y prevalece (R7).
2. **Dato local del proyecto** — `models.json` de la corrida anterior.
3. **Almacén de la máquina** — `global.json`.
4. **Catálogo** — semillas de `clis-catalog.json`.

## Transiciones de estado del nivel de un modelo

```
sin clasificar ──(match inequívoco)──▶ medido
      │                                  │
      │ (match ambiguo)                  │ (usuario corrige)
      ▼                                  ▼
  pendiente de confirmación ──────▶   manual  ◀── (usuario corrige)
      │ (usuario elige)                  ▲
      └────────────▶ medido              │
                                         │
  sin entrada en el leaderboard ─▶ estimado ──┘
```

`manual` es absorbente: una vez que el usuario fija un nivel, ningún refresco lo mueve
(FR-006, SC-007).
