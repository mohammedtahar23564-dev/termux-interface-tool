"""Validated configuration models."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, Mapping

from .errors import ConfigurationError

COLOR_NAMES = {"foreground", "background", "cursor"} | {f"color{i}" for i in range(16)}
DEFAULT_COLORS = {
    "foreground": "#e6edf3",
    "background": "#0d1117",
    "cursor": "#58a6ff",
}
DEFAULT_ALIASES = {"ll": "ls -la", "la": "ls -A"}
_ALIAS_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def _text(value: Any, field_name: str, maximum: int) -> str:
    if not isinstance(value, str) or "\x00" in value or len(value) > maximum:
        raise ConfigurationError(f"{field_name} must be text of at most {maximum} characters")
    return value


@dataclass
class ToolConfig:
    """User preferences persisted in ~/.termux_tool/config.json."""

    prompt: str = r"\u@\h:\w\$ "
    welcome: str = "Welcome to Termux"
    banner: str = "TERMUX"
    terminal_colors: Dict[str, str] = field(default_factory=lambda: dict(DEFAULT_COLORS))
    aliases: Dict[str, str] = field(default_factory=lambda: dict(DEFAULT_ALIASES))

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ToolConfig":
        if not isinstance(raw, Mapping):
            raise ConfigurationError("configuration must be a JSON object")
        colors = dict(DEFAULT_COLORS)
        supplied_colors = raw.get("terminal_colors", {})
        if not isinstance(supplied_colors, Mapping):
            raise ConfigurationError("terminal_colors must be an object")
        for name, value in supplied_colors.items():
            if name not in COLOR_NAMES or not isinstance(value, str) or not _HEX_COLOR.fullmatch(value):
                raise ConfigurationError(f"invalid terminal color: {name}")
            colors[name] = value.upper()

        aliases: Dict[str, str] = {}
        supplied_aliases = raw.get("aliases", {})
        if not isinstance(supplied_aliases, Mapping):
            raise ConfigurationError("aliases must be an object")
        for name, value in supplied_aliases.items():
            if not isinstance(name, str) or not _ALIAS_NAME.fullmatch(name):
                raise ConfigurationError(f"invalid alias name: {name!r}")
            aliases[_text(name, "alias name", 40)] = _text(value, f"alias {name}", 200)

        return cls(
            prompt=_text(raw.get("prompt", cls.prompt), "prompt", 200),
            welcome=_text(raw.get("welcome", cls.welcome), "welcome", 500),
            banner=_text(raw.get("banner", cls.banner), "banner", 2000),
            terminal_colors=colors,
            aliases=aliases,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "prompt": self.prompt,
            "welcome": self.welcome,
            "banner": self.banner,
            "terminal_colors": dict(sorted(self.terminal_colors.items())),
            "aliases": dict(sorted(self.aliases.items())),
        }

    def updated(self, **changes: Any) -> "ToolConfig":
        values = self.to_dict()
        values.update(changes)
        return ToolConfig.from_dict(values)
