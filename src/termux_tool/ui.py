"""Small terminal presentation layer."""

from __future__ import annotations

import os
import sys
from typing import TextIO


class Console:
    def __init__(self, no_color: bool = False, assume_yes: bool = False, interactive: bool = True,
                 stream: TextIO | None = None):
        self.stream = stream or sys.stdout
        self.assume_yes = assume_yes
        self.interactive = interactive
        self.color = not no_color and os.environ.get("NO_COLOR") is None and self._isatty()

    def _isatty(self) -> bool:
        try:
            return bool(self.stream.isatty())
        except (AttributeError, OSError):
            return False

    def style(self, text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.color else text

    def heading(self, text: str) -> None:
        self.stream.write(f"\n{self.style(text, '1;36')}\n")

    def info(self, text: str) -> None:
        self.stream.write(f"{self.style('•', '36')} {text}\n")

    def success(self, text: str) -> None:
        self.stream.write(f"{self.style('✓', '32')} {text}\n")

    def warning(self, text: str) -> None:
        self.stream.write(f"{self.style('!', '33')} {text}\n")

    def error(self, text: str) -> None:
        self.stream.write(f"{self.style('✗', '31')} {text}\n")

    def confirm(self, question: str, default: bool = False) -> bool:
        if self.assume_yes:
            return True
        if not self.interactive:
            return False
        suffix = "[Y/n]" if default else "[y/N]"
        answer = input(f"{question} {suffix} ").strip().lower()
        return default if not answer else answer in {"y", "yes"}

    def ask(self, question: str, default: str = "") -> str:
        if not self.interactive:
            return default
        suffix = f" [{default}]" if default else ""
        answer = input(f"{question}{suffix}: ")
        return answer if answer else default

    def flush(self) -> None:
        self.stream.flush()
