# Dry-run: sincronización con upstream

## Objetivo

Verificar que el procedimiento de sync con `github/spec-kit` no rompe la capa multi-CLI de gen al actualizar el upstream vendorizado en `src/specify_cli/`.

## Pasos del ensayo

1. Clonar `github/spec-kit` en una carpeta temporal y checkout al tag pineado (actualmente `v0.13.0`).
2. Copiar `src/specify_cli/` del clon temporal sobre el fork, **excepto** el directorio `src/specify_cli/gen_multicli/`.
3. Re-aplicar el diff mínimo sobre los dos archivos de upstream:
   - `src/specify_cli/_version.py` — ajustar `GITHUB_API_LATEST` y `_GITHUB_SOURCE_URL` al fork `tOMAS-gen/gen_speckit`.
   - `src/specify_cli/commands/init.py` — reinsertar:
     - helper `_resolve_skills_agents`;
     - opción `--skills` en la firma de `init`;
     - tracker `"multicli"` en el loop de `tracker.add`;
     - llamada a `install_product` tras `ensure_constitution_from_template`.
4. Reconstruir el wheel:

   ```bash
   uv build --wheel
   ```

5. Ejecutar la suite de Python y un comando de humo:

   ```bash
   pytest tests/python/
   specify init /tmp/smoke-test --project-name smoke
   ```

## Resultado esperado

- `src/specify_cli/gen_multicli/` y `tests/python/` permanecen intactos.
- `specify init` sigue generando el scaffold base del spec-kit más el producto multi-CLI.
- El wheel se empaqueta sin errores.

## Nota

La separación entre upstream y capa gen ya fue verificada: del spec-kit original solo difieren los archivos `src/specify_cli/_version.py` e `src/specify_cli/commands/init.py`. Todo lo demás bajo `src/specify_cli/gen_multicli/` y en `tests/python/` es nuevo y no toca archivos de upstream.
