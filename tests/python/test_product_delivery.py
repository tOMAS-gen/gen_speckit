"""SC-002: un solo ``install_product`` entrega el 100 % del producto multi-CLI."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

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

SCRIPTS = (
    "platform.ps1",
    "scan-models.ps1",
    "invoke-secondary.ps1",
    "update-quota.ps1",
    "get-parallel-groups.ps1",
    "clis-config.ps1",
)

GITIGNORE_ENTRIES = (
    ".specify/models.json",
    ".specify/models.scan.json",
    "specs/**/orchestration-logs/",
)


@pytest.fixture()
def project_root(tmp_path: Path) -> Path:
    install_product(tmp_path, ["claude"])
    return tmp_path


def test_skills_entregadas(project_root: Path) -> None:
    for name in SKILLS:
        skill_dir = project_root / ".claude" / "skills" / name
        assert skill_dir.is_dir(), f"falta la carpeta de skill {skill_dir}"
        assert (skill_dir / "SKILL.md").is_file(), f"falta {skill_dir}/SKILL.md"


def test_orchestrator_playbooks(project_root: Path) -> None:
    assert (project_root / ".specify" / "orchestrator" / "triage.md").is_file()


def test_scripts_powershell(project_root: Path) -> None:
    scripts_dir = project_root / ".specify" / "scripts" / "powershell"
    for script in SCRIPTS:
        assert (scripts_dir / script).is_file(), f"falta {scripts_dir / script}"


def test_python_scripts_deposited(tmp_path: Path) -> None:
    src_dir = str(Path(__file__).resolve().parents[2] / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    from specify_cli.gen_multicli import install_product

    install_product(tmp_path, ["claude"])

    scripts_dir = tmp_path / ".specify" / "scripts" / "python"
    for script in (
        "scan_models.py",
        "invoke_secondary.py",
        "update_quota.py",
        "get_parallel_groups.py",
        "clis_config.py",
        "platform_helper.py",
    ):
        assert (scripts_dir / script).is_file(), f"falta {scripts_dir / script}"


def test_catalogo_clis(project_root: Path) -> None:
    assert (project_root / ".specify" / "clis-catalog.json").is_file()


def test_agents_md(project_root: Path) -> None:
    assert (project_root / "AGENTS.md").is_file()


def test_gitignore_exclusiones(project_root: Path) -> None:
    gitignore = project_root / ".gitignore"
    assert gitignore.is_file(), "falta .gitignore"
    content = gitignore.read_text(encoding="utf-8")
    for entry in GITIGNORE_ENTRIES:
        assert entry in content, f"falta la exclusión {entry!r} en .gitignore"
