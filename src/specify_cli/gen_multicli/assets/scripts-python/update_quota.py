"""Update a CLI quota state in the multi-CLI models inventory."""

import argparse
import datetime
import json


def _timestamp(value):
    """Format a local datetime like PowerShell's yyyy-MM-ddTHH:mm:sszzz."""
    return value.astimezone().isoformat(timespec="seconds")


def _reset_for_plan(plan, started):
    """Estimate the reset timestamp using the plan's declared window."""
    if not plan or plan.strip().lower() == "desconocido":
        return "desconocido"

    normalized = plan.lower()
    number = ""
    for index, character in enumerate(normalized):
        if character.isdigit():
            number += character
            continue
        if number and character == "h":
            return _timestamp(started + datetime.timedelta(hours=int(number)))
        if number and not character.isspace():
            number = ""

    if "sem" in normalized or "week" in normalized:
        return _timestamp(started + datetime.timedelta(days=7))
    if "dia" in normalized or "day" in normalized or "daily" in normalized or "diari" in normalized:
        return _timestamp(started + datetime.timedelta(days=1))
    if "mes" in normalized or "month" in normalized:
        return _timestamp(started + datetime.timedelta(days=30))
    return "desconocido"


def update_quota(models_path, cli, estado, plan=None):
    """Update one inventory entry and write it back in canonical JSON format."""
    try:
        with open(models_path, "r", encoding="utf-8-sig") as models_file:
            data = json.load(models_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"No existe el inventario: {models_path}") from None

    clis = data.get("clis")
    if not isinstance(clis, dict) or cli not in clis:
        raise KeyError(f"CLI '{cli}' no existe en el inventario")
    entry = clis[cli]
    now = datetime.datetime.now().astimezone()

    if estado == "agotada":
        entry["cuota"] = "agotada"
        entry["cuota_desde"] = _timestamp(now)
        selected_plan = plan if plan is not None else entry.get("plan", "desconocido")
        entry["cuota_reset"] = _reset_for_plan("" if selected_plan is None else str(selected_plan), now)
    else:
        entry["cuota"] = "ok"
        entry.pop("cuota_desde", None)
        entry.pop("cuota_reset", None)

    with open(models_path, "w", encoding="utf-8", newline="") as models_file:
        json.dump(data, models_file, ensure_ascii=False, indent=2)
        models_file.write("\n")

    reset = entry.get("cuota_reset")
    print(f"Cuota de '{cli}' -> {entry['cuota']}" + (f" (reset estimado: {reset})" if reset else ""))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", required=True)
    parser.add_argument("--estado", required=True, choices=("ok", "agotada"))
    parser.add_argument("--models-path", required=True)
    parser.add_argument("--plan")
    arguments = parser.parse_args()
    update_quota(arguments.models_path, arguments.cli, arguments.estado, arguments.plan)


if __name__ == "__main__":
    main()
