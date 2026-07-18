import pathlib

import pytest


@pytest.fixture
def repo_root() -> pathlib.Path:
    """Return the repository root as an absolute Path."""
    return pathlib.Path(__file__).resolve().parents[2]
