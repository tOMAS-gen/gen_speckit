"""Tests para .specify/scripts/python/get_parallel_groups.py.

Se ejecuta el script vía subprocess con sys.executable para robustez y se
valida el JSON que emite por stdout.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


TASKS_CONTENT = """\
- [ ] T001 [P] [C:media] [M:kimi/kimi-default] Implementar cambios en src/module_a.py
- [ ] T002 [P] [C:baja] [M:kimi/kimi-default] Refactorizar src/module_b.py
- [ ] T003 [C:alta] [M:claude/claude-sonnet] Documentar tarea sin paralelismo
"""


@pytest.fixture
def script_path(repo_root: Path) -> Path:
    """Ruta al script bajo test."""
    return repo_root / ".specify" / "scripts" / "python" / "get_parallel_groups.py"


@pytest.fixture
def tasks_file(tmp_path: Path) -> Path:
    """Archivo tasks.md temporal con 3 tareas de ejemplo."""
    path = tmp_path / "tasks.md"
    path.write_text(TASKS_CONTENT, encoding="utf-8")
    return path


def test_get_parallel_groups_subprocess(script_path: Path, tasks_file: Path) -> None:
    """El script agrupa las dos tareas [P] sin rutas compartidas en paralelo."""
    assert script_path.exists(), f"Script no encontrado: {script_path}"

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--tasks-path",
            str(tasks_file),
            "--max-concurrency",
            "4",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert not result.stderr

    data = json.loads(result.stdout)

    # Claves del resumen
    assert set(data.keys()) >= {
        "total_tareas",
        "pendientes",
        "sin_asignar",
        "max_concurrencia",
        "grupos",
    }

    assert data["total_tareas"] == 3
    assert data["pendientes"] == 3
    assert data["sin_asignar"] == 0
    assert data["max_concurrencia"] == 4

    grupos = data["grupos"]
    assert isinstance(grupos, list)
    assert len(grupos) == 2

    # Buscar el grupo paralelo con las dos tareas [P]
    parallel_groups = [g for g in grupos if g["paralelo"]]
    assert len(parallel_groups) == 1
    parallel_group = parallel_groups[0]
    assert len(parallel_group["tareas"]) == 2
    parallel_ids = {t["id"] for t in parallel_group["tareas"]}
    assert parallel_ids == {"T001", "T002"}

    # El otro grupo es serial y contiene T003
    serial_groups = [g for g in grupos if not g["paralelo"]]
    assert len(serial_groups) == 1
    assert len(serial_groups[0]["tareas"]) == 1
    assert serial_groups[0]["tareas"][0]["id"] == "T003"

    # Cada tarea expone las claves requeridas
    required_task_keys = {"id", "complejidad", "cli", "modelo", "rutas", "descripcion"}
    for grupo in grupos:
        for tarea in grupo["tareas"]:
            assert set(tarea.keys()) >= required_task_keys
            assert isinstance(tarea["rutas"], list)
            assert tarea["descripcion"]
