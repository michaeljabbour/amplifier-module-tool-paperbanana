"""Basic sanity tests for tool-paperbanana.

These tests don't exercise the figure-generation pipeline (which requires
matplotlib + LaTeX + working models). They establish the floor: the package
imports cleanly, the manifest is well-formed, the entry-point modules are
discoverable. Anything more invasive belongs in an integration test that
runs against a real Amplifier session.

Layout note: tool-paperbanana uses the FLAT layout (`tool_paperbanana/`
at module root) rather than the src/ layout used by tool-experiment-*.
Both are valid; tests reflect actual structure.
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import pytest

PKG_ROOT = Path(__file__).resolve().parents[1]


# -----------------------------------------------------------------
# Package imports
# -----------------------------------------------------------------

def test_package_imports_cleanly():
    """The top-level package imports without side-effect errors."""
    pkg = importlib.import_module("tool_paperbanana")
    assert pkg is not None


def test_mount_function_exposed_at_package_level():
    """The pyproject entry-point declares `tool-paperbanana = "tool_paperbanana:mount"`.
    `mount` must be importable as `tool_paperbanana.mount` (the function, not the
    submodule)."""
    pkg = importlib.import_module("tool_paperbanana")
    assert hasattr(pkg, "mount"), (
        "tool_paperbanana package must expose a `mount` symbol "
        "(per the pyproject.toml entry-point declaration)"
    )
    # And it must be callable
    mount = pkg.mount
    assert callable(mount), "tool_paperbanana.mount must be callable"


def test_mount_submodule_importable():
    """The mount.py submodule is also importable in its own right."""
    sub = importlib.import_module("tool_paperbanana.mount")
    assert sub is not None


def test_internal_modules_import():
    """The 5 internal modules (per the methodology) all import without error."""
    for name in ("retriever", "planner", "visualizer", "critic", "utils"):
        importlib.import_module(f"tool_paperbanana.{name}")


# -----------------------------------------------------------------
# Project structure
# -----------------------------------------------------------------

def test_pyproject_toml_present_and_well_formed():
    """pyproject.toml exists, declares the package name, and lists the
    expected entry-point."""
    pp = PKG_ROOT / "pyproject.toml"
    assert pp.exists(), "tool-paperbanana must have pyproject.toml"
    text = pp.read_text()
    assert 'name = "tool-paperbanana"' in text, "pyproject must name the package"
    assert "amplifier.modules" in text, (
        "pyproject must declare the amplifier.modules entry-point group"
    )
    assert 'tool-paperbanana = "tool_paperbanana:mount"' in text, (
        "pyproject must declare the mount entry point"
    )


def test_flat_layout_package_present():
    """tool-paperbanana uses flat layout: tool_paperbanana/ at module root."""
    pkg = PKG_ROOT / "tool_paperbanana"
    assert pkg.is_dir(), f"expected flat layout at {pkg}"
    assert (pkg / "__init__.py").exists()
    # 5 expected internal modules
    for name in ("retriever.py", "planner.py", "visualizer.py", "critic.py", "utils.py", "mount.py"):
        assert (pkg / name).exists(), f"missing internal module: {name}"


# -----------------------------------------------------------------
# Mount contract
# -----------------------------------------------------------------

def test_mount_signature_matches_kernel_contract():
    """The mount() callable must accept (coordinator, config) per the kernel contract."""
    pkg = importlib.import_module("tool_paperbanana")
    mount = pkg.mount

    # mount may be a function, a class with __call__, or a static method
    if inspect.isclass(mount):
        # if a class, check __call__
        sig = inspect.signature(mount.__call__)
    else:
        sig = inspect.signature(mount)
    params = [p for p in sig.parameters.keys() if p != "self"]
    assert len(params) >= 2, (
        f"mount must take at least (coordinator, config); got {params}"
    )


# -----------------------------------------------------------------
# Methodology constants (sanity check on PaperBanana veto rules)
# -----------------------------------------------------------------

def test_quality_veto_rules_documented_in_methodology():
    """The PaperBanana methodology document must enumerate the 8 quality
    veto rules. This is a static check on the behavior contract that
    the rest of the bundle's figure-generation discipline depends on."""
    methodology = Path(__file__).resolve().parents[3] / (
        "context/figure-generation/paperbanana-methodology.md"
    )
    if not methodology.exists():
        pytest.skip(f"methodology doc not at {methodology}")
    text = methodology.read_text()
    # Each of the 8 numbered veto rules should be present (as ### N. or ## N.)
    for n in range(1, 9):
        assert (f"### {n}." in text) or (f"## {n}." in text), (
            f"PaperBanana methodology missing veto rule #{n}"
        )
