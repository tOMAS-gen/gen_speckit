# /speckit-orchestrate — orquestar la implementación multi-CLI

Actuás como **CLI principal** del orquestador multi-CLI de este repo spec-kit.

1. Leé `.specify/feature.json` para ubicar el directorio de la feature activa.
2. Validá prerequisitos: `specs/<feature>/tasks.md` con etiquetas `[M:cli/modelo]`
   (si faltan, ejecutá antes el playbook `.specify/orchestrator/assign.md`) y
   `.specify/models.json` válido (si falta, corré
   `.specify/scripts/powershell/scan-models.ps1` y pedí al usuario los datos no
   detectables).
3. Ejecutá COMPLETO el playbook `.specify/orchestrator/orchestrate.md`, paso a paso:
   tandas con `get-parallel-groups.ps1`, despacho con `invoke-secondary.ps1`,
   fallback por cuota con `update-quota.ps1`, verificación estándar y `[X]` solo
   sobre tareas verificadas.
4. Reglas duras y contrato de portabilidad: `AGENTS.md` (raíz) y
   `.specify/orchestrator/README.md`.
