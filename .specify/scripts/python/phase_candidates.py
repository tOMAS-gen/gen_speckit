"""Resuelve la lista de candidatos para despachar una fase del orquestador.

El módulo expone `resolve_phase_candidates`, que filtra el ranking del inventario
(.specify/models.json) según el estado de los CLIs/modelos, cuota y preferencia,
y un `main` para consumirlo desde línea de comandos.
"""

import argparse
import datetime
import json
import sys


def _candidato_elegible(candidato, clis, preferido, ahora):
    """Devuelve True si el candidato pasa los filtros de elegibilidad.

    No aplica la excepción del principal: el candidato se evalúa como cualquier
    otro. El principal se reintegra después si fue descartado y quedaron otros
    candidatos.
    """
    if "/" not in candidato:
        return False

    cli_id, modelo_id = candidato.split("/", 1)
    cli = clis.get(cli_id)
    if not isinstance(cli, dict):
        return False

    if cli.get("deshabilitado"):
        return False

    modelos = cli.get("modelos") or []
    modelo = None
    for m in modelos:
        if isinstance(m, dict) and m.get("id") == modelo_id:
            modelo = m
            break

    if modelo and modelo.get("deshabilitado"):
        return False

    if preferido and cli_id != preferido:
        return False

    if cli.get("cuota") == "agotada":
        reset = cli.get("cuota_reset")
        if not reset:
            return False
        try:
            reset_dt = datetime.datetime.fromisoformat(reset)
        except (ValueError, TypeError):
            return False
        try:
            if reset_dt > ahora:
                return False
        except TypeError:
            # Reset sin zona horaria: asumimos UTC para no bloquear.
            if reset_dt.tzinfo is None:
                ahora_naive = datetime.datetime.utcnow()
            else:
                ahora_naive = datetime.datetime.now()
            if reset_dt > ahora_naive:
                return False

    return True


def resolve_phase_candidates(inventory, fase, nivel_minimo, principal):
    """Devuelve la lista ordenada de candidatos para una fase.

    Reglas:
      1. Partir de `asignacion_por_fase[fase]` si existe y no está vacía;
         si no, de `asignacion[nivel_minimo]`.
      2. Excluir modelos de CLIs deshabilitados y modelos deshabilitados.
      3. Si `preferido` existe en `clis`, conservar solo modelos de ese CLI.
      4. Excluir candidatos con cuota "agotada" cuyo reset aún no venció.
         Si `cuota_reset` no parsea, se trata la cuota como agotada.
      5. El principal nunca se pierde del resultado final: si los filtros lo
         descartaron pero quedó al menos otro candidato, se reinserta al
         principio. Si no queda ningún candidato, se devuelve lista vacía
         (la fase corre en sesión).
    """
    clis = inventory.get("clis") or {}
    asignacion = inventory.get("asignacion") or {}
    asignacion_por_fase = inventory.get("asignacion_por_fase") or {}

    base = asignacion_por_fase.get(fase) or asignacion.get(nivel_minimo) or []
    if not isinstance(base, list):
        base = []

    preferido_raw = inventory.get("preferido")
    preferido = preferido_raw if preferido_raw in clis else None

    ahora = datetime.datetime.now(datetime.timezone.utc)

    filtrados = [
        c for c in base
        if isinstance(c, str) and _candidato_elegible(c, clis, preferido, ahora)
    ]

    if principal and principal not in filtrados and filtrados:
        filtrados.insert(0, principal)

    return filtrados


def main(argv=None):
    """Punto de entrada para línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Resuelve candidatos para despachar una fase del orquestador."
    )
    parser.add_argument("--fase", required=True)
    parser.add_argument("--models-path", required=True)
    parser.add_argument("--principal", required=True)
    parser.add_argument("--nivel", default="alta")
    args = parser.parse_args(argv)

    with open(args.models_path, "r", encoding="utf-8-sig") as fh:
        inventory = json.load(fh)

    candidatos = resolve_phase_candidates(
        inventory, args.fase, args.nivel, args.principal
    )

    print(json.dumps({"candidatos": candidatos}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
