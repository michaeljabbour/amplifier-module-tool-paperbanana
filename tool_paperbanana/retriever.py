"""
Retriever Agent: Extract relevant information from paper content.

Implements the first stage of the PaperBanana multi-agent architecture.
"""

import re

from .utils import PaperContext


class Retriever:
    """Extract context from paper content for figure generation."""

    def extract(self, paper_content: str) -> PaperContext:
        """
        Extract relevant information from paper text.

        Args:
            paper_content: Paper abstract and methods sections

        Returns:
            PaperContext with extracted information
        """
        # Extract key concepts (capitalized terms, technical terms)
        key_concepts = self._extract_key_concepts(paper_content)

        # Extract methodology description
        methodology = self._extract_methodology(paper_content)

        # Extract relationships between concepts
        relationships = self._extract_relationships(paper_content, key_concepts)

        # Build terminology dictionary
        terminology = self._extract_terminology(paper_content, key_concepts)

        # Identify visual elements that should be included
        visual_elements = self._identify_visual_elements(paper_content)

        return PaperContext(
            key_concepts=key_concepts,
            methodology=methodology,
            relationships=relationships,
            terminology=terminology,
            visual_elements=visual_elements,
        )

    def _extract_key_concepts(self, text: str) -> list[str]:
        """Extract key technical terms and concepts."""
        # Find capitalized terms (potential proper nouns/technical terms)
        capitalized = re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b", text)

        # Find terms in quotes or emphasized
        quoted = re.findall(r'"([^"]+)"', text)
        emphasized = re.findall(r"\*\*([^*]+)\*\*", text)

        # Combine and deduplicate
        concepts = list(set(capitalized + quoted + emphasized))

        # Filter out common words
        common_words = {
            "Abstract",
            "Introduction",
            "Methods",
            "Results",
            "Discussion",
            "The",
            "We",
            "Our",
            "This",
            "These",
        }
        concepts = [c for c in concepts if c not in common_words]

        # Limit to top concepts (by frequency)
        concept_freq = {c: text.count(c) for c in concepts}
        sorted_concepts = sorted(concept_freq.items(), key=lambda x: x[1], reverse=True)

        return [c for c, _ in sorted_concepts[:15]]  # Top 15 concepts

    def _extract_methodology(self, text: str) -> str:
        """Extract methodology description from paper."""
        # Look for methods/approach section
        methods_patterns = [
            r"Methods?:?\s+(.*?)(?:Results?:|Discussion:|$)",
            r"Approach:?\s+(.*?)(?:Results?:|Discussion:|$)",
            r"Methodology:?\s+(.*?)(?:Results?:|Discussion:|$)",
        ]

        for pattern in methods_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                methodology = match.group(1).strip()
                # Limit length
                if len(methodology) > 500:
                    methodology = methodology[:500] + "..."
                return methodology

        # If no explicit methods section, use first 300 chars after abstract
        abstract_end = text.find("Abstract:") + len("Abstract:")
        if abstract_end > len("Abstract:"):
            return text[abstract_end : abstract_end + 300].strip() + "..."

        return text[:300].strip() + "..."

    def _extract_relationships(self, text: str, concepts: list[str]) -> list[tuple[str, str, str]]:
        """Extract relationships between concepts (for diagram arrows)."""
        relationships = []

        # Common relationship indicators
        relationship_patterns = [
            (r"(\w+)\s+(?:uses|utilizes|employs)\s+(\w+)", "uses"),
            (r"(\w+)\s+(?:consists of|comprises)\s+(\w+)", "contains"),
            (r"(\w+)\s+(?:feeds into|flows to)\s+(\w+)", "flows_to"),
            (r"(\w+)\s+(?:processes|transforms)\s+(\w+)", "processes"),
            (r"(\w+)\s+(?:generates|produces)\s+(\w+)", "generates"),
        ]

        for pattern, rel_type in relationship_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for source, target in matches:
                # Check if source and target are in our key concepts
                source_match = next((c for c in concepts if c.lower() in source.lower()), None)
                target_match = next((c for c in concepts if c.lower() in target.lower()), None)

                if source_match and target_match:
                    relationships.append((source_match, rel_type, target_match))

        return relationships[:10]  # Limit to avoid clutter

    def _extract_terminology(self, text: str, concepts: list[str]) -> dict[str, str]:
        """Build terminology dictionary for tooltips/legends."""
        terminology = {}

        for concept in concepts:
            # Look for definition patterns near the concept
            patterns = [
                rf"{concept}\s+(?:is|refers to|means)\s+([^.]+)\.",
                rf"(?:We define|We call)\s+{concept}\s+as\s+([^.]+)\.",
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    definition = match.group(1).strip()
                    terminology[concept] = definition
                    break

        return terminology

    def _identify_visual_elements(self, text: str) -> list[str]:
        """Identify what visual elements should be included."""
        elements = []

        # Look for mentions of visual components
        visual_keywords = {
            "diagram": ["boxes", "arrows", "flowchart"],
            "graph": ["nodes", "edges", "network"],
            "plot": ["line", "scatter", "bar", "curve"],
            "architecture": ["layers", "modules", "components"],
            "pipeline": ["stages", "steps", "phases"],
        }

        text_lower = text.lower()

        for category, keywords in visual_keywords.items():
            if category in text_lower:
                elements.append(category)
                for keyword in keywords:
                    if keyword in text_lower:
                        elements.append(keyword)

        return list(set(elements))
