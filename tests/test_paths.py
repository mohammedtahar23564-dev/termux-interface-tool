import os
from pathlib import Path
import tempfile
import unittest

from termux_tool.errors import SafetyError
from termux_tool.paths import AppPaths, ensure_within, is_termux


class PathTests(unittest.TestCase):
    def test_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(SafetyError):
                ensure_within(root / ".." / "outside", root)

    def test_termux_markers(self):
        self.assertTrue(is_termux({"PREFIX": "/data/data/com.termux/files/usr"}))
        self.assertFalse(is_termux({"PREFIX": "/usr/local", "TERMUX_VERSION": ""}))
