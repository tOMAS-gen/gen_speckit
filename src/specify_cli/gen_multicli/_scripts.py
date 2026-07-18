import pathlib
import shutil


def _copy_scripts(src: pathlib.Path, dest: pathlib.Path, pattern: str) -> list[pathlib.Path]:
    if not src.is_dir():
        return []
    dest.mkdir(parents=True, exist_ok=True)
    created: list[pathlib.Path] = []
    for item in sorted(src.glob(pattern)):
        target = dest / item.name
        shutil.copy2(item, target)
        created.append(target)
    return created


def install_scripts(project_root: pathlib.Path) -> list[pathlib.Path]:
    """Instala los scripts de soporte del orquestador multi-CLI.

    Vía por defecto: los scripts **Python** en ``.specify/scripts/python/`` (corren en
    cualquier entorno con solo Python, sin PowerShell — feature 005). Durante la
    transición se conservan también los scripts PowerShell heredados (FR-008).
    """
    from . import assets_dir

    project_root = pathlib.Path(project_root)
    created: list[pathlib.Path] = []
    # Python (vía por defecto): incluye platform_helper.py y __init__.py si están.
    created += _copy_scripts(
        assets_dir() / "scripts-python",
        project_root / ".specify" / "scripts" / "python",
        "*.py",
    )
    # PowerShell (heredado, transición).
    created += _copy_scripts(
        assets_dir() / "scripts-powershell",
        project_root / ".specify" / "scripts" / "powershell",
        "*.ps1",
    )
    return created
