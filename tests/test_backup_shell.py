from pathlib import Path
import tempfile
import unittest

from termux_tool.backup import BackupManager
from termux_tool.models import ToolConfig
from termux_tool.paths import AppPaths
from termux_tool.shell import END, START, apply, remove, render_block


class BackupAndShellTests(unittest.TestCase):
    def test_apply_preserves_unmanaged_content_and_creates_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            paths = AppPaths(home)
            shell_file = home / ".bashrc"
            shell_file.write_text("# user setting\nexport EDITOR=vi\n", encoding="utf-8")
            manager = BackupManager(paths)
            self.assertTrue(apply(shell_file, ToolConfig(), manager))
            result = shell_file.read_text(encoding="utf-8")
            self.assertIn("# user setting", result)
            self.assertIn(START, result)
            self.assertIn(END, result)
            self.assertEqual(len(manager.list()), 1)

    def test_remove_only_removes_managed_block(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            paths = AppPaths(home)
            shell_file = home / ".zshrc"
            shell_file.write_text("before\n" + render_block(ToolConfig()) + "\nafter\n", encoding="utf-8")
            manager = BackupManager(paths)
            self.assertTrue(remove(shell_file, manager))
            result = shell_file.read_text(encoding="utf-8")
            self.assertIn("before", result)
            self.assertIn("after", result)
            self.assertNotIn(START, result)

    def test_restore_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            paths = AppPaths(home)
            manager = BackupManager(paths)
            with self.assertRaises(Exception):
                manager.resolve("../config.json")
