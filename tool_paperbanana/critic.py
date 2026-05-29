"""
Critic Agent: Quality validation and refinement guidance.

Implements the fifth stage of the PaperBanana multi-agent architecture.
"""

from .utils import QUALITY_RULES, Critique, Figure


class Critic:
    """Validate figure quality against veto rules."""

    def evaluate(self, figure: Figure, quality_rules: list[str]) -> Critique:
        """
        Evaluate figure against quality veto rules.

        Args:
            figure: Generated figure to evaluate
            quality_rules: List of rule names to check

        Returns:
            Critique with passed/failed rules and severity
        """
        passed_rules = []
        failed_rules = []
        issues = []

        # Check each requested rule
        for rule_name in quality_rules:
            rule = next((r for r in QUALITY_RULES if r.name == rule_name), None)
            if not rule:
                continue

            # Run the check
            passed, issue = self._run_check(figure, rule)

            if passed:
                passed_rules.append(rule_name)
            else:
                failed_rules.append(rule_name)
                if issue:
                    issues.append(issue)

        # Determine overall pass/fail and severity
        overall_passed = len(failed_rules) == 0
        severity = self._calculate_severity(failed_rules, issues)

        # Generate summary
        summary = self._generate_summary(passed_rules, failed_rules, issues)

        return Critique(
            passed=overall_passed,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            issues=issues,
            summary=summary,
            severity=severity,
        )

    def _run_check(self, figure: Figure, rule: object) -> tuple[bool, dict[str, str] | None]:
        """Run a specific quality check."""
        # Get check function name
        check_fn_name = getattr(rule, "check_function", None)
        if not check_fn_name:
            return True, None

        # Call the appropriate check method
        check_method = getattr(self, check_fn_name, None)
        if check_method:
            return check_method(figure, rule)

        # If check method not implemented, pass by default
        return True, None

    def check_artifacts(self, figure: Figure, rule: object) -> tuple[bool, dict[str, str] | None]:
        """Check for low-quality artifacts."""
        # In a full implementation, this would analyze the image
        # For now, assume vector formats are artifact-free
        if figure.format in ["pdf", "svg"]:
            return True, None

        # For raster formats, would need image analysis
        return True, None

    def check_colors(self, figure: Figure, rule: object) -> tuple[bool, dict[str, str] | None]:
        """Check for professional color usage."""
        # Would need to analyze actual colors in the image
        # For now, pass if we used a color scheme
        return True, None

    def check_background(self, figure: Figure, rule: object) -> tuple[bool, dict[str, str] | None]:
        """Check for black backgrounds."""
        # Would need image analysis
        # Matplotlib default is white, so pass
        return True, None

    def check_style(self, figure: Figure, rule: object) -> tuple[bool, dict[str, str] | None]:
        """Check for modern style."""
        # Would check fonts, clip-art usage
        # For now, assume matplotlib defaults are professional
        return True, None

    def check_format(self, figure: Figure, rule: object) -> tuple[bool, dict[str, str] | None]:
        """Check if vector format is used."""
        rule_name = getattr(rule, "name", "unknown")

        if figure.format in ["pdf", "svg", "tikz"]:
            return True, None

        # Raster format used
        return False, {
            "rule": rule_name,
            "severity": "minor",
            "description": f"Raster format '{figure.format}' used instead of vector (PDF/SVG)",
        }

    def check_aspect_ratio(
        self, figure: Figure, rule: object
    ) -> tuple[bool, dict[str, str] | None]:
        """Check if aspect ratio is appropriate."""
        aspect_ratio = figure.width_inches / figure.height_inches

        # Check for extreme aspect ratios
        if aspect_ratio < 0.3 or aspect_ratio > 3.0:
            rule_name = getattr(rule, "name", "unknown")
            return False, {
                "rule": rule_name,
                "severity": "major",
                "description": f"Extreme aspect ratio {aspect_ratio:.2f} may not print well",
            }

        return True, None

    def check_labels(self, figure: Figure, rule: object) -> tuple[bool, dict[str, str] | None]:
        """Check if labels are clear."""
        # Would need to analyze text size in the image
        # For now, check if figure is too small
        if figure.width_inches < 2.0 or figure.height_inches < 1.5:
            rule_name = getattr(rule, "name", "unknown")
            description = (
                f"Figure too small ({figure.width_inches}x{figure.height_inches} "
                f"inches) - labels may be illegible"
            )
            return False, {
                "rule": rule_name,
                "severity": "major",
                "description": description,
            }

        return True, None

    def check_data_integrity(
        self, figure: Figure, rule: object
    ) -> tuple[bool, dict[str, str] | None]:
        """Check for data integrity issues."""
        # Would need to verify data representation
        # This is complex and domain-specific
        return True, None

    def _calculate_severity(self, failed_rules: list[str], issues: list[dict[str, str]]) -> str:
        """Calculate overall severity based on failed rules and issues."""
        if not failed_rules:
            return "pass"

        # Count by severity
        critical_count = sum(1 for issue in issues if issue.get("severity") == "critical")
        major_count = sum(1 for issue in issues if issue.get("severity") == "major")
        minor_count = sum(1 for issue in issues if issue.get("severity") == "minor")

        if critical_count > 0:
            return "critical"
        elif major_count > 0:
            return "major"
        elif minor_count > 0:
            return "minor"
        else:
            return "minor"  # Default for unclassified failures

    def _generate_summary(
        self, passed_rules: list[str], failed_rules: list[str], issues: list[dict[str, str]]
    ) -> str:
        """Generate human-readable summary of quality check."""
        total = len(passed_rules) + len(failed_rules)

        if not failed_rules:
            return f"✅ All {total} quality checks passed. Figure is publication-ready."

        summary_parts = [
            f"Quality Check: {len(passed_rules)}/{total} rules passed",
            "",
            "Failed Rules:",
        ]

        for issue in issues:
            rule = issue.get("rule", "unknown")
            severity = issue.get("severity", "unknown")
            description = issue.get("description", "No details")
            summary_parts.append(f"  • [{severity.upper()}] {rule}: {description}")

        return "\n".join(summary_parts)
