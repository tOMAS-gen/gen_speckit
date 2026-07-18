"""Verifica la entrega de skills para Claude, Codex y Kimi."""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from specify_cli.gen_multicli import install_product


SKILLS = (
    "speckit-models",
    "speckit-clis",
    "speckit-agents",
    "speckit-readme",
    "speckit-orchestrate",
    "speckit-constitution-plus",
    "speckit-specify-auto",
    "speckit-specify-auto-eco",
)


def test_skills_se_entregan_para_los_tres_agentes(tmp_path: Path) -> None:
    """Cada agente recibe las ocho skills en su formato correspondiente."""
    install_product(tmp_path, ["claude", "codex", "kimi"])

    for agent_dir in (".claude", ".kimi"):
        for name in SKILLS:
            skill_dir = tmp_path / agent_dir / "skills" / name
            assert skill_dir.is_dir(), f"falta la carpeta de skill {skill_dir}"
            assert (skill_dir / "SKILL.md").is_file(), f"falta {skill_dir / 'SKILL.md'}"

    codex_prompts = tmp_path / ".codex" / "prompts"
    prompt_files = list(codex_prompts.glob("*.md"))
    assert len(prompt_files) == 8

    models_prompt = codex_prompts / "speckit-models.md"
    content = models_prompt.read_text(encoding="utf-8")
    assert not content.startswith("---")
    assert content.splitlines()[0] == "# /speckit-models"
