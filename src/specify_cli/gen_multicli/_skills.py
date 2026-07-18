"""Entrega las 8 skills multi-CLI al/los agente(s) elegido(s) (T013).

Mapeo por agente (paridad con install.ps1):
- ``claude`` → ``.claude/skills/<nombre>/SKILL.md`` (copia literal de la carpeta)
- ``kimi``   → ``.kimi/skills/<nombre>/SKILL.md`` (mismo formato SKILL.md)
- ``codex``  → ``.codex/prompts/<nombre>.md`` (cuerpo sin frontmatter, prefijado ``# /<nombre>``)
- otro       → ``.specify/skills-portables/<nombre>/`` (copia portable, no se pierde nada)
"""

from __future__ import annotations

import pathlib
import re
import shutil

_FRONTMATTER = re.compile(r"(?s)^---.*?---\s*")


def _copy_skill_dir(skill_dir: pathlib.Path, dest_dir: pathlib.Path) -> list[pathlib.Path]:
    created: list[pathlib.Path] = []
    for item in sorted(skill_dir.rglob("*")):
        rel = item.relative_to(skill_dir)
        target = dest_dir / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            created.append(target)
    return created


def _install_codex_prompt(skill_dir: pathlib.Path, name: str, prompts_dir: pathlib.Path) -> list[pathlib.Path]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return []
    body = _FRONTMATTER.sub("", skill_md.read_text(encoding="utf-8"))
    prompts_dir.mkdir(parents=True, exist_ok=True)
    target = prompts_dir / f"{name}.md"
    target.write_text(f"# /{name}\n\n{body}", encoding="utf-8")
    return [target]


def install_skills(project_root: pathlib.Path, agents) -> list[pathlib.Path]:
    from . import assets_dir

    src = assets_dir() / "skills-multicli"
    if not src.is_dir():
        return []
    if isinstance(agents, str):
        agents = [agents]

    project_root = pathlib.Path(project_root)
    skill_dirs = sorted(d for d in src.iterdir() if d.is_dir())
    created: list[pathlib.Path] = []

    for agent in agents:
        agent = str(agent).strip().lower()
        for skill_dir in skill_dirs:
            name = skill_dir.name
            if agent in ("claude", "kimi"):
                dest = project_root / f".{agent}" / "skills" / name
                created += _copy_skill_dir(skill_dir, dest)
            elif agent == "codex":
                created += _install_codex_prompt(
                    skill_dir, name, project_root / ".codex" / "prompts"
                )
            else:
                dest = project_root / ".specify" / "skills-portables" / name
                created += _copy_skill_dir(skill_dir, dest)
    return created
