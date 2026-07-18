"""Instala las instrucciones y exclusiones locales del sistema multi-CLI."""

from __future__ import annotations

import pathlib
import shutil


def install_agents_and_gitignore(project_root: pathlib.Path) -> list[pathlib.Path]:
    from . import assets_dir

    project_root = pathlib.Path(project_root)
    src = assets_dir() / "AGENTS.md"
    agents_path = project_root / "AGENTS.md"
    if agents_path.exists():
        agents_target = project_root / "AGENTS.gen-speckit.md"
    else:
        agents_target = agents_path
    shutil.copy2(src, agents_target)

    changed = [agents_target]
    gitignore = project_root / ".gitignore"
    content = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    entries = (
        ".specify/models.json",
        ".specify/models.scan.json",
        "specs/**/orchestration-logs/",
    )
    missing = [entry for entry in entries if entry not in content]
    if missing:
        comment = "# gen_speckit: datos locales del sistema multi-CLI"
        addition = [comment, *missing]
        separator = "" if not content or content.endswith("\n") else "\n"
        gitignore.write_text(
            content + separator + "\n".join(addition) + "\n",
            encoding="utf-8",
        )
        changed.append(gitignore)

    return changed
