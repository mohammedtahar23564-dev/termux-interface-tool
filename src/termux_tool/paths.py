"""Paths and environment detection with no hardcoded user names."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable, List

from .errors import SafetyError


@dataclass(frozen=True)
class AppPaths:
    home: Path

    @property
    def app_dir(self) -> Path:
        return self.home / ".termux_tool"

    @property
    def config_file(self) -> Path:
        return self.app_dir / "config.json"

    @property
    def backup_dir(self) -> Path:
        return self.app_dir / "backups"

    @property
    def termux_dir(self) -> Path:
        return self.home / ".termux"

    @property
    def colors_file(self) -> Path:
        return self.termux_dir / "colors.properties"

    def shell_candidates(self) -> List[Path]:
        return [self.home / ".bashrc", self.home / ".zshrc"]


def current_paths() -> AppPaths:
    return AppPaths(Path.home().resolve())


def is_termux(env: dict | None = None) -> bool:
    """Return true only for recognizable Termux markers."""

    values = os.environ if env is None else env
    prefix = values.get("PREFIX", "")
    return bool(
        values.get("TERMUX_VERSION")
        or values.get("TERMUX_APK_RELEASE")
        or "/com.termux/" in prefix
        or prefix.endswith("/com.termux")
    )


def existing_shell_files(paths: AppPaths) -> List[Path]:
    return [candidate for candidate in paths.shell_candidates() if candidate.is_file()]


def ensure_within(path: Path, root: Path) -> Path:
    """Resolve a path and reject traversal outside root."""

    resolved_root = root.expanduser().resolve()
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise SafetyError(f"path is outside the permitted directory: {path}") from exc
    return resolved


def allowed_restore_target(path: Path, paths: AppPaths) -> Path:
    resolved = ensure_within(path, paths.home)
    allowed = {candidate.resolve() for candidate in paths.shell_candidates()}
    allowed.add(paths.colors_file.resolve())
    if resolved not in allowed:
        raise SafetyError("restore target is not a supported Termux configuration file")
    return resolved
