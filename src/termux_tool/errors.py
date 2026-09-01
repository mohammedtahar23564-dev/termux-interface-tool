"""Application-specific exceptions."""


class ToolError(Exception):
    """A safe, user-facing application error."""


class ConfigurationError(ToolError):
    """The local configuration is missing or invalid."""


class SafetyError(ToolError):
    """An operation was rejected by a path or input safety check."""
