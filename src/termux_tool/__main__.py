"""Allow ``python -m termux_tool``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
