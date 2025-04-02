"""KernelView - System information tool with Debian-themed output."""

from .core import get_system_info, display_system_info  # Import key functions
from .cli import main  # Import the CLI entry point

__version__ = "1.0.0"  # Match version in pyproject.toml
__all__ = ["get_system_info", "display_system_info", "main"]  # Public API