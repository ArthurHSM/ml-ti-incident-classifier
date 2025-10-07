"""Package marker for src.

This makes `src` importable (so tests can import `src.app`).
"""

from . import api  # re-export api package for convenience

__all__ = ["api"]
