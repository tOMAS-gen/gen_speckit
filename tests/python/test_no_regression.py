"""SC-003: la instalacion multi-CLI es aditiva respecto de spec-kit base."""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from specify_cli.gen_multicli import install_product


def test_install_product_no_modifica_artefactos_base(tmp_path: Path) -> None:
    """Los directorios base de templates y memory se conservan intactos."""
    template = tmp_path / ".specify" / "templates" / "spec-template.md"
    constitution = tmp_path / ".specify" / "memory" / "constitution.md"
    template.parent.mkdir(parents=True)
    constitution.parent.mkdir(parents=True)
    template.write_text("BASE ORIGINAL", encoding="utf-8")
    constitution.write_text("CONST BASE", encoding="utf-8")

    base_files_before = {
        path.relative_to(tmp_path): path.read_bytes()
        for directory in (template.parent, constitution.parent)
        for path in directory.rglob("*")
        if path.is_file()
    }

    install_product(tmp_path, ["claude"])

    assert template.read_text(encoding="utf-8") == "BASE ORIGINAL"
    assert constitution.read_text(encoding="utf-8") == "CONST BASE"

    base_files_after = {
        path.relative_to(tmp_path): path.read_bytes()
        for directory in (template.parent, constitution.parent)
        for path in directory.rglob("*")
        if path.is_file()
    }
    assert base_files_after == base_files_before
