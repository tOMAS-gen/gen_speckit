"""Instala los playbooks del orquestador multi-CLI en el proyecto destino (T010).

Deposita el contenido de ``assets/orchestrator/`` en ``<project>/.specify/orchestrator/``.
Aditivo y no destructivo respecto de la base de spec-kit: solo agrega archivos propios.
"""

from __future__ import annotations

import pathlib
import shutil


def install_orchestrator(project_root: pathlib.Path) -> list[pathlib.Path]:
    from . import assets_dir

    src = assets_dir() / "orchestrator"
    if not src.is_dir():
        return []

    dest = pathlib.Path(project_root) / ".specify" / "orchestrator"
    dest.mkdir(parents=True, exist_ok=True)

    created: list[pathlib.Path] = []
    for item in sorted(src.rglob("*")):
        rel = item.relative_to(src)
        target = dest / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            created.append(target)
    return created
