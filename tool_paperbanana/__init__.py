"""
PaperBanana: Multi-agent academic illustration generation tool.

Implements the PaperBanana architecture from arXiv 2601.23265.
"""

import logging
from typing import Any

from .mount import PaperBananaToolMount

__version__ = "0.3.0"

__all__ = ["PaperBananaToolMount", "mount"]

logger = logging.getLogger(__name__)


async def mount(coordinator: Any, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Mount the PaperBanana tool into the Amplifier coordinator.

    Registers ``paperbanana_generate_figure`` so that any session loading
    the ``research-paperbanana`` behavior can invoke the 5-stage
    Retriever → Planner → Stylist → Visualizer → Critic pipeline.

    Args:
        coordinator: Amplifier coordinator that accepts tool registrations.
        config: Optional overrides forwarded to ``PaperBananaToolMount``:
            - ``default_max_iterations`` (int): Critic refinement cap (default 3).
            - ``default_quality_rules`` (list[str]): Veto rules to enforce.
            - ``output_dir`` (str): Directory for saved figures (default "figures").

    Returns:
        Metadata dict confirming what was registered.
    """
    tool = PaperBananaToolMount(config=config)
    await coordinator.mount("tools", tool, name=tool.name)
    logger.info("tool-paperbanana mounted: registered '%s'", tool.name)
    return {
        "name": "tool-paperbanana",
        "version": __version__,
        "provides": [tool.name],
    }
