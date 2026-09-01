from pathlib import Path
import tempfile
import unittest

from termux_tool.backup import BackupManager
from termux_tool.paths import AppPaths
from termux_tool.terminal import update_colors


class TerminalTests(unittest.TestCase):
    def test_color_update_preserves_comments_and_unknown_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            paths = AppPaths(home)
            colors = paths.colors_file
            colors.parent.mkdir()
            colors.write_text("# keep me\nforeground=#ffffff\ncustom=value\n", encoding="utf-8")
            changed = update_colors(
                colors, {"foreground": "#000000", "background": "#111111"},
                BackupManager(paths),
            )
            self.assertTrue(changed)
            content = colors.read_text(encoding="utf-8")
            self.assertIn("# keep me", content)
            self.assertIn("custom=value", content)
            self.assertIn("foreground=#000000", content)
            self.assertIn("background=#111111", content)
            self.assertEqual(len(BackupManager(paths).list()), 1)
