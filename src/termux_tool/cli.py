"""Command-line interface and command orchestration."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Optional

from . import __version__
from .backup import BackupManager
from .config import load_config, save_config
from .dependencies import check as check_dependencies, install_missing
from .errors import ConfigurationError, ToolError
from .models import COLOR_NAMES, ToolConfig
from .paths import AppPaths, current_paths, existing_shell_files, is_termux
from .shell import apply as apply_shell, remove as remove_shell
from .terminal import update_colors
from .ui import Console
from .update import fast_forward_update


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="termux-tool",
        description="Safely customize the Termux terminal interface.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--no-color", action="store_true", help="disable colored output")
    parser.add_argument("--yes", action="store_true", help="answer yes to change confirmations")
    parser.add_argument("--non-interactive", action="store_true", help="never prompt; refuse unconfirmed changes")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    sub.add_parser("help", help="show this help message")
    sub.add_parser("version", help="show the installed version")
    install = sub.add_parser("install", help="check dependencies and optionally install missing optional tools")
    install.add_argument("--install-missing", action="store_true", help="install the allowlisted missing Termux package")
    sub.add_parser("setup", help="apply the default profile")
    customize = sub.add_parser("customize", help="edit and apply the saved profile")
    customize.add_argument("--prompt", help="shell prompt string")
    customize.add_argument("--welcome", help="welcome message")
    customize.add_argument("--banner", help="ASCII banner; use a quoted string")
    customize.add_argument("--color", action="append", metavar="NAME=#RRGGBB", help="set a Termux color")
    customize.add_argument("--alias", action="append", metavar="NAME=VALUE", help="set an alias")
    backup = sub.add_parser("backup", help="create or list backups")
    backup.add_argument("--list", action="store_true", help="list existing backups")
    restore = sub.add_parser("restore", help="restore a backup without path traversal")
    restore.add_argument("--file", help="exact backup filename")
    restore.add_argument("--latest", action="store_true", help="restore the newest backup for each supported file")
    reset = sub.add_parser("reset", help="remove only termux-tool managed blocks")
    reset.add_argument("--keep-config", action="store_true", help="keep the saved profile")
    sub.add_parser("status", help="show environment and diagnostics")
    sub.add_parser("update", help="fast-forward a local source checkout safely")
    return parser


def _parse_pairs(values: Optional[Iterable[str]], kind: str) -> dict:
    result = {}
    for item in values or []:
        if "=" not in item:
            raise ToolError(f"{kind} must use NAME=VALUE")
        name, value = item.split("=", 1)
        if not name or "\n" in item or "\r" in item:
            raise ToolError(f"invalid {kind}: {item!r}")
        result[name] = value
    return result


def _custom_config(args: argparse.Namespace, current: ToolConfig, console: Console) -> ToolConfig:
    changes = {}
    if args.prompt is not None:
        changes["prompt"] = args.prompt
    if args.welcome is not None:
        changes["welcome"] = args.welcome
    if args.banner is not None:
        changes["banner"] = args.banner
    colors = dict(current.terminal_colors)
    for name, value in _parse_pairs(args.color, "color").items():
        if name not in COLOR_NAMES or not value.startswith("#") or len(value) != 7:
            raise ToolError(f"color must be one of {', '.join(sorted(COLOR_NAMES))} and #RRGGBB")
        colors[name] = value
    if args.color:
        changes["terminal_colors"] = colors
    aliases = dict(current.aliases)
    for name, value in _parse_pairs(args.alias, "alias").items():
        aliases[name] = value
    if args.alias:
        changes["aliases"] = aliases
    if changes or any(value is not None for value in (args.prompt, args.welcome, args.banner, args.color, args.alias)):
        return current.updated(**changes)
    if not console.interactive:
        return current
    console.heading("Customize profile")
    changes = {
        "prompt": console.ask("Prompt", current.prompt),
        "welcome": console.ask("Welcome message", current.welcome),
        "banner": console.ask("ASCII banner", current.banner),
    }
    return current.updated(**changes)


def _apply_profile(paths: AppPaths, config: ToolConfig, console: Console, title: str) -> int:
    backups = BackupManager(paths)
    shells = existing_shell_files(paths)
    colors_exists = paths.colors_file.exists()
    targets = [*shells, paths.colors_file] if shells or colors_exists else []
    create_missing = False
    console.heading(title)
    console.info(f"Detected environment: {'Termux' if is_termux() else 'non-Termux'}")
    if shells:
        console.info("Shell files: " + ", ".join(str(path) for path in shells))
    else:
        console.warning("No existing ~/.bashrc or ~/.zshrc was found.")
    if colors_exists:
        console.info(f"Termux colors: {paths.colors_file}")
    if not targets:
        if not console.confirm("Create ~/.bashrc and ~/.termux/colors.properties?"):
            console.warning("No files changed.")
            return 0
        shells = [paths.home / ".bashrc"]
        targets = [*shells, paths.colors_file]
        create_missing = True
    elif not console.confirm("Apply this profile?"):
        console.warning("No files changed.")
        return 0

    save_config(paths, config)
    changed = 0
    for shell_path in shells:
        if apply_shell(shell_path, config, backups, create=create_missing or shell_path.exists()):
            changed += 1
    if update_colors(paths.colors_file, config.terminal_colors, backups, create=create_missing or paths.colors_file.exists()):
        changed += 1
    if changed:
        console.success(f"Applied profile; {changed} file(s) changed.")
        console.info(f"Backups are stored in {paths.backup_dir}")
    else:
        console.info("Profile was already up to date.")
    return 0


def _status(paths: AppPaths, console: Console) -> int:
    backups = BackupManager(paths)
    dependencies = check_dependencies()
    payload = {
        "version": __version__,
        "termux": is_termux(),
        "home": str(paths.home),
        "config": {"path": str(paths.config_file), "exists": paths.config_file.exists()},
        "shell_files": [{"path": str(p), "exists": p.exists()} for p in paths.shell_candidates()],
        "colors_file": {"path": str(paths.colors_file), "exists": paths.colors_file.exists()},
        "backup_count": len(backups.list()),
        "dependencies": dependencies,
    }
    console.heading("termux-tool status")
    console.info(f"Version: {payload['version']}")
    console.info(f"Termux detected: {'yes' if payload['termux'] else 'no'}")
    console.info(f"Home: {payload['home']}")
    console.info(f"Configuration: {'present' if payload['config']['exists'] else 'not created'}")
    console.info(f"Backups: {payload['backup_count']}")
    for dependency in dependencies:
        state = "installed" if dependency["installed"] else "missing"
        console.info(f"{dependency['name']}: {state}")
    return 0


def _backup(paths: AppPaths, console: Console) -> int:
    manager = BackupManager(paths)
    if not console.interactive and not console.assume_yes:
        raise ToolError("backup requires --yes in non-interactive mode")
    sources = [*existing_shell_files(paths)]
    if paths.colors_file.is_file():
        sources.append(paths.colors_file)
    if not sources:
        console.warning("No supported configuration files exist to back up.")
        return 0
    if not console.confirm("Create backups of detected configuration files?"):
        console.warning("No files changed.")
        return 0
    for source in sources:
        destination = manager.create(source)
        console.success(f"{source.name} → {destination.name}")
    return 0


def _restore(paths: AppPaths, args: argparse.Namespace, console: Console) -> int:
    manager = BackupManager(paths)
    records = manager.list()
    if not records:
        console.warning("No backups are available.")
        return 0
    selected = []
    if args.file:
        selected = [next((r for r in records if r.get("backup") == args.file), None)]
        if selected[0] is None:
            raise ToolError(f"backup not found: {args.file}")
    elif args.latest:
        seen_sources = set()
        selected = []
        for record in records:
            source_name = Path(record.get("source", "")).name
            if source_name not in seen_sources:
                selected.append(record)
                seen_sources.add(source_name)
    else:
        console.heading("Available backups")
        for index, record in enumerate(records, 1):
            console.info(f"{index}. {record.get('backup')} ({record.get('source')})")
        choice = console.ask("Choose a backup number", "")
        if not choice.isdigit() or not 1 <= int(choice) <= len(records):
            raise ToolError("invalid backup selection")
        selected = [records[int(choice) - 1]]
    if not console.confirm(f"Restore {len(selected)} backup(s)?"):
        console.warning("No files changed.")
        return 0
    restored = 0
    for record in selected:
        source = Path(record.get("source", ""))
        target = paths.home / source.name
        if target.name == "colors.properties":
            target = paths.colors_file
        target = target.resolve()
        # Restoring is also a modification. Preserve the current state so an
        # accidental restore can be reversed without losing user changes.
        if target.is_file():
            manager.create(target)
        manager.restore(record["backup"], target)
        restored += 1
        console.success(f"Restored {record['backup']} → {target}")
    return 0 if restored else 1


def _reset(paths: AppPaths, args: argparse.Namespace, console: Console) -> int:
    manager = BackupManager(paths)
    shells = existing_shell_files(paths)
    if not console.confirm("Remove only termux-tool managed blocks from shell files?"):
        console.warning("No files changed.")
        return 0
    changed = sum(remove_shell(path, manager) for path in shells)
    if not args.keep_config and paths.config_file.exists():
        if console.confirm("Remove the termux-tool profile file?"):
            paths.config_file.unlink()
            changed += 1
    console.success(f"Reset complete; {changed} file(s) changed.") if changed else console.info("Nothing to reset.")
    return 0


def _interactive_menu(paths: AppPaths, console: Console) -> int:
    while True:
        console.heading("termux-tool")
        console.info("1) Setup  2) Customize  3) Backup  4) Restore")
        console.info("5) Reset  6) Status  7) Exit")
        choice = console.ask("Choose an option", "7")
        if choice == "1":
            _apply_profile(paths, ToolConfig(), console, "Setup")
        elif choice == "2":
            current = load_config(paths)
            _apply_profile(paths, _custom_config(argparse.Namespace(
                prompt=None, welcome=None, banner=None, color=None, alias=None
            ), current, console), console, "Customize")
        elif choice == "3":
            _backup(paths, console)
        elif choice == "4":
            _restore(paths, argparse.Namespace(file=None, latest=False), console)
        elif choice == "5":
            _reset(paths, argparse.Namespace(keep_config=False), console)
        elif choice == "6":
            _status(paths, console)
        elif choice in {"7", "q", "quit", "exit"}:
            return 0
        else:
            console.warning("Choose a number from 1 to 7.")


def run(args: argparse.Namespace, console: Console, paths: AppPaths | None = None) -> int:
    paths = paths or current_paths()
    if args.command in (None, "help"):
        if args.command is None:
            return _interactive_menu(paths, console)
        build_parser().print_help()
        return 0
    if args.command == "version":
        console.stream.write(f"{__version__}\n")
        return 0
    if args.command == "install":
        results = check_dependencies()
        for item in results:
            state = "installed" if item["installed"] else "missing"
            console.info(f"{item['name']}: {state}")
        if args.install_missing:
            installed = install_missing()
            for package in installed:
                console.success(f"Installed {package}")
        return 0
    if args.command == "status":
        return _status(paths, console)
    if args.command == "setup":
        return _apply_profile(paths, ToolConfig(), console, "Setup")
    if args.command == "customize":
        current = load_config(paths)
        return _apply_profile(paths, _custom_config(args, current, console), console, "Customize")
    if args.command == "backup":
        if args.list:
            for record in BackupManager(paths).list():
                console.info(f"{record.get('backup')} ({record.get('source')})")
            return 0
        return _backup(paths, console)
    if args.command == "restore":
        return _restore(paths, args, console)
    if args.command == "reset":
        return _reset(paths, args, console)
    if args.command == "update":
        updated, message = fast_forward_update()
        console.success(message) if updated else console.info(message)
        return 0
    raise ToolError(f"unknown command: {args.command}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = Console(
        no_color=args.no_color,
        assume_yes=args.yes,
        interactive=not args.non_interactive,
    )
    try:
        return int(run(args, console))
    except (ToolError, ConfigurationError, PermissionError, OSError) as exc:
        console.error(str(exc))
        return 2
    except KeyboardInterrupt:
        console.warning("Cancelled.")
        return 130
