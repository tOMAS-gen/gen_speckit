"""Cross-platform helpers for the multi-CLI orchestrator."""

from __future__ import annotations

import glob
import json
import os
import platform as _platform
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def os_family() -> str:
    """Return the current operating-system family."""
    system = _platform.system().lower()
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "macos"
    return "linux"


def user_config_dir() -> Path:
    """Devuelve el directorio de configuracion de usuario para gen-speckit.

    El orden de resolucion es:

    1. ``GEN_SPECKIT_GLOBAL_DIR`` si esta definida y no es vacia.
    2. Segun la familia de SO:

       - Windows: ``%APPDATA%\\gen-speckit``
       - macOS: ``~/Library/Application Support/gen-speckit``
       - Linux: ``$XDG_CONFIG_HOME/gen-speckit`` o ``~/.config/gen-speckit``

    No crea el directorio; solo devuelve la ruta resuelta.
    """
    env_override = os.environ.get("GEN_SPECKIT_GLOBAL_DIR", "").strip()
    if env_override:
        return Path(env_override)

    family = os_family()
    if family == "windows":
        appdata = os.environ.get("APPDATA", "").strip()
        if appdata:
            return Path(appdata) / "gen-speckit"
        return Path.home() / "AppData" / "Roaming" / "gen-speckit"
    if family == "macos":
        return Path.home() / "Library" / "Application Support" / "gen-speckit"

    xdg_config = os.environ.get("XDG_CONFIG_HOME", "").strip()
    if xdg_config:
        return Path(xdg_config) / "gen-speckit"
    return Path.home() / ".config" / "gen-speckit"


def expand_portable_path(path: str) -> str:
    """Expand user-home and both Unix- and Windows-style environment variables."""
    if not path or path.isspace():
        return path

    expanded = os.path.expanduser(path)
    expanded = os.path.expandvars(expanded)
    expanded = re.sub(
        r"%([^%]+)%",
        lambda match: os.environ.get(match.group(1), match.group(0)),
        expanded,
    )
    return expanded


def resolve_executable(name: str, exe_hints=None) -> str | None:
    """Resolve an executable from candidate paths, then from ``PATH``."""
    for hint in exe_hints or ():
        expanded = expand_portable_path(hint)
        matches = glob.glob(expanded)
        for candidate in matches or [expanded]:
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)

    resolved = shutil.which(name)
    return os.path.abspath(resolved) if resolved else None


def run_process(
    command: str,
    timeout: int,
    out_file: str,
    err_file: str,
    work_dir: str,
) -> dict:
    """Run a command with redirected UTF-8 output and a timeout in seconds."""
    with open(out_file, "w", encoding="utf-8", newline="") as stdout_handle, open(
        err_file, "w", encoding="utf-8", newline=""
    ) as stderr_handle:
        process = subprocess.Popen(
            command,
            cwd=work_dir,
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            shell=True,
            text=True,
            encoding="utf-8",
        )
        try:
            exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            return {"exitCode": -1, "timedOut": True}

    return {"exitCode": exit_code, "timedOut": False}


def write_utf8_nobom(path: str, content: str) -> None:
    """Write text as UTF-8 without a byte-order mark."""
    Path(path).write_text(content, encoding="utf-8")


def write_json_atomic(path: str, obj) -> None:
    """Escribe un objeto JSON de forma atomica en `path`.

    Serializa `obj` con indentacion de 2 espacios y sin forzar ASCII,
    guarda el resultado en un archivo temporal ubicado en el mismo
    directorio que `path` y luego lo mueve con `os.replace()`. Si algo
    falla durante la escritura, el archivo temporal se elimina y `path`
    permanece inalterado.
    """
    target = Path(path)
    content = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    raw = content.encode("utf-8")
    temp_path = None
    try:
        fd, temp_path = tempfile.mkstemp(
            dir=target.parent,
            prefix=f".{target.name}.tmp-",
        )
        try:
            os.write(fd, raw)
        finally:
            os.close(fd)
        os.replace(temp_path, target)
        temp_path = None
    finally:
        if temp_path is not None:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
