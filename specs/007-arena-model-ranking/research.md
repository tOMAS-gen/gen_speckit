# Research: Clasificación de modelos por nivel y tarea (007)

**Fecha**: 2026-07-19 | **Spec**: [spec.md](./spec.md)

Cada sección: **Decisión** → **Racional** → **Alternativas descartadas**.

---

## R1 — Obtención de los datos del leaderboard

**Decisión**: **no scrapear arena.ai**. Consumir el dataset público oficial que
respalda ese leaderboard, vía la API REST gratuita de HuggingFace datasets-server:

```
https://datasets-server.huggingface.co/filter
  ?dataset=lmarena-ai%2Fleaderboard-dataset
  &config=text_style_control
  &split=latest
  &where="category"='coding'
  &orderby="rating"%20DESC
  &offset=0&length=100
```

JSON puro sobre HTTPS, sin autenticación, alcanzable con `urllib.request` de stdlib.
**Respaldo** (FR-005a): si esa API no responde, la skill le pide al agente que consulte
`https://arena.ai/leaderboard/text/<categoria>` con su herramienta web y le entrega las
filas al script por stdin, que las normaliza igual que las de la API.

**Cuatro condiciones que el implementador NO puede cambiar sin romper el resultado**:

1. **`config=text_style_control`, no `text`.** El nombre engaña: `text` existe y parece
   lo correcto, pero **no es lo que muestra el sitio**. Verificado: `claude-fable-5` da
   rank 1 / 1507.48 en `text_style_control` (idéntico al sitio) y rank 3 / 1493.44 en
   `text`. Elegir mal la config produce un ranking distinto sin ningún error visible.
2. **Ordenar por `rating` descendente, no por `rank`.** El campo `rank` del dataset no
   coincide con el que muestra la web (la web aplica empates / "Rank Spread"): con
   `organization=openai`, `gpt-5.6-sol-xhigh` es rank 8 en el dataset y #10 en el sitio.
3. **La fecha del snapshot es `leaderboard_publish_date`** (p. ej. `"2026-07-16"`), y
   **es distinta por arena** (text 2026-07-16, webdev 2026-07-17). No asumir una fecha
   global (FR-002).
4. **`Price $/M` y `Context` no están en el dataset** — son exclusivos de la web. No es
   un problema: el costo viene del plan declarado por el usuario (ver Assumptions) y el
   contexto ya lo trae el inventario.

**Racional**: arena.ai **no tiene API pública**. Se probaron `/api/leaderboard`,
`/api/leaderboard/text` y `/api/leaderboards`: las tres devuelven **403** (no 404 — las
rutas existen pero están bloqueadas por WAF), y `/leaderboard/text.json` devuelve el HTML
de "Leaderboard Not Found". Scrapear el HTML era la única alternativa directa y **no se
pudo verificar si la página es SSR o SPA** (los dos proxies de HTML crudo devolvieron 522
y el sandbox no tiene red), o sea que sería una apuesta. El dataset de HuggingFace, en
cambio, es la fuente **oficial de LMArena**, versionada por commit, y sus números
**coinciden exactamente** con los que renderiza el sitio — es el mismo dato, servido de
una forma estable y pensada para consumo programático.

**Alternativas descartadas**:
- **Scrapear `arena.ai/leaderboard/text`**: fragilidad no cuantificable (SSR sin
  confirmar) y un cambio de maquetado deja la feature muerta. Queda como respaldo vía
  agente, donde el modelo interpreta la página y absorbe los cambios de formato.
- **Parquet directo** (`.../resolve/main/text_style_control/latest-*.parquet`, ~554 kB):
  es la misma fuente y evita depender de la datasets-server API, pero parsear Parquet
  exige `pyarrow` o `pandas` — dependencias pesadas que el proyecto no tiene y que la
  Constitución (stdlib + `uv`) no justifica para 400 filas.
- **Mirror de terceros** `api.wulong.dev/arena-ai-leaderboards`: JSON limpio y con
  `fetched_at`, pero trae **solo 10 modelos y solo la categoría overall** — no alcanza
  para el reparto por tipo de tarea (US3), y es el proyecto personal de un tercero.
- **`github.com/fboulnois/llm-leaderboard-csv`**: última publicación 2025-09-02,
  ~10 meses desactualizado.

### R1.1 — Categorías reales disponibles

Las cinco que necesita el mapeo por fase existen con estos nombres literales en la
columna `category`: **`coding`** (371 modelos), **`math`** (364),
**`creative_writing`** (374), **`instruction_following`** (376), **`multi_turn`** (374).
Hay 29 en total (incluye idiomas y categorías ocupacionales `industry_*`), que quedan
fuera de alcance por decisión del spec. En la web los mismos filtros usan guiones
(`instruction-following`), lo que importa solo para el camino de respaldo por agente.

### R1.2 — Realidad del mapeo (valida FR-004a y FR-010)

Se cruzaron los modelos del inventario actual contra el dataset:

| Modelo del inventario | Entrada del leaderboard | Estado |
|---|---|---|
| `claude/fable` | `claude-fable-5` | inequívoco |
| `claude/haiku` | `claude-haiku-4-5-20251001` | inequívoco |
| `kimi/k3` | `kimi-k3` | inequívoco |
| `codex/gpt-5.6-sol` | `gpt-5.6-sol-xhigh` | única variante existente |
| `claude/opus` | `claude-opus-4-8`, `claude-opus-4-8-thinking`, `claude-opus-4-7`, … | **ambiguo** (familia + variantes de esfuerzo) |
| `claude/sonnet` | `claude-sonnet-4-6`, `claude-sonnet-5-high` | **ambiguo** |
| `codex/gpt-5.5` | `gpt-5.5`, `gpt-5.5-high`, `gpt-5.5-instant` | **ambiguo** |
| `codex/gpt-5.6-terra` | — | **no existe** en el leaderboard |
| `kimi/kimi-for-coding` | — | **no existe** (lo más cercano, `kimi-k2.7-code`, es otro modelo) |

Esto confirma que el diseño acertó en dos puntos: los casos ambiguos **se le preguntan al
usuario** en vez de resolverse por similitud (FR-004a) — equiparar `kimi-for-coding` con
`kimi-k2.7-code` habría metido un puntaje ajeno en el reparto —, y que **modelos sin dato
externo son la norma, no la excepción**, así que conservar su nivel previo y dejarlos
competir (FR-010) es lo que evita que dos modelos del inventario actual queden fuera del
reparto.

Los nombres del leaderboard **no son IDs de API**: llevan sufijos de configuración de
inferencia (`-thinking`, `-high`, `-xhigh`, `-instant`, `-thinking-32k`) y a veces
paréntesis (`glm-5.2 (max)`). Cualquier mapeo por igualdad exacta de string se rompe con
la próxima variante, de ahí la normalización + confirmación.

---

## R2 — Dónde vive el almacén de la máquina

**Decisión**: un único archivo JSON en el directorio de configuración del usuario,
resuelto por familia de SO con stdlib, sin dependencias nuevas:

| SO | Ruta |
|---|---|
| Windows | `%APPDATA%\gen-speckit\global.json` |
| macOS | `~/Library/Application Support/gen-speckit/global.json` |
| Linux | `${XDG_CONFIG_HOME:-~/.config}/gen-speckit/global.json` |

La resolución se agrega como `user_config_dir()` en `platform_helper.py`, que ya
concentra `os_family()` y `expand_portable_path()`. Variable de entorno
`GEN_SPECKIT_GLOBAL_DIR` para override (indispensable para tests, CI y usuarios con el
home en red).

**Racional**: `platform_helper.py` ya es el único punto donde el proyecto conoce
diferencias de SO; agregar una función más ahí mantiene esa propiedad. Un solo archivo
(en vez de un directorio con varios) hace trivial la escritura atómica y el borrado que
pide FR-015.

**Alternativas descartadas**:
- `platformdirs` (paquete PyPI): resuelve exactamente esto, pero agrega una dependencia
  externa a scripts que hoy son stdlib puro y corren dentro del proyecto del usuario.
- `~/.specify/` fijo en todos los SO: simple, pero ensucia el home en Windows y macOS,
  donde hay una convención clara.
- Guardarlo dentro del paquete instalado (`site-packages`): se pierde en cada upgrade
  de la herramienta.

---

## R3 — Escritura atómica y concurrencia (FR-017)

**Decisión**: escribir a un archivo temporal en el **mismo directorio** destino y luego
`os.replace()`. Sin locks. Lectura tolerante: si el JSON no parsea, se ignora el archivo
con aviso (FR-020) en vez de abortar.

**Racional**: `os.replace()` es atómico dentro del mismo volumen tanto en POSIX como en
Windows (a diferencia de `os.rename`, que en Windows falla si el destino existe). Con
"último que escribe gana" alcanza: el peor caso de dos proyectos escribiendo a la vez es
perder un refresco, nunca un archivo corrupto — que es exactamente lo que exige FR-017.

**Alternativas descartadas**:
- Lock de archivo (`msvcrt.locking` / `fcntl.flock`): distinto en cada SO, y agrega el
  riesgo de locks huérfanos si un proceso muere; el beneficio no justifica el costo.
- Escritura con `write_utf8_nobom()` directa (lo que hace hoy `write_json2`): una
  interrupción a mitad deja el archivo truncado — inaceptable para un archivo compartido
  entre proyectos.

---

## R4 — Cómo se convierte el puntaje en el nivel del inventario

**Decisión**: función escalonada, determinista y sin estado:
`capacidad = clamp(1, 10, floor((rating - 950) / 56) + 1)`. Los dos números (piso 950 y
paso 56) viven en el catálogo (`clasificacion.escala`) para ajustarlos sin tocar código.
Modelos sin puntaje conservan su nivel previo y quedan marcados `origen: "estimado"`.

Anclaje contra datos reales del snapshot 2026-07-16 (rango observado 952–1508):
`claude-fable-5` 1507 → **10**; un modelo de ~1350 → **8**; uno de ~1200 → **5**; el piso
~960 → **1**. La escala usa el rango real del leaderboard, no un rango inventado.

**Racional**: SC-006 exige que dos corridas sin cambios den el mismo reparto. Una
normalización relativa al conjunto observado (min-max sobre los modelos presentes)
**viola** eso: basta que el sitio agregue un modelo nuevo en el tope para que bajen los
niveles de todos los demás y cambie el reparto sin que haya cambiado nada en la máquina
del usuario. Una escala absoluta ancla el nivel al puntaje y no al ranking relativo.

**Alternativas descartadas**:
- Min-max sobre el conjunto observado: no reproducible (arriba).
- Usar la posición (rank) en vez del puntaje: pierde la magnitud — el puesto 3 y el 4
  pueden estar separados por 1 punto o por 80.
- Percentiles del leaderboard completo: reproducible, pero depende de cuántos modelos
  irrelevantes (no disponibles en ningún CLI) publique el sitio.

---

## R5 — Frescura y refresco

**Decisión**: `frescura_dias: 7` en el catálogo. Al correr `/speckit-models`: si el dato
guardado tiene menos de 7 días se usa tal cual (sin red); si tiene más, se intenta
refrescar y ante falla se usa el viejo avisando su antigüedad. `--refrescar-clasificacion`
fuerza el refresco ignorando la frescura.

**Racional**: el ranking de modelos se mueve en semanas, no en horas. 7 días mantiene el
dato razonablemente vigente sin castigar al usuario que crea varios proyectos el mismo
día — que es justamente el caso que la feature busca abaratar (SC-002).

**Alternativas descartadas**:
- Refrescar siempre: rompe SC-002 (el segundo proyecto no debe tocar la red).
- Sin vencimiento (refresco solo manual): el dato envejece en silencio, que es
  exactamente el problema de las semillas del catálogo que esta feature viene a resolver.

---

## R6 — Mapeo entre categorías del leaderboard y fases del pipeline

**Decisión**: mapeo declarado en el catálogo (`clasificacion.categorias_por_fase`), no
hardcodeado:

| Fase | Categoría del leaderboard (nombre literal) |
|---|---|
| implement | `coding` |
| plan, analyze, tasks | `math` |
| specify, clarify, checklist | `creative_writing` + `instruction_following` |
| verificación de despachos | `instruction_following` |

Un modelo sin datos por categoría participa igual, ordenado por nivel general y costo
(FR-010).

**Racional**: dejarlo en el catálogo permite corregir el mapeo cuando el sitio renombre o
agregue categorías, sin tocar código ni volver a testear. Es el mismo patrón que ya usa
el proyecto para `config_hints` y `fuentes_oficiales`.

**Alternativas descartadas**:
- Hardcodear el mapeo en el script: cualquier cambio de nombre del sitio exige un
  release.
- Preguntarle el mapeo al usuario: viola el Principio VI (interrumpir sin necesidad).

---

## R7 — Dónde se integra en el flujo existente

**Decisión**: la clasificación se aplica **antes** de `build_asignacion()`, sobre la lista
de modelos ya detectados, y entra al inventario como parte de `proposed`. El merge que ya
existe (`merge_preserving_user_edits`, que compara el archivo actual contra
`models.scan.json` para detectar ediciones a mano) resuelve FR-006 **sin código nuevo**:
si el usuario tocó el nivel, su valor difiere de la propuesta previa y prevalece
automáticamente.

**Racional**: es el punto de menor cirugía y el que reutiliza la garantía de prioridad
del usuario que el proyecto ya tiene testeada (`test_merge_campos_nuevos.py`). Meter la
clasificación después del merge exigiría reimplementar esa lógica.

**Alternativas descartadas**:
- Un comando separado (`/speckit-clasificar`): el usuario pidió explícitamente que pase
  "cuando se llama speckit-modelo".
- Aplicarla en el triage, en tiempo de reparto: obligaría a consultar la red en cada
  idea, no en cada inventario.
