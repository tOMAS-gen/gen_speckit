# gen_speckit

gen_speckit es una version de `specify-cli` enfocada en que puedas usar Spec Kit con
flujos multi-CLI desde un solo punto de entrada.

## Requisitos

- Python 3.11 o superior
- `uv`
- Al menos un CLI de IA instalado, por ejemplo Claude Code, Codex CLI o Kimi CLI

## Instalacion

Instalar la herramienta una sola vez por maquina:

```bash
uv tool install specify-cli --force --from git+https://github.com/tOMAS-gen/gen_speckit.git
```

Inicializarla dentro de tu proyecto:

```bash
specify init . --script ps
```

Ese comando abre el selector interactivo para elegir la integracion.

Si preferis fijarla manualmente, podes indicar una integracion concreta:

```bash
specify init . --integration codex --script ps
```

Si queres instalar las skills multi-CLI para otro agente, podes usar `--skills`:

```bash
specify init . --integration codex --script ps --skills todos
```

## Uso Recomendado

1. Ejecutar `/speckit-models` una vez por maquina para registrar y ordenar los modelos disponibles.
2. Ejecutar `/speckit-specify-auto "tu idea"` para correr el flujo completo.
3. Si la idea es simple o queres un flujo mas corto, usar `/speckit-specify-auto-eco "tu idea"`.

## Comandos Principales

| Comando | Uso |
|---|---|
| `/speckit-models` | Detecta y configura modelos disponibles |
| `/speckit-clis` | Registrar, editar o verificar CLIs |
| `/speckit-specify-auto "idea"` | Corre el flujo completo recomendado |
| `/speckit-specify-auto-eco "idea"` | Corre un flujo reducido para ideas simples |
| `/speckit-orchestrate` | Ejecuta la implementacion orquestada cuando ya existe `tasks.md` |
| `/speckit-agents` | Genera agentes del proyecto |
| `/speckit-readme` | Actualiza el README gestionado del proyecto |

## Comandos Base De Spec Kit

Si preferis ejecutar el flujo paso por paso, tambien tenes disponibles los comandos base:

- `/speckit-constitution`
- `/speckit-specify`
- `/speckit-clarify`
- `/speckit-plan`
- `/speckit-tasks`
- `/speckit-checklist`
- `/speckit-analyze`
- `/speckit-implement`
- `/speckit-converge`
- `/speckit-taskstoissues`

## Flujo Tipico

```text
/speckit-models
/speckit-specify-auto "tu idea"
```

Con eso, el sistema decide el flujo y reparte el trabajo segun los modelos disponibles.
