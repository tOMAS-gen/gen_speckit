# Research: Fork de specify-cli con mejoras multi-CLI integradas

**Feature**: 004-specify-cli-fork | **Fecha**: 2026-07-18

> Fase 0 del plan. Resuelve los NEEDS CLARIFICATION técnicos del plan investigando la
> arquitectura real del spec-kit oficial (github/spec-kit, rama `main`, v0.13.x).

## Decisión 1 — Sobre qué versión del upstream forkear

- **Decisión**: forkear **`main` / v0.13.x** (arquitectura de wheel bundleado + registry de
  integraciones), NO el modelo viejo de ZIPs por agente.
- **Rationale**: el usuario quiere "lo mismo que spec-kit **ahora** + mis mejoras". "Ahora"
  = v0.13.x. Además, verificado en `CHANGELOG.md`, el modelo viejo (descarga de
  `spec-kit-template-<agente>-<script>-<ver>.zip` desde releases) fue **eliminado en
  v0.4.0** (`feat(cli): embed core pack in wheel #1803`). Basar el fork en un modelo
  abandonado dejaría el fork desalineado con upstream desde el día uno.
- **Alternativas consideradas**:
  - *Fork del modelo viejo (patchear la URL de descarga)*: rechazada — arquitectura
    muerta; rompe "igual que ahora"; obliga a mantener un release de ZIPs propio.
  - *Wrapper fino sobre el oficial (pip dependency + overlay)*: rechazada por el usuario —
    quiere un fork real, "una sola pieza", no un agregado al costado.
  - *Extensión/preset comunitario aportado a upstream*: rechazada — no da identidad "de
    gen" ni control; y el producto igual necesita bundling propio.

## Decisión 2 — Cómo el `init` entrega el producto (mecanismo de integración)

- **Hechos verificados** (rutas reales en `main`):
  - `specify init` (en `src/specify_cli/commands/init.py`) **copia assets bundleados en el
    paquete** — "initialization does not need network access and templates match the
    installed CLI version". El flag `--offline` quedó deprecado/oculto: "All scaffolding now
    uses bundled assets".
  - Agentes = **registry dinámico** `INTEGRATION_REGISTRY`, construido en
    `_agent_config.py` iterando subclases bajo `src/specify_cli/integrations/`. Cada
    integración es un subdirectorio con una subclase que declara `key`, `config`,
    `registrar_config` y un método `setup(project_root, manifest, parsed_options, ...) ->
    list[Path]` que instala archivos y crea las carpetas destino.
  - `claude` = `SkillsIntegration`, `config.folder = ".claude/"`, `commands_subdir =
    "skills"`, `registrar_config = { dir: ".claude/skills", format: markdown, extension:
    "/SKILL.md" }`. **Coincide exactamente** con el formato actual de las 8 skills de
    gen_speckit.
  - `codex` y `kimi` **ya existen** como integraciones en upstream.
- **Decisión**: entregar el producto por **dos vías bundleadas**, ambas nativas del fork:
  1. **Skills multi-CLI (8)** → por el mecanismo de la integración del agente elegido
     (SkillsIntegration para claude/kimi → `.../skills/<nombre>/SKILL.md`; para codex →
     prompt plano en `.codex/prompts/<nombre>.md` sin frontmatter, como hoy `install.ps1`).
  2. **Playbooks del orquestador, 6 scripts PowerShell y `clis-catalog.json`** → como
     assets del bloque `.specify/` que el `init` siempre deposita (junto a memory/scripts/
     templates de upstream).
- **Rationale**: reutiliza el mecanismo oficial (mínimo código propio, máxima
  compatibilidad) y respeta que las skills ya están en formato SkillsIntegration.
- **Alternativas consideradas**:
  - *Nueva subclase de integración "gen" única*: descartada como vía principal — el
    producto debe convivir con la elección de agente base del usuario, no reemplazarla;
    mejor sumar assets + un preset que se aplique siempre.
  - *Preset `--preset gen` opcional*: descartada como gate — el usuario pidió que el
    producto venga **siempre** (FR-009). Se puede usar el mecanismo de preset internamente,
    pero aplicado por defecto, sin exigir el flag.

## Decisión 3 — Nombre del comando y fuente de instalación

- **Hechos**: `pyproject.toml` de upstream declara paquete `specify-cli`, entry-point
  `specify` → `specify_cli:main`. El owner/repo está hardcodeado en `src/specify_cli/
  _version.py` (`GITHUB_API_LATEST`, `_GITHUB_SOURCE_URL` = `github/spec-kit`), usado para
  el **auto-chequeo de versión/upgrade** (ya no para bajar templates).
- **Decisión**: conservar el comando **`specify`** y el nombre de paquete `specify-cli`; el
  fork reemplaza al oficial en la máquina. Instalación:
  `uv tool install specify-cli --from git+https://github.com/tOMAS-gen/gen_speckit.git`.
  Redirigir `_version.py` al fork para que el auto-upgrade apunte a gen (no al oficial).
- **Rationale**: FR-008 — mismo gesto que ya conoce el usuario; "es el spec-kit de gen".
- **Nota de riesgo**: colisión de entry-point con un `specify` oficial ya instalado vía
  `uv`. Mitigación: `uv tool install --force`/reinstall; documentarlo en README. No se
  busca convivencia (decisión del usuario).

## Decisión 4 — Mantenibilidad contra upstream (FR-007 / US3)

- **Decisión**: pinear el fork a una **versión/tag concreta** del upstream y documentar el
  procedimiento de sync en `UPSTREAM.md`. La capa propia se aísla en:
  - un submódulo Python `gen_multicli/` (wiring del bundling/preset del producto),
  - assets del producto en carpeta separada,
  - cambios mínimos y localizados en archivos de upstream (idealmente solo `_version.py` y
    el punto de enganche del preset/bundling), listados en `UPSTREAM.md`.
- **Rationale**: el Principio I exige que actualizar upstream no obligue a rehacer la capa
  propia; minimizar el "diff sobre upstream" hace el rebase/merge viable.
- **Alternativas consideradas**: git subtree/submodule del upstream completo — evaluable en
  implement; se documenta la opción en `UPSTREAM.md`, pero el pin + overlay acotado es el
  enfoque base.

## Decisión 5 — Destino de install.ps1

- **Decisión**: **deprecar** `install.ps1` como gesto de instalación una vez que el `init`
  entrega todo. Se conserva temporalmente con un aviso de deprecación apuntando al nuevo
  gesto, y se elimina de la documentación como camino recomendado. La lógica no destructiva
  que hoy tiene (no pisar AGENTS.md, preservar `.specify/`, sumar exclusiones a
  `.gitignore`) se **replica dentro del flujo del `init`/producto** para no perder esas
  garantías (FR-005).
- **Rationale**: FR-009 — un solo camino de instalación coherente con "instalar todo de
  una".

## Riesgos y puntos abiertos (para tasks/implement)

- **No verificado línea por línea**: el detalle interno de `src/specify_cli/bundler/` (qué
  carpeta mapea a qué dentro del wheel). Implica una tarea de lectura del bundler antes de
  cablear los assets del producto.
- **Esfuerzo de vendorizado**: traer y mantener ~40 módulos de integración de upstream es
  la parte más pesada; el pin + `UPSTREAM.md` acotan el costo recurrente.
- **CI multiplataforma**: validar el `init` del fork en Windows/Linux/macOS (SC-005).
- **Colisión de comando `specify`**: documentar la reinstalación con `--force`.
