"""
Visualizer Agent: Generate figures using Gemini/Imagen image generation.

Implements the fourth stage of the PaperBanana multi-agent architecture.
Uses Imagen 4 (Google's image generation model) for methodology diagrams.
"""

import os
from pathlib import Path

from .utils import ContentPlan, Critique, Figure, StylePlan


class Visualizer:
    """Generate figures using Gemini/Imagen image generation API."""

    def __init__(self, output_dir: str = "figures", gemini_api_key: str | None = None):
        """
        Initialize visualizer with Gemini API.

        Args:
            output_dir: Directory for generated figures
            gemini_api_key: Google API key (or set GOOGLE_API_KEY env var)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Get API key
        api_key = gemini_api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Google API key required. Set GOOGLE_API_KEY environment variable "
                "or pass gemini_api_key parameter."
            )

        # Initialize Gemini client
        try:
            from google import genai

            self.client = genai.Client(api_key=api_key)
            self.genai = genai
        except ImportError as e:
            raise RuntimeError(
                "google-genai package required. Install: pip install google-genai"
            ) from e

    def generate(self, content_plan: ContentPlan, style_plan: StylePlan) -> Figure:
        """
        Generate figure using Gemini/Imagen (REAL PaperBanana approach).

        Args:
            content_plan: What to include
            style_plan: Visual aesthetics

        Returns:
            Figure object with path
        """
        from google.genai import types

        # Build detailed prompt from plans
        prompt = self._build_image_generation_prompt(content_plan, style_plan)

        # Generate with Imagen 4
        response = self.client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=self._calculate_aspect_ratio(style_plan),
            ),
        )

        if not response.generated_images:
            raise RuntimeError("No images generated")

        # Extract and save image
        generated = response.generated_images[0]
        output_path = self.output_dir / f"figure_{os.getpid()}.png"

        # Extract image bytes correctly
        if not generated.image:
            raise RuntimeError("No image object in generated response")

        img_dict = generated.image.model_dump()
        if "image_bytes" not in img_dict or not img_dict["image_bytes"]:
            raise RuntimeError("No image_bytes in response")

        # Write image
        with output_path.open("wb") as f:
            f.write(img_dict["image_bytes"])

        return Figure(
            path=str(output_path),
            format="png",
            width_inches=style_plan.width_inches,
            height_inches=style_plan.height_inches,
            metadata={
                "model": "imagen-4.0-generate-001",
                "prompt_length": len(prompt),
                "num_elements": len(content_plan.elements),
                "layout": style_plan.layout,
                "generation_method": "gemini_image_generation",
            },
        )

    def refine(self, figure: Figure, critique: Critique) -> Figure:
        """
        Refine figure based on critique (iterative PaperBanana loop).

        Args:
            figure: Current figure
            critique: Quality validation

        Returns:
            Refined figure
        """
        if critique.passed:
            return figure

        from google.genai import types

        # Build refinement prompt
        refinement_prompt = self._build_refinement_prompt(figure, critique)

        try:
            response = self.client.models.generate_images(
                model="imagen-4.0-generate-001",
                prompt=refinement_prompt,
                config=types.GenerateImagesConfig(number_of_images=1),
            )

            if not response.generated_images:
                return figure

            # Extract and save refined image
            generated = response.generated_images[0]
            if not generated.image:
                return figure

            img_dict = generated.image.model_dump()

            if "image_bytes" in img_dict and img_dict["image_bytes"]:
                output_path = Path(figure.path)
                with output_path.open("wb") as f:
                    f.write(img_dict["image_bytes"])

                # Update metadata
                figure.metadata["refined"] = True
                figure.metadata["refinement_iteration"] = (
                    figure.metadata.get("refinement_iteration", 0) + 1
                )

            return figure

        except Exception:
            return figure  # Keep original if refinement fails

    def _build_image_generation_prompt(
        self, content_plan: ContentPlan, style_plan: StylePlan
    ) -> str:
        """
        Build detailed textual specification for Gemini image generation.

        This implements PaperBanana's Planner → Stylist → Visualizer flow.
        """
        prompt_parts = [
            f"Generate a professional academic {style_plan.layout} diagram "
            "for a NeurIPS research paper.",
            "",
            "DIAGRAM STRUCTURE:",
        ]

        # Elements with hierarchy
        for i, element in enumerate(content_plan.elements, 1):
            label = content_plan.labels.get(element, element)
            priority = content_plan.hierarchy.get(element, 2)
            if priority == 1:
                emphasis = "PRIMARY (larger, emphasized)"
            else:
                emphasis = "secondary"
            prompt_parts.append(f"{i}. '{label}' [{emphasis}]")

        # Relationships
        if content_plan.relationships:
            prompt_parts.append("")
            prompt_parts.append("CONNECTIONS:")
            for source, target in content_plan.relationships:
                prompt_parts.append(f"  → {source} connects to {target} with curved arrow")

        # Visual style (PaperBanana aesthetic guidelines)
        prompt_parts.extend(
            [
                "",
                "VISUAL STYLE:",
                f"- Layout arrangement: {style_plan.layout} (layered if methodology)",
                "- Shape: Rounded rectangles with soft shadows",
                "- Colors: Professional academic palette:",
                "  * Core/foundational elements: soft blue (#E8F4F8 fill, #2C5F7B border)",
                "  * Process/dynamic elements: soft yellow (#FFF9C4 fill, #F57F17 border)",
                "  * Emergent/advanced elements: soft pink (#F8BBD0 fill, #C2185B border)",
                "- Arrows: Smooth curved arrows, medium gray color",
                "- Typography: Serif font (Times-like), clear and legible",
                f"- Font size: {style_plan.font_size}pt minimum",
                "- Background: Clean white",
                "- Spacing: Generous white space, not crowded",
                "",
                "QUALITY REQUIREMENTS:",
                "- Modern academic aesthetics (NeurIPS 2025 style)",
                "- Publication-ready professional appearance",
                "- Clear visual hierarchy and grouping",
                "- Colorblind-safe palette",
                "- High resolution for print quality",
                "- Clean, sophisticated design",
                "",
                "AVOID:",
                "- PowerPoint clipart or generic shapes",
                "- Neon or overly bright colors",
                "- Black backgrounds",
                "- Cluttered or busy layouts",
                "- Comic Sans or informal typography",
                "- Low-quality artifacts or pixelation",
            ]
        )

        return "\n".join(prompt_parts)

    def _build_refinement_prompt(self, figure: Figure, critique: Critique) -> str:
        """Build refinement prompt with critic feedback."""
        prompt_parts = [
            "REFINE the academic diagram to address quality issues while maintaining structure.",
            "",
            "CRITIQUE SUMMARY:",
            critique.summary,
            "",
            "ISSUES TO FIX:",
        ]

        for issue in critique.issues:
            rule = issue.get("rule", "unknown")
            desc = issue.get("description", "")
            severity = issue.get("severity", "minor")
            prompt_parts.append(f"  [{severity.upper()}] {rule}: {desc}")

        prompt_parts.extend(
            [
                "",
                "REFINEMENT GOALS:",
                "- Fix all identified issues",
                "- Maintain overall content and structure",
                "- Improve professional quality",
                "- Ensure publication-ready appearance",
                "",
                "Generate an improved version with these fixes applied.",
            ]
        )

        return "\n".join(prompt_parts)

    def _calculate_aspect_ratio(self, style_plan: StylePlan) -> str:
        """Map dimensions to Gemini aspect ratio."""
        ratio = style_plan.width_inches / style_plan.height_inches

        if ratio > 1.5:
            return "16:9"
        elif ratio > 1.2:
            return "3:2"
        elif ratio < 0.7:
            return "2:3"
        elif ratio < 0.8:
            return "9:16"
        else:
            return "1:1"
