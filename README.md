# termux-interface-tool

[![CI](https://github.com/mohammedtahar23564-dev/termux-interface-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/mohammedtahar23564-dev/termux-interface-tool/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A safe, dependency-light Python CLI for making a Termux shell feel like your own.
It manages only the files it owns, creates a timestamped backup before every
change, and works in both interactive and scriptable environments.

## What it does

- Interactive menu and conventional subcommands
- Shell prompt and welcome-message customization
- Termux `colors.properties` customization
- ASCII banners and carefully quoted aliases
- Timestamped backup, restore, and non-destructive reset
- Termux and shell detection without hardcoded usernames
- Diagnostics for paths, permissions, backups, and optional dependencies
- Safe update checks using fast-forward-only Git operations
- Standard-library runtime with no required third-party packages

## Installation

In Termux:

```sh
pkg update
pkg install python
git clone https://github.com/mohammedtahar23564-dev/termux-interface-tool.git
cd termux-interface-tool
python -m pip install .
```

The package can also be run from a checkout without installation:

```sh
PYTHONPATH=src python -m termux_tool
```

## Usage

```sh
termux-tool                 # open the interactive menu
termux-tool setup           # apply the default profile
termux-tool customize       # edit the profile interactively
termux-tool customize --prompt '\u@\h:\w\$ ' --color accent=#58a6ff
termux-tool backup          # back up detected configuration files
termux-tool backup --list
termux-tool restore --latest
termux-tool reset           # remove only termux-tool's managed blocks
termux-tool status
termux-tool update
termux-tool --help
termux-tool --version
python -m termux_tool status
```

Use `--yes` only when running a change in an automated workflow. Without it,
important modifications and creation of missing configuration files are
confirmed interactively.

## Files managed

The tool may manage:

- `~/.bashrc` and `~/.zshrc`, but only when they exist or their creation is
  explicitly confirmed
- `~/.termux/colors.properties`, under the same creation rule
- `~/.termux_tool/config.json`
- `~/.termux_tool/backups/`

Shell changes live between clearly marked `termux-tool` comments, so reset
removes the managed block instead of deleting a user's shell configuration.
The tool never needs root access and never edits Android system files.

## Security model

Updates use `git pull --ff-only`; the application never pipes downloaded content
to a shell or executes code fetched from the network. Dependency installation,
when requested, is restricted to an allowlisted Termux package and uses an
argument list rather than shell evaluation. Paths are resolved and checked
before backup or restore operations, aliases are validated and shell-quoted,
and backups are created before a managed file is changed.

See [SECURITY.md](SECURITY.md) for responsible disclosure guidance.

## Development

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

The project deliberately keeps its runtime dependency-free. Contributions
should preserve that property unless a dependency provides a substantial,
well-justified benefit.

## License

MIT © 2026 mohammedtahar23564-dev
