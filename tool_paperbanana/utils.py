"""
Shared utilities and data structures for PaperBanana tool.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class QualityRule:
    """Quality veto rule from PaperBanana research."""

    name: str
    description: str
    check_function: str  # Name of function to call for validation


# 8 Quality Veto Rules from PaperBanana (arXiv 2601.23265)
QUALITY_RULES = [
    QualityRule(
        name="no_low_quality_artifacts",
        description="No visible grid artifacts, blur, or distortion",
        check_function="check_artifacts",
    ),
    QualityRule(
        name="professional_colors",
        description="No neon colors, proper color balance, use ColorBrewer palettes",
        check_function="check_colors",
    ),
    QualityRule(
        name="no_black_backgrounds",
        description="Avoid unprofessional black backgrounds",
        check_function="check_background",
    ),
    QualityRule(
        name="modern_style",
        description="Appropriate fonts (no Comic Sans), minimal clip-art",
        check_function="check_style",
    ),
    QualityRule(
        name="vector_preferred",
        description="Use PDF/SVG over raster when possible",
        check_function="check_format",
    ),
    QualityRule(
        name="appropriate_aspect_ratio",
        description="Match conference column/page width requirements",
        check_function="check_aspect_ratio",
    ),
    QualityRule(
        name="clear_labels",
        description="All axes, legends, captions legible at print size",
        check_function="check_labels",
    ),
    QualityRule(
        name="data_integrity",
        description="Accurate representation of data, no misleading visualizations",
        check_function="check_data_integrity",
    ),
]


@dataclass
class PaperContext:
    """Extracted context from paper content."""

    key_concepts: list[str]
    methodology: str
    relationships: list[tuple[str, str, str]]  # (source, relationship, target)
    terminology: dict[str, str]  # term -> definition
    visual_elements: list[str]  # boxes, arrows, graphs, etc.


@dataclass
class ContentPlan:
    """Plan for what to include in the figure."""

    elements: list[str]
    hierarchy: dict[str, int]  # element -> priority level
    relationships: list[tuple[str, str]]  # (source, target)
    labels: dict[str, str]  # element -> label text


@dataclass
class StylePlan:
    """Plan for visual aesthetics."""

    color_scheme: list[str]  # Hex color codes
    font_family: str
    font_size: int
    layout: str  # "horizontal" | "vertical" | "grid"
    width_inches: float
    height_inches: float
    format: str  # "pdf" | "tikz" | "svg" | "png"


@dataclass
class Figure:
    """Generated figure."""

    path: str
    format: str
    width_inches: float
    height_inches: float
    metadata: dict[str, Any]


@dataclass
class Critique:
    """Quality validation results."""

    passed: bool
    passed_rules: list[str]
    failed_rules: list[str]
    issues: list[dict[str, str]]  # [{"rule": str, "severity": str, "description": str}]
    summary: str
    severity: str  # "pass" | "minor" | "major" | "critical"


# Conference-specific requirements
CONFERENCE_SPECS = {
    "neurips": {
        "column_width_inches": 5.5,
        "page_width_inches": 5.5,
        "text_height_inches": 9.0,
        "preferred_fonts": ["Times", "Computer Modern"],
    },
    "icml": {
        "column_width_inches": 3.25,
        "page_width_inches": 6.75,
        "text_height_inches": 9.0,
        "preferred_fonts": ["Times"],
    },
    "ieee": {
        "column_width_inches": 3.5,
        "page_width_inches": 7.0,
        "text_height_inches": 9.0,
        "preferred_fonts": ["Times"],
    },
    "acl": {
        "column_width_inches": 3.33,
        "page_width_inches": 6.75,
        "text_height_inches": 9.45,
        "preferred_fonts": ["Times"],
    },
    "acm": {
        "column_width_inches": 3.33,
        "page_width_inches": 6.75,
        "text_height_inches": 9.0,
        "preferred_fonts": ["Libertine"],
    },
}


# ColorBrewer palettes (colorblind-safe)
COLORBLIND_SAFE_PALETTES = {
    "qualitative": [
        ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],  # Default matplotlib
        ["#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3"],  # Pastel
        ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00"],  # Set1
    ],
    "sequential": [
        ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6"],  # Blues
        ["#fff5eb", "#fee6ce", "#fdd0a2", "#fdae6b", "#fd8d3c"],  # Oranges
    ],
}


def get_conference_width(conference: str, width_type: str = "column") -> float:
    """Get width in inches for a given conference and width type."""
    if conference not in CONFERENCE_SPECS:
        # Default to NeurIPS single-column
        return 5.5

    spec = CONFERENCE_SPECS[conference]
    if width_type == "page":
        return spec["page_width_inches"]
    else:
        return spec["column_width_inches"]
