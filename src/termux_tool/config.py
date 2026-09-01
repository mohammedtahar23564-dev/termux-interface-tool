"""Persistent configuration management."""

from __future__ import annotations

from .errors import ConfigurationError
from .models import ToolConfig
from .paths import AppPaths
from .storage import ensure_private_dir, read_json, write_json


def load_config(paths: AppPaths) -> ToolConfig:
    if not paths.config_file.exists():
        return ToolConfig()
    try:
        return ToolConfig.from_dict(read_json(paths.config_file))
    except (OSError, ValueError, TypeError) as exc:
        raise ConfigurationError(f"cannot read {paths.config_file}: {exc}") from exc


def save_config(paths: AppPaths, config: ToolConfig) -> None:
    try:
        ensure_private_dir(paths.app_dir)
        write_json(paths.config_file, config.to_dict())
    except OSError as exc:
        raise ConfigurationError(f"cannot save {paths.config_file}: {exc}") from exc
