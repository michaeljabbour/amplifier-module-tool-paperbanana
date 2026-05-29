"""
PaperBanana Tool Mount: Main entry point implementing Tool protocol.

Orchestrates the 5-agent PaperBanana workflow:
Retriever → Planner → Stylist → Visualizer → Critic
"""

from typing import Any

from amplifier_core import ToolResult

from .critic import Critic
from .planner import Planner
from .retriever import Retriever
from .visualizer import Visualizer


class PaperBananaToolMount:
    """
    Tool mount for PaperBanana multi-agent figure generation.

    Implements the Tool protocol for Amplifier.
    """

    # --- Tool protocol properties ---

    @property
    def name(self) -> str:
        return "paperbanana_generate_figure"

    @property
    def description(self) -> str:
        return (
            "Generate a publication-quality academic figure from paper content using the "
            "PaperBanana multi-agent pipeline (arXiv 2601.23265). "
            "Runs a 5-stage Retriever → Planner → Stylist → Visualizer → Critic workflow "
            "with iterative quality refinement. Use this tool when you need to create "
            "methodology diagrams, result plots, or architecture figures for a research paper."
        )

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "paper_content": {
                    "type": "string",
                    "description": (
                        "Paper text to generate a figure for — typically the abstract "
                        "plus the methods section. Required."
                    ),
                },
                "figure_type": {
                    "type": "string",
                    "enum": ["methodology", "plot", "architecture"],
                    "description": (
                        "Kind of figure to produce. "
                        "'methodology' for pipeline/workflow diagrams, "
                        "'plot' for data/results charts, "
                        "'architecture' for system-design figures."
                    ),
                },
                "style_requirements": {
                    "type": "object",
                    "description": (
                        "Optional visual style overrides. Recognised keys: "
                        "'conference' (e.g. 'NeurIPS', 'ICML'), "
                        "'colorblind_safe' (bool), "
                        "'width' (column width in inches, e.g. 3.5 for single-column)."
                    ),
                    "properties": {
                        "conference": {"type": "string"},
                        "colorblind_safe": {"type": "boolean"},
                        "width": {"type": "number"},
                    },
                },
                "quality_rules": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of quality veto rules the Critic must enforce. "
                        "Defaults to the module's built-in ruleset when omitted: "
                        "no_low_quality_artifacts, professional_colors, no_black_backgrounds, "
                        "modern_style, vector_preferred, appropriate_aspect_ratio, "
                        "clear_labels, data_integrity."
                    ),
                },
                "max_iterations": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": (
                        "Maximum Critic→Visualizer refinement iterations (default: 3)."
                    ),
                },
            },
            "required": ["paper_content"],
        }

    # --- Initialisation ---

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize PaperBanana tool with configuration.

        Args:
            config: Optional configuration dict with:
                - default_max_iterations: Max refinement iterations (default: 3)
                - default_quality_rules: Quality rules to enforce
                - output_dir: Directory for generated figures (default: "figures")
        """
        self.config = config or {}
        self.default_max_iterations = self.config.get("default_max_iterations", 3)
        self.default_quality_rules = self.config.get(
            "default_quality_rules",
            [
                "no_low_quality_artifacts",
                "professional_colors",
                "no_black_backgrounds",
                "modern_style",
                "vector_preferred",
                "appropriate_aspect_ratio",
                "clear_labels",
                "data_integrity",
            ],
        )
        self.output_dir = self.config.get("output_dir", "figures")

        # Initialize components
        self.retriever = Retriever()
        self.planner = Planner()
        self.visualizer = Visualizer(output_dir=self.output_dir)
        self.critic = Critic()

    # --- Tool protocol execute ---

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        """
        Execute PaperBanana workflow to generate a figure.

        Args:
            input_data: Dict with:
                - paper_content: str (required) - Paper text (abstract + methods)
                - figure_type: str - "methodology" | "plot" | "architecture"
                - style_requirements: dict - Conference, colorblind_safe, width
                - quality_rules: list[str] - Veto rules to enforce
                - max_iterations: int - Refinement attempts

        Returns:
            ToolResult whose .output dict contains:
                - figure_path: str (if success)
                - format: str (if success)
                - metadata: dict
                - error: str (if failure)
        """
        try:
            # Extract and validate inputs
            paper_content = input_data.get("paper_content", "")
            if not paper_content:
                return ToolResult(
                    success=False,
                    output={"error": "paper_content is required"},
                )

            style_requirements = input_data.get("style_requirements", {})
            quality_rules = input_data.get("quality_rules", self.default_quality_rules)
            max_iterations = input_data.get("max_iterations", self.default_max_iterations)

            # STAGE 1: Retrieve context from paper
            context = self.retriever.extract(paper_content)

            # STAGE 2: Plan content (what to include)
            content_plan = self.planner.plan_content(context)

            # STAGE 3: Plan style (visual aesthetics)
            style_plan = self.planner.plan_style(context, style_requirements)

            # STAGE 4: Generate initial figure
            figure = self.visualizer.generate(content_plan, style_plan)

            # STAGE 5: Iterative refinement with critic
            critique = None
            iteration_count = 0

            for i in range(max_iterations):
                iteration_count = i + 1

                # Evaluate quality
                critique = self.critic.evaluate(figure, quality_rules)

                if critique.passed:
                    # Quality check passed!
                    break

                if i < max_iterations - 1:
                    # Try to refine
                    figure = self.visualizer.refine(figure, critique)

            # Return results
            if critique:
                return ToolResult(
                    success=critique.passed,
                    output={
                        "figure_path": figure.path,
                        "format": figure.format,
                        "metadata": {
                            "iterations": iteration_count,
                            "rules_passed": critique.passed_rules,
                            "rules_failed": critique.failed_rules,
                            "critique": critique.summary,
                            "severity": critique.severity,
                            "width_inches": figure.width_inches,
                            "height_inches": figure.height_inches,
                            "num_elements": figure.metadata.get("num_elements", 0),
                            "layout": figure.metadata.get("layout", "unknown"),
                        },
                        "error": (
                            None if critique.passed else f"Quality issues: {critique.severity}"
                        ),
                    },
                )
            else:
                # No critique (shouldn't happen with max_iterations >= 1)
                return ToolResult(
                    success=True,
                    output={
                        "figure_path": figure.path,
                        "format": figure.format,
                        "metadata": {
                            "iterations": iteration_count,
                            "width_inches": figure.width_inches,
                            "height_inches": figure.height_inches,
                        },
                    },
                )

        except Exception as e:
            return ToolResult(
                success=False,
                output={"error": f"PaperBanana execution failed: {str(e)}"},
            )

    def execute_sync(self, input_data: dict[str, Any]) -> ToolResult:
        """
        Synchronous version of execute (for compatibility).

        Args:
            input_data: Same as execute()

        Returns:
            ToolResult — same as execute()
        """
        import asyncio

        # Run async execute in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.execute(input_data))
