"""Re-export mount() at module root so amplifier-core's loader validator
finds the package without needing the amplifier_module_* directory rename.

See _find_package_dir() in amplifier_core/loader.py — its first check is
``module_path/__init__.py``. This file satisfies that check; the actual
runtime entry point in pyproject.toml (tool_paperbanana:mount) is unchanged.
"""
from tool_paperbanana import mount, __version__

__all__ = ["mount", "__version__"]
