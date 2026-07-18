# Contrato: comando `specify init` del fork de gen

**Feature**: 004-specify-cli-fork

> Contrato de comportamiento del `init` del fork. Define QUÉ debe cumplir la interfaz de
> línea de comandos, sin prescribir la implementación interna. Base: las opciones oficiales
> de upstream (v0.13.x) SE CONSERVAN; se agrega la entrega del producto multi-CLI.

## Comando

```
specify init [DESTINO] [opciones]
```

## Opciones (todas las oficiales se preservan — Principio I)

| Opción | Origen | Comportamiento |
|---|---|---|
| `--integration <agente>` | upstream | Agente/integración base (claude/codex/kimi/copilot/...). Default de upstream. |
| `--script <sh\|ps>` | upstream | Tipo de script de soporte. En gen, el producto usa PowerShell. |
| `--here` | upstream | Inicializa en el directorio actual. |
| `--force` | upstream | Merge/overwrite sin confirmación (con `--here`). |
| `--preset <id>` | upstream | Aplica un preset por id. |
| `--ignore-agent-tools` | upstream | Saltea el chequeo de herramientas del agente. |
| `--skills <claude\|codex\|kimi\|todos\|lista>` | **gen (nuevo)** | Agente(s) destino de las **skills multi-CLI**. Default: el valor de `--integration`. Paridad con el `-Skills` de `install.ps1`. |

## Postcondiciones (garantías verificables)

Tras `specify init` exitoso, el proyecto destino DEBE contener:

1. **Base de spec-kit oficial** (sin regresión): skills/comandos base, `.specify/memory/`,
   `.specify/scripts/`, `.specify/templates/`, con el mismo comportamiento que una
   instalación oficial. (SC-003)
2. **Producto multi-CLI completo** (SC-002), sin pasos adicionales:
   - las 8 skills en la ubicación/formato del/los agente(s) de `--skills`;
   - `.specify/orchestrator/` con los playbooks;
   - los 6 scripts en `.specify/scripts/powershell/`;
   - `.specify/clis-catalog.json`;
   - aporte a `AGENTS.md` (no destructivo);
   - 3 exclusiones agregadas al `.gitignore`.
3. **Sin acceso de red requerido** (assets bundleados).

## Invariantes / reglas

- **No destructivo**: no pisa un `AGENTS.md` existente ni destruye un `.specify/` previo;
  el `.gitignore` se modifica solo por append idempotente.
- **Idempotencia razonable**: re-correr `init` sobre un proyecto ya inicializado
  actualiza/mantiene el producto sin duplicar.
- **Elección de agente**: `--skills todos` entrega las 8 skills a claude, codex y kimi.
- **Multiplataforma**: el resultado es equivalente en Windows/Linux/macOS (SC-005).

## Errores

| Caso | Comportamiento esperado |
|---|---|
| Destino con `AGENTS.md` propio | Aporte va a `AGENTS.gen-speckit.md` + aviso; no se pisa. |
| Agente de `--skills` desconocido | Aviso claro; se omite ese agente, no aborta el resto. |
| Falta una skill/asset en el bundle | Aviso por elemento faltante (no silencioso). |
| Colisión con `specify` oficial instalado | Documentado: reinstalar el fork con `uv tool install --force`. |
