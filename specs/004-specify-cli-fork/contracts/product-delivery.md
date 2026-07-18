# Contrato: entrega del producto multi-CLI (bundling)

**Feature**: 004-specify-cli-fork

> Define el contrato entre el paquete del fork y el proyecto destino respecto de QUÉ se
> entrega y DÓNDE, tomando como fuente de verdad el manifiesto vigente de `install.ps1`.

## Manifiesto de entrega (fuente de verdad = install.ps1)

### Skills multi-CLI (8) — según agente

| Skill | claude / kimi | codex |
|---|---|---|
| `speckit-models` | `.<a>/skills/speckit-models/SKILL.md` | `.codex/prompts/speckit-models.md` |
| `speckit-clis` | idem | idem |
| `speckit-agents` | idem | idem |
| `speckit-readme` | idem | idem |
| `speckit-orchestrate` | idem | idem |
| `speckit-constitution-plus` | idem | idem |
| `speckit-specify-auto` | idem | idem |
| `speckit-specify-auto-eco` | idem | idem |

- claude/kimi: copia literal del `SKILL.md`.
- codex: cuerpo sin frontmatter (`(?s)^---.*?---\s*` → ''), prefijado con `# /<skill>`.

### Otros assets — destino fijo

| Asset origen | Destino en el proyecto |
|---|---|
| `orchestrator/` (triage.md, assign.md, orchestrate.md, report-template.md, README.md) | `.specify/orchestrator/` |
| `platform.ps1`, `scan-models.ps1`, `invoke-secondary.ps1`, `update-quota.ps1`, `get-parallel-groups.ps1`, `clis-config.ps1` | `.specify/scripts/powershell/` |
| `clis-catalog.json` | `.specify/clis-catalog.json` |
| `AGENTS.md` | raíz (o `AGENTS.gen-speckit.md` si ya existe) |

### `.gitignore` — append idempotente

```
.specify/models.json
.specify/models.scan.json
specs/**/orchestration-logs/
```

## Reglas de conformidad

- **Completitud (SC-002)**: verificable ítem por ítem contra esta tabla; 0 faltantes.
- **Separación producto/desarrollo**: NADA del desarrollo del repo del fork (specs,
  constitución de gen, agentes de gen, tests, CI, README de gen) se entrega al destino —
  solo lo listado acá. (Igual que hoy el manifiesto de `install.ps1`.)
- **Aditividad (Principio I)**: la entrega no modifica ni el formato ni el contenido de los
  artefactos base de spec-kit.
- **Sincronía con la fuente**: si el manifiesto de `install.ps1` cambia (agrega/quita un
  elemento), esta tabla y el bundling del fork deben seguirlo.
