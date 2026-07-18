"""Instala el catálogo de CLIs en el proyecto destino (T012).

Deposita ``assets/clis-catalog.json`` en ``<project>/.specify/clis-catalog.json``.
"""

from __future__ import annotations

import pathlib
import shutil


def install_catalog(project_root: pathlib.Path) -> list[pathlib.Path]:
    from . import assets_dir

    src = assets_dir() / "clis-catalog.json"
    if not src.is_file():
        return []

    dest_dir = pathlib.Path(project_root) / ".specify"
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest = dest_dir / "clis-catalog.json"
    shutil.copy2(src, dest)
    return [dest]
