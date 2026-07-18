# Resultados de quickstart

| Escenario | Resultado | Evidencia |
|---|---|---|
| 1. Init de un solo paso | PASS | `specify init` real mostró en el tracker "Install multi-CLI product (gen_speckit) (23 archivos)" y dejó base + producto sin segundo instalador. |
| 2. Completitud SC-002 | PASS | `pytest test_product_delivery` (6 asserts) verde: 8 skills, `orchestrator/triage.md`, 6 scripts, `clis-catalog.json`, `AGENTS.md`, 3 exclusiones en `.gitignore`. |
| 3. Sin regresión SC-003 | PASS | `pytest test_no_regression` verde: `install_product` no modifica `.specify/templates` ni `.specify/memory`. |
| 4. Pipelines end-to-end SC-004 | PARCIAL | Las 8 skills y playbooks quedan presentes tras el init; la corrida completa de `/speckit-specify-auto` se valida manualmente por el usuario. |
| 5. `--skills todos` | PASS | Init real entregó las 8 skills a claude, kimi y codex (39 archivos). |
| 6. No destructivo FR-005 | PASS | Con `AGENTS.md` propio el aporte va a `AGENTS.gen-speckit.md`; `.gitignore` idempotente (verificado en test). |
| 7. Multiplataforma SC-005 | PENDIENTE CI | Validado localmente en Windows; el workflow `.github/workflows/gen-validate.yml` corre el smoke en ubuntu/windows/macos. |

Resumen: 6 PASS, 1 parcial, 1 pendiente-CI.
