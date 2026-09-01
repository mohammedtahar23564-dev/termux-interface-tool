"""A deliberately conservative source checkout updater."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import re
from typing import Tuple

from .errors import ToolError


def repository_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        if (directory / ".git").is_dir():
            return directory
    return None


def fast_forward_update(root: Path | None = None) -> Tuple[bool, str]:
    """Fetch no scripts and allow only Git's fast-forward update behavior."""

    git = shutil.which("git")
    if not git:
        raise ToolError("Git is not installed; run 'termux-tool install' in Termux")
    checkout = repository_root(root)
    if checkout is None:
        return False, "not running from a Git checkout; nothing was updated"
    result = subprocess.run(
        [git, "-C", str(checkout), "pull", "--ff-only"],
        check=False,
        capture_output=True,
        text=True,
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise ToolError(f"safe update failed: {_redact(output) or 'git returned a non-zero exit code'}")
    return True, _redact(output) or "already up to date"


def _redact(value: str) -> str:
    """Avoid echoing credentials if a Git remote reports them in diagnostics."""

    return re.sub(r"(https?://)([^/\s@]+):([^@\s]+)@", r"\1[redacted]@", value)
