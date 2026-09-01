"""Minimal, allowlisted dependency checks."""

from __future__ import annotations

from dataclasses import dataclass
import shutil
import subprocess
from typing import List

from .errors import ToolError
from .paths import is_termux


@dataclass(frozen=True)
class Dependency:
    name: str
    command: str
    required: bool = False


DEPENDENCIES = (Dependency("Python", "python", True), Dependency("Git (optional)", "git"))
ALLOWLISTED_TERMUX_PACKAGES = {"git": "git"}


def check() -> List[dict]:
    return [
        {"name": item.name, "command": item.command, "installed": shutil.which(item.command) is not None}
        for item in DEPENDENCIES
    ]


def install_missing() -> List[str]:
    """Install only the known optional package, and only via Termux's package manager."""

    missing = [item for item in check() if not item["installed"]]
    optional = [item for item in missing if item["command"] in ALLOWLISTED_TERMUX_PACKAGES]
    if not optional:
        return []
    if not is_termux():
        raise ToolError("automatic dependency installation is available only inside Termux")
    if shutil.which("pkg") is None:
        raise ToolError("Termux package manager 'pkg' was not found")
    installed = []
    for item in optional:
        package = ALLOWLISTED_TERMUX_PACKAGES[item["command"]]
        result = subprocess.run(["pkg", "install", "-y", package], check=False)
        if result.returncode != 0:
            raise ToolError(f"Termux could not install {package} (exit code {result.returncode})")
        installed.append(package)
    return installed
