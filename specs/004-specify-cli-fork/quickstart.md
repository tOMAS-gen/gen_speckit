# Quickstart / Validación: Fork de specify-cli con mejoras multi-CLI

**Feature**: 004-specify-cli-fork | **Fecha**: 2026-07-18

> Guía de validación end-to-end. Prueba que el fork entrega base + producto en un solo
> `specify init`. No incluye código de implementación; referencia los contratos y el
> data-model.

## Prerrequisitos

- `uv` instalado.
- PowerShell 7 (`pwsh`) disponible (Windows/Linux/macOS) para los scripts del producto.
- (Para la validación funcional completa) los CLIs claude/codex/kimi instalados y
  autenticados.

## Escenario 1 — Instalación de un solo paso (US1, SC-001)

```powershell
# 1) Instalar el fork de gen (reemplaza al specify oficial si estuviera)
uv tool install specify-cli --force --from git+https://github.com/tOMAS-gen/gen_speckit.git
specify version   # muestra la versión del fork de gen

# 2) En una carpeta de proyecto vacía, un solo init
mkdir C:\tmp\proj-demo; cd C:\tmp\proj-demo
specify init . --integration claude --script ps
```

**Resultado esperado**: sin correr ningún segundo instalador, el proyecto tiene:
- base de spec-kit: `.specify/memory/`, `.specify/scripts/`, `.specify/templates/`, skills
  base del agente;
- producto multi-CLI: 8 skills en `.claude/skills/`, `.specify/orchestrator/`, los 6
  scripts en `.specify/scripts/powershell/`, `.specify/clis-catalog.json`, aporte a
  `AGENTS.md`, 3 exclusiones en `.gitignore`.

## Escenario 2 — Completitud del producto (SC-002)

Verificar ítem por ítem contra `contracts/product-delivery.md`:

```powershell
# skills
'speckit-models','speckit-clis','speckit-agents','speckit-readme','speckit-orchestrate',
'speckit-constitution-plus','speckit-specify-auto','speckit-specify-auto-eco' |
  ForEach-Object { Test-Path ".claude/skills/$_/SKILL.md" }   # todos True

# orquestador + scripts + catálogo
Test-Path .specify/orchestrator/triage.md
'platform.ps1','scan-models.ps1','invoke-secondary.ps1','update-quota.ps1',
'get-parallel-groups.ps1','clis-config.ps1' |
  ForEach-Object { Test-Path ".specify/scripts/powershell/$_" }   # todos True
Test-Path .specify/clis-catalog.json
```

**Esperado**: 0 faltantes.

## Escenario 3 — Sin regresión de compatibilidad (SC-003)

```powershell
# los comandos/artefactos base de spec-kit se comportan igual que en instalación oficial
specify --help          # opciones oficiales presentes (--integration, --script, --here, ...)
```

**Esperado**: comportamiento base idéntico al oficial; el producto es estrictamente
aditivo (ninguna skill base ni archivo `.specify/` de upstream modificado).

## Escenario 4 — Pipelines multi-CLI de punta a punta (SC-004)

```powershell
# en el proyecto recién inicializado
/speckit-models                       # genera .specify/models.json
/speckit-specify-auto "una idea de prueba"
```

**Esperado**: el pipeline corre sin que falte ningún playbook, script o skill (triage →
specify → ... → orquestación disponible).

## Escenario 5 — Elección de agente `todos` (US2)

```powershell
specify init . --integration claude --script ps --skills todos
```

**Esperado**: las 8 skills quedan entregadas para los tres agentes: `.claude/skills/`,
`.codex/prompts/` (planos, sin frontmatter) y `.kimi/skills/`.

## Escenario 6 — No destructivo (FR-005)

```powershell
# proyecto con AGENTS.md propio previo
"mi contenido" | Set-Content AGENTS.md
specify init . --integration claude
```

**Esperado**: `AGENTS.md` original intacto; aporte multi-CLI en `AGENTS.gen-speckit.md` +
aviso. `.specify/` previo preservado. `.gitignore` con append idempotente (sin duplicar).

## Escenario 7 — Multiplataforma (SC-005)

Repetir el Escenario 1 en Windows, Linux y macOS (con `pwsh` 7). **Esperado**: producto
entregado equivalente en las tres plataformas (corrida de validación / CI del proyecto).

## Criterios de aceptación de la validación

- [ ] Escenario 1: un solo `init` deja base + producto (SC-001).
- [ ] Escenario 2: 0 elementos del producto faltantes (SC-002).
- [ ] Escenario 3: sin regresión de compatibilidad (SC-003).
- [ ] Escenario 4: pipelines corren de punta a punta (SC-004).
- [ ] Escenario 5: `--skills todos` entrega a los 3 agentes (US2).
- [ ] Escenario 6: entrega no destructiva (FR-005).
- [ ] Escenario 7: equivalente en Windows/Linux/macOS (SC-005).
