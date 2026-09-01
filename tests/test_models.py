import unittest

from termux_tool.errors import ConfigurationError
from termux_tool.models import ToolConfig


class ToolConfigTests(unittest.TestCase):
    def test_defaults_are_valid_and_serializable(self):
        config = ToolConfig.from_dict(ToolConfig().to_dict())
        self.assertEqual(config.prompt, r"\u@\h:\w\$ ")
        self.assertEqual(config.terminal_colors["background"], "#0D1117")

    def test_rejects_invalid_color(self):
        with self.assertRaises(ConfigurationError):
            ToolConfig.from_dict({"terminal_colors": {"foreground": "red"}})

    def test_rejects_alias_injection_newline(self):
        with self.assertRaises(ConfigurationError):
            ToolConfig.from_dict({"aliases": {"bad\nname": "echo nope"}})
