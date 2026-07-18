"""Cross-platform helpers for the multi-CLI orchestrator."""

from __future__ import annotations

import glob
import os
import platform as _platform
import re
import shutil
import subprocess
from pathlib import Path


def os_family() -> str:
    """Return the current operating-system family."""
    system = _platform.system().lower()
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "macos"
    return "linux"


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
