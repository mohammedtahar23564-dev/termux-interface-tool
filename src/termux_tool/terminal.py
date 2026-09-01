"""Termux colors.properties editing."""

from __future__ import annotations

from pathlib import Path
import stat
from typing import Dict

from .backup import BackupManager
from .errors import ToolError
from .models import COLOR_NAMES
from .paths import AppPaths
from .storage import atomic_write_text


def update_colors(path: Path, colors: Dict[str, str], backups: BackupManager, create: bool = False) -> bool:
    """Update only known color keys while preserving comments and other keys."""

    if path.exists() and not path.is_file():
        raise ToolError(f"colors path is not a regular file: {path}")
    if not path.exists() and not create:
        return False
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = original.splitlines()
    found = set()
    rendered = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in colors:
                rendered.append(f"{key}={colors[key]}")
                found.add(key)
                continue
        rendered.append(line)
    for key in sorted(set(colors) & COLOR_NAMES):
        if key not in found:
            rendered.append(f"{key}={colors[key]}")
    content = "\n".join(rendered).rstrip() + "\n"
    if content == original and path.exists():
        return False
    if path.exists():
        backups.create(path)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    atomic_write_text(path, content, mode=mode)
    return True
