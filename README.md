# gen_speckit

<!-- speckit:objetivo:inicio -->
## Objetivo

Un **fork del [Spec Kit de GitHub](https://github.com/github/spec-kit)** con un
orquestador multi-CLI (Claude Code, Codex y Kimi) integrado dentro del propio
`specify-cli`: el usuario solo escribe la idea y el sistema clasifica su complejidad
(triage), elige el flujo y el modelo para cada fase y cada tarea, y despacha el trabajo
al modelo más económico que alcance — reservando los caros para las decisiones que lo
justifican. Un único `specify init` instala base + producto, y corre en cualquier
entorno con solo Python. Todo de forma estrictamente aditiva sobre spec-kit.

_Actualizado: 2026-07-18_
<!-- speckit:objetivo:fin -->

<!-- speckit:alcance:inicio -->
## Alcance

**Es**: fork de spec-kit con las mejoras multi-CLI dentro de `specify-cli` (un solo
`specify init`); skills y playbooks Markdown portables; scripts de soporte en **Python**
(multiplataforma, sin PowerShell); inventario y ranking de modelos (`models.json`);
pipelines de una sola llamada (IDEAL y ECO); asignación de tareas por complejidad;
orquestación con despacho headless, paralelismo y fallback por cuota; especificador de
agentes y README gestionado.

**No es**: no modifica las skills base ni el formato de artefactos de spec-kit; no usa
API keys (solo los CLIs con sus suscripciones). Los scripts PowerShell heredados quedan
solo por transición.

_Actualizado: 2026-07-18_
<!-- speckit:alcance:fin -->

<!-- speckit:estado:inicio -->
## Estado

| Feature | Fase | Avance |
|---|---|---|
| 001 — Orquestador Multi-CLI | Implementada | Despacho real a los 3 CLIs validado en producción |
| 002 — Especificador de Agentes y README | Implementada | 7 agentes del proyecto generados y aprobados |
| 003 — Soporte Genérico de CLIs y Multiplataforma | Implementada | Cualquier CLI registrable sin tocar código |
| 004 — Fork de specify-cli (init de un solo paso) | Implementada | 28/28; `specify init` entrega base + producto, validado con el CLI real; `install.ps1` deprecado |
| 005 — Scripts de soporte en Python (multiplataforma) | Implementada | 20/20; orquestador corre con solo Python (sin `pwsh`); CI `validate` verde en Windows/Linux/macOS |

_Actualizado: 2026-07-18_
<!-- speckit:estado:fin -->

> **Dos mundos que no se cruzan.** Este README separa **[Usar gen_speckit](#usar-gen_speckit-instalar-en-tu-proyecto)**
> (instalar la herramienta en tu proyecto) de **[Desarrollo de gen_speckit](#desarrollo-de-gen_speckit-este-repo)**
> (trabajar sobre este repo). Lo que se instala en un proyecto es **solo el producto**;
> los artefactos y datos del desarrollo de la herramienta nunca viajan al proyecto destino.

---

# Usar gen_speckit (instalar en tu proyecto)

## Instalación — un solo paso

gen_speckit se instala **con el mismo gesto del spec-kit oficial**, pero un único
`specify init` deja base + producto multi-CLI, **todo de una**:

```powershell
# 1) Instalar el spec-kit de gen (una sola vez por máquina; reemplaza al specify oficial):
uv tool install specify-cli --force --from git+https://github.com/tOMAS-gen/gen_speckit.git
specify version   # verificar

# 2) En la carpeta de tu proyecto — un solo init entrega base + mejoras multi-CLI:
specify init . --integration claude --script ps
```

No hay segundo paso ni `install.ps1`. Corre en **Windows / Linux / macOS con solo
Python** (los scripts de soporte del orquestador son Python; no hace falta `pwsh`).

## Qué te instala (el producto, y solo el producto)

`specify init` deposita, además de la base intacta de spec-kit:

- las **8 skills multi-CLI** (`speckit-models`, `speckit-clis`, `speckit-agents`,
  `speckit-readme`, `speckit-orchestrate`, `speckit-constitution-plus`,
  `speckit-specify-auto`, `speckit-specify-auto-eco`);
- los **playbooks del orquestador** en `.specify/orchestrator/` (triage, assign, orchestrate, report);
- los **scripts de soporte en Python** en `.specify/scripts/python/`;
- el **catálogo de CLIs** (`.specify/clis-catalog.json`);
- el aporte a `AGENTS.md` (no destructivo) y las exclusiones de datos locales en `.gitignore`.

> **Nada del desarrollo de este repo** (specs, constitución de gen, agentes, tests, CI,
> ni tu `models.json` local) llega a tu proyecto. Ver
> [Separación desarrollo ↔ producto](#separación-desarrollo--producto-instalado).

**Elegís tu agente principal** con `--skills` (por defecto, el mismo de `--integration`):

| Valor de `--skills` | Dónde quedan las skills |
|---|---|
| `claude` (default) | `.claude/skills/<nombre>/SKILL.md` |
| `kimi` | `.kimi/skills/<nombre>/SKILL.md` (mismo formato SKILL.md) |
| `codex` | `.codex/prompts/<nombre>.md` (prompt plano, sin frontmatter) |
| `todos` | los tres a la vez |

## Requisitos

- **Cualquier entorno con Python ≥3.11** (Windows / Linux / macOS) — sin PowerShell/`pwsh`.
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes de Python).
- CLIs instalados: [Claude Code](https://claude.com/claude-code), Codex CLI, Kimi CLI.

## Configuración previa (una vez por máquina)

Antes de orquestar corré `/speckit-models`: detecta los CLIs instalados y arma
`.specify/models.json` con el inventario y el ranking. Lo no detectable (plan contratado,
cuotas, ventana de contexto) lo declarás vos y **tus correcciones a mano siempre
prevalecen**. Este archivo tiene **datos locales de tu máquina** y está en `.gitignore` —
no se versiona ni se distribuye.

## Cómo se usa (el flujo)

```
Preparación (una vez):
  /speckit-models  → inventario + ranking en .specify/models.json

Por cada idea / feature:
  Triage (el modelo más capaz, antes de arrancar):
    · Idea simple   → flujo ECO,  fases con modelos económicos
    · Idea media    → flujo IDEAL, fases mixtas
    · Idea compleja → flujo IDEAL, fases clave con el modelo importante
  Pipeline (specify → ... → tasks):
    En tasks, el modelo importante clasifica cada tarea [C:baja|media|alta]
    y le asigna un modelo [M:cli/modelo] (nunca discrimina — todos participan).
  Orquestador (implement):
    Despacha cada tarea a su CLI ([P] en paralelo), escala al siguiente del
    ranking si uno agota cuota, y el principal integra, verifica y marca [X].
```

- **Una sola llamada**: `/speckit-specify-auto "idea"` (7 fases, con controles de calidad)
  o `/speckit-specify-auto-eco "idea"` (ciclo mínimo). Encadenan solo; frenan ante dudas
  reales. Flags: `-bypass` (salta el gate si no hay dudas), `--sin-implementar` (para tras
  planificar). Retomables.
- **Arquitectura simétrica**: el orquestador corre desde cualquiera de los 3 CLIs como
  **principal**; los otros dos son **secundarios** invocados por línea de comandos
  (headless). Por eso la lógica es portable, sin depender de un CLI.
- **Autocorrección del triage**: si la idea se escribe en un CLI económico pero es
  compleja, **escala** la planificación; si es simple pero se escribió en el caro,
  **degrada**. Ningún punto de entrada es incorrecto.

### Contratos de datos

**Etiquetas en `tasks.md`** (las agrega el asignador; editables a mano):

```
- [ ] T012 [P] [US1] [C:baja]  [M:kimi/k3]     Crear modelo User en src/models/user.py
- [ ] T019     [US2] [C:alta]  [M:claude/opus] Integrar pasarela de pagos en src/services/payments.py
```

`[C:baja|media|alta]` (complejidad) y `[M:cli/modelo]` (modelo responsable) son
**aditivas e inline**; el formato oficial de spec-kit (checkbox, `T###`, `[P]`, `[US#]`,
ruta) no se toca.

**`.specify/models.json`** (lo genera `/speckit-models`; corregible a mano): por cada CLI
`instalado`/`autenticado`/`headless`/`plan`/`cuota`/`modelos[]` (con `capacidad` 1–10 y
`costo` 1–3), y `asignacion` con listas ordenadas `alta`/`media`/`baja` (el primero es el
preferido; si no tiene cuota o contexto, se escala al siguiente — fallback por diseño).

---

# Desarrollo de gen_speckit (este repo)

## Separación desarrollo ↔ producto instalado

El repo mantiene **dos cosas distintas que no se cruzan**:

| | **Desarrollo de la herramienta** (este repo se usa a sí mismo) | **Producto que se instala** (lo que shippea `specify init`) |
|---|---|---|
| Vive en | `.specify/` propio, `.claude/skills/`, `specs/`, `AGENTS.md`, `tests/`, constitución | `src/specify_cli/gen_multicli/assets/` (fuente de verdad de lo shippeable) |
| Datos locales | `.specify/models.json`, `.specify/models.scan.json`, `specs/**/orchestration-logs/` — **en `.gitignore`**, no se versionan ni se distribuyen | — |

Reglas:

1. **Fuente de verdad de lo shippeable** = `src/specify_cli/gen_multicli/assets/`. El
   `init` deposita desde ahí. Si tocás una skill/script/playbook, actualizá esa copia.
2. **El desarrollo no viaja al destino**: `specify init` instala solo el producto
   (manifiesto de arriba); nunca specs, constitución de gen, agentes, tests ni CI.
3. **Datos locales nunca se versionan ni se shippean**: `models.json` y compañía viven
   solo en tu máquina.

> Nota: hoy el producto vive también como copia de trabajo del propio repo (`.specify/`,
> `.claude/skills/`) para que gen_speckit se dogfoodee. Mantener esas copias en sync con
> `assets/` es responsabilidad del desarrollo (ver issues/roadmap para una única fuente).

## Estructura del repo

```
gen_speckit/                    # el repo ES el fork instalable (paquete Python)
├── pyproject.toml              # paquete specify-cli, entry-point `specify`, hatchling
├── src/specify_cli/            # fork de spec-kit vendorizado (upstream) + capa propia
│   └── gen_multicli/           #   capa gen: install_product + assets/ (lo shippeable)
│       └── assets/             #     skills-multicli, orchestrator, scripts-python,
│                               #     scripts-powershell (heredado), clis-catalog.json
├── templates/ scripts/ extensions/ workflows/ presets/   # core_pack de upstream (bundled)
├── .specify/                   # runtime de DESARROLLO (dogfooding)
│   ├── memory/                 #   constitución del proyecto
│   ├── orchestrator/           #   playbooks portables (triage, assign, orchestrate, report)
│   ├── scripts/python/         #   scripts de soporte en Python (via por defecto)
│   └── scripts/powershell/     #   scripts heredados (transición)
├── .claude/skills/  .codex/prompts/   # adaptadores por CLI (dev)
├── specs/                      # features especificadas (spec, plan, tasks, reportes)
├── tests/python/               # suite pytest (scripts + entrega del producto)
├── .github/workflows/          # CI: gen-validate (fork + Python en 3 SO)
├── UPSTREAM.md                 # versión pineada del upstream + procedimiento de sync
├── AGENTS.md                   # adaptador para Codex/Kimi como principal
└── README.md
```

## Construir y probar

```bash
uv build --wheel                                              # construye el paquete
uv run --no-project --with dist/*.whl --with pytest \
  python -m pytest tests/python/ -q                           # suite de tests
```

El CI (`.github/workflows/gen-validate.yml`) corre build + pytest + un `specify init` de
humo y valida los scripts Python **sin PowerShell** en Windows / Linux / macOS.

## Relación con el upstream

Este repo es un fork de `github/spec-kit@v0.13.0`. `UPSTREAM.md` documenta la versión
pineada, el **diff mínimo sobre upstream** (solo `_version.py` e `init.py`) y el
procedimiento para incorporar actualizaciones sin rehacer la capa multi-CLI.

## Skills de contexto de proyecto

- `speckit-agents`: analiza el objetivo del proyecto contra una taxonomía de dominios y
  genera las definiciones de agentes en `.specify/agents/` (portables) y `.claude/agents/`.
- `speckit-readme`: crea/actualiza este README con secciones gestionadas delimitadas
  (objetivo, alcance, estado) preservando el contenido manual.
- `speckit-constitution-plus`: corre la fase constitution y ofrece el especificador de agentes.
- `speckit-clis`: registra/edita/verifica/da de baja cualquier CLI en `models.json`
  (catálogo versionado en `.specify/clis-catalog.json`).
