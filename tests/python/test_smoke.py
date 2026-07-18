import pathlib


def test_pyproject_exists(repo_root: pathlib.Path) -> None:
    pyproject = repo_root / "pyproject.toml"
    assert pyproject.exists()
