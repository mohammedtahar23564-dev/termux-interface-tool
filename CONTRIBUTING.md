# Contributing

Thanks for helping make Termux customization safer and more useful.

## Before opening a pull request

1. Keep changes focused and preserve the standard-library-only runtime.
2. Add or update tests for behavior changes.
3. Run `python -m unittest discover -s tests -v`.
4. Check that no user files, credentials, or generated backups are included.
5. Explain any security or compatibility trade-offs in the pull request.

Please use conventional, descriptive commit messages and keep the command-line
interface backwards compatible where practical.
