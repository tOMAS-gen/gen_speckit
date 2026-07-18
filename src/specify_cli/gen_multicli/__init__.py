import pathlib

from ._agents import install_agents_and_gitignore
from ._catalog import install_catalog
from ._orchestrator import install_orchestrator
from ._scripts import install_scripts
from ._skills import install_skills


def assets_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent / "assets"


def install_product(
    project_root: pathlib.Path, skills_agents
) -> list[pathlib.Path]:
    created_paths: list[pathlib.Path] = []
    created_paths.extend(install_orchestrator(project_root))
    created_paths.extend(install_scripts(project_root))
    created_paths.extend(install_catalog(project_root))
    created_paths.extend(install_skills(project_root, skills_agents))
    created_paths.extend(install_agents_and_gitignore(project_root))
    return created_paths
