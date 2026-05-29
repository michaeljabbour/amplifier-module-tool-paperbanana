"""
Planner Agent: Plan content and style for the figure.

Implements the second stage of the PaperBanana multi-agent architecture.
"""

from .utils import (
    COLORBLIND_SAFE_PALETTES,
    CONFERENCE_SPECS,
    ContentPlan,
    PaperContext,
    StylePlan,
    get_conference_width,
)


class Planner:
    """Plan content and style for figure generation."""

    def plan_content(self, context: PaperContext) -> ContentPlan:
        """
        Plan what content to include in the figure.

        Args:
            context: Extracted paper context

        Returns:
            ContentPlan with elements, hierarchy, relationships, labels
        """
        # Determine what elements to include based on context
        elements = self._select_elements(context)

        # Establish visual hierarchy (what's most important)
        hierarchy = self._establish_hierarchy(elements, context)

        # Map relationships for arrows/connections
        relationships = self._map_relationships(context.relationships, elements)

        # Generate labels for each element
        labels = self._generate_labels(elements, context.terminology)

        return ContentPlan(
            elements=elements, hierarchy=hierarchy, relationships=relationships, labels=labels
        )

    def plan_style(
        self, context: PaperContext, style_requirements: dict[str, str | bool]
    ) -> StylePlan:
        """
        Plan visual aesthetics for the figure.

        Args:
            context: Extracted paper context
            style_requirements: Conference, colorblind_safe, width

        Returns:
            StylePlan with colors, fonts, layout, dimensions, format
        """
        conference_raw = style_requirements.get("conference", "neurips")
        conference = str(conference_raw) if conference_raw else "neurips"

        colorblind_safe_raw = style_requirements.get("colorblind_safe", True)
        colorblind_safe = bool(colorblind_safe_raw)

        width_type_raw = style_requirements.get("width", "column")
        width_type = str(width_type_raw) if width_type_raw else "column"

        # Select color scheme
        color_scheme = self._select_color_scheme(colorblind_safe, len(context.key_concepts))

        # Choose font based on conference
        font_family = self._select_font(conference)
        font_size = self._select_font_size(width_type)

        # Determine layout based on visual elements
        layout = self._determine_layout(context.visual_elements)

        # Calculate dimensions
        width_inches = get_conference_width(conference, width_type)
        height_inches = self._calculate_height(width_inches, layout)

        # Select output format
        format_type = "pdf"  # Vector preferred per quality rules

        return StylePlan(
            color_scheme=color_scheme,
            font_family=font_family,
            font_size=font_size,
            layout=layout,
            width_inches=width_inches,
            height_inches=height_inches,
            format=format_type,
        )

    def _select_elements(self, context: PaperContext) -> list[str]:
        """Select which elements to include in the figure."""
        # Start with key concepts
        elements = context.key_concepts[:8]  # Limit to avoid clutter

        # Add visual elements if they're mentioned
        if "pipeline" in context.visual_elements or "stages" in context.visual_elements:
            # Add stage boxes
            elements.extend([f"Stage {i + 1}" for i in range(3)])

        return elements

    def _establish_hierarchy(self, elements: list[str], context: PaperContext) -> dict[str, int]:
        """Establish visual hierarchy (priority levels)."""
        hierarchy = {}

        # Primary elements (mentioned in relationships)
        primary = set()
        for source, _, target in context.relationships:
            primary.add(source)
            primary.add(target)

        for element in elements:
            if element in primary:
                hierarchy[element] = 1  # High priority
            else:
                hierarchy[element] = 2  # Secondary

        return hierarchy

    def _map_relationships(
        self, all_relationships: list[tuple[str, str, str]], selected_elements: list[str]
    ) -> list[tuple[str, str]]:
        """Map relationships between selected elements (for arrows)."""
        relationships = []

        for source, _, target in all_relationships:
            if source in selected_elements and target in selected_elements:
                relationships.append((source, target))

        return relationships

    def _generate_labels(self, elements: list[str], terminology: dict[str, str]) -> dict[str, str]:
        """Generate labels for each element."""
        labels = {}

        for element in elements:
            # Use terminology definition if available, otherwise use element name
            if element in terminology:
                # Truncate long definitions
                definition = terminology[element]
                if len(definition) > 50:
                    definition = definition[:47] + "..."
                labels[element] = f"{element}\n({definition})"
            else:
                labels[element] = element

        return labels

    def _select_color_scheme(self, colorblind_safe: bool, num_colors: int) -> list[str]:
        """Select appropriate color palette."""
        if colorblind_safe:
            # Use ColorBrewer colorblind-safe palette
            palette = COLORBLIND_SAFE_PALETTES["qualitative"][0]
        else:
            # Use default matplotlib colors
            palette = [
                "#1f77b4",
                "#ff7f0e",
                "#2ca02c",
                "#d62728",
                "#9467bd",
                "#8c564b",
                "#e377c2",
                "#7f7f7f",
            ]

        # Extend palette if needed
        while len(palette) < num_colors:
            palette.extend(palette)

        return palette[:num_colors]

    def _select_font(self, conference: str) -> str:
        """Select font family based on conference."""
        if conference in CONFERENCE_SPECS:
            preferred = CONFERENCE_SPECS[conference]["preferred_fonts"]
            return preferred[0] if preferred else "Times"
        return "Times"

    def _select_font_size(self, width_type: str) -> int:
        """Select appropriate font size."""
        if width_type == "column":
            return 8  # Smaller for column width
        else:
            return 10  # Larger for full page width

    def _determine_layout(self, visual_elements: list[str]) -> str:
        """Determine layout based on figure type."""
        if "pipeline" in visual_elements or "stages" in visual_elements:
            return "horizontal"
        elif "architecture" in visual_elements or "layers" in visual_elements:
            return "vertical"
        elif "graph" in visual_elements or "network" in visual_elements:
            return "grid"
        else:
            return "horizontal"  # Default

    def _calculate_height(self, width: float, layout: str) -> float:
        """Calculate appropriate height based on width and layout."""
        if layout == "horizontal":
            return width * 0.4  # Wide aspect ratio
        elif layout == "vertical":
            return width * 1.2  # Tall aspect ratio
        else:
            return width * 0.75  # Square-ish
