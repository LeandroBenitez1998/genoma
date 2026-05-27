"""Skill auditor — evaluates skills against perfect skill model."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SkillAuditMetrics:
    """Quality metrics for a skill."""

    completeness: float  # 0-1: has all expected sections
    description_clarity: float  # 0-1: description triggers without false positives
    instruction_quality: float  # 0-1: step-by-step, actionable, no ambiguity
    example_realism: float  # 0-1: examples match real user pain points
    resource_completeness: float  # 0-1: has necessary context/resources

    overall_score: float = field(init=False)

    def __post_init__(self):
        """Calculate weighted overall score."""
        scores = [
            self.completeness * 0.15,
            self.description_clarity * 0.20,
            self.instruction_quality * 0.35,
            self.example_realism * 0.15,
            self.resource_completeness * 0.15,
        ]
        self.overall_score = sum(scores)


@dataclass
class SkillAuditIssue:
    """Issue found in skill audit."""

    category: str  # "completeness" | "clarity" | "instruction" | "example" | "resource"
    severity: str  # "critical" | "high" | "medium" | "low"
    title: str
    description: str
    suggestion: str  # How to fix it


@dataclass
class SkillAuditReport:
    """Complete audit report for a skill."""

    skill_name: str
    file_path: Path
    metrics: SkillAuditMetrics
    issues: list[SkillAuditIssue] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


class SkillAuditor:
    """Evaluate skills against perfect skill model."""

    # Expected sections in SKILL.md
    EXPECTED_SECTIONS = {
        "when_to_activate": ["When to Activate", "When to Use", "Activation"],
        "core_principles": ["Core Principles", "Principles", "Key Concepts"],
        "instructions": ["Instructions", "How to Use", "Workflow"],
        "examples": ["Examples", "Example", "Usage Examples"],
        "resources": ["Resources", "Reference", "Further Reading"],
    }

    def __init__(self):
        self.issues: list[SkillAuditIssue] = []

    def audit(self, skill_path: Path) -> SkillAuditReport:
        """Audit a skill SKILL.md file. Return report with metrics and issues."""
        self.issues = []

        if not skill_path.exists():
            raise FileNotFoundError(f"Skill not found: {skill_path}")

        content = skill_path.read_text(encoding="utf-8")
        frontmatter, markdown = self._parse_skill(content)
        skill_name = frontmatter.get("name", skill_path.parent.name)

        # Run audits
        completeness = self._audit_completeness(markdown)
        clarity = self._audit_description_clarity(frontmatter)
        instruction_quality = self._audit_instruction_quality(markdown)
        example_realism = self._audit_example_realism(markdown)
        resource_completeness = self._audit_resource_completeness(markdown)

        metrics = SkillAuditMetrics(
            completeness=completeness,
            description_clarity=clarity,
            instruction_quality=instruction_quality,
            example_realism=example_realism,
            resource_completeness=resource_completeness,
        )

        # Generate suggestions
        suggestions = self._generate_suggestions(metrics)

        return SkillAuditReport(
            skill_name=skill_name,
            file_path=skill_path,
            metrics=metrics,
            issues=self.issues,
            suggestions=suggestions,
        )

    def _parse_skill(self, content: str) -> tuple[dict, str]:
        """Parse frontmatter and markdown from skill file."""
        if not content.startswith("---"):
            return {}, content

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content

        frontmatter = self._parse_yaml_simple(parts[1])
        markdown = parts[2].strip()
        return frontmatter, markdown

    def _parse_yaml_simple(self, yaml_str: str) -> dict:
        """Simple YAML parser for frontmatter (key: value format only)."""
        result = {}
        for line in yaml_str.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                result[key] = value
        return result

    def _audit_completeness(self, markdown: str) -> float:
        """Score: 0-1. Checks presence of expected sections."""
        found_sections = 0

        for section_names in self.EXPECTED_SECTIONS.values():
            for name in section_names:
                if re.search(rf"^#+\s+{re.escape(name)}", markdown, re.MULTILINE | re.IGNORECASE):
                    found_sections += 1
                    break

        score = found_sections / len(self.EXPECTED_SECTIONS)

        if score < 0.6:
            self.issues.append(SkillAuditIssue(
                category="completeness",
                severity="high",
                title="Missing sections",
                description=f"Skill has {found_sections}/{len(self.EXPECTED_SECTIONS)} expected sections",
                suggestion="Add missing sections: When to Activate, Core Principles, Instructions, Examples, Resources"
            ))

        return score

    def _audit_description_clarity(self, frontmatter: dict) -> float:
        """Score: 0-1. Description activates correctly without false positives."""
        description = frontmatter.get("description", "")

        if not description:
            self.issues.append(SkillAuditIssue(
                category="clarity",
                severity="critical",
                title="Missing description",
                description="Skill has no description in frontmatter",
                suggestion="Add clear, concise description that explains when skill activates"
            ))
            return 0.0

        # Check length (too short = vague, too long = confusing)
        words = len(description.split())
        if words < 10:
            self.issues.append(SkillAuditIssue(
                category="clarity",
                severity="medium",
                title="Description too short",
                description=f"Description is {words} words (recommend 15-30)",
                suggestion="Expand to clarify when/why skill activates"
            ))
            return 0.4

        if words > 100:
            self.issues.append(SkillAuditIssue(
                category="clarity",
                severity="medium",
                title="Description too long",
                description=f"Description is {words} words (recommend 15-30)",
                suggestion="Condense to essential activation triggers"
            ))
            return 0.6

        return 0.9

    def _audit_instruction_quality(self, markdown: str) -> float:
        """Score: 0-1. Instructions are step-by-step, actionable, unambiguous."""
        # Look for numbered/bulleted lists in instruction sections
        instruction_match = re.search(
            r"^#+\s+(Instructions?|How to Use|Workflow)(.*?)(?=^#+|\Z)",
            markdown,
            re.MULTILINE | re.DOTALL | re.IGNORECASE
        )

        if not instruction_match:
            self.issues.append(SkillAuditIssue(
                category="instruction",
                severity="high",
                title="No instruction section",
                description="Skill missing 'Instructions' or 'How to Use' section",
                suggestion="Add step-by-step instructions for using the skill"
            ))
            return 0.0

        instruction_text = instruction_match.group(2)

        # Count numbered/bulleted items (good structure)
        list_items = re.findall(r"^[\s]*(?:\d+\.|[-*])\s+", instruction_text, re.MULTILINE)
        if not list_items:
            self.issues.append(SkillAuditIssue(
                category="instruction",
                severity="high",
                title="No structured steps",
                description="Instructions lack numbered or bulleted list format",
                suggestion="Reorganize as numbered steps (1. 2. 3.) or bullet points"
            ))
            return 0.3

        score = min(0.9, len(list_items) / 5)  # 5+ steps = good
        return score

    def _audit_example_realism(self, markdown: str) -> float:
        """Score: 0-1. Examples match real user pain points, not toy problems."""
        # Look for code blocks or concrete examples
        code_blocks = re.findall(r"```[\w]*\n(.*?)\n```", markdown, re.DOTALL)

        if not code_blocks:
            self.issues.append(SkillAuditIssue(
                category="example",
                severity="medium",
                title="No code examples",
                description="Skill has no code examples or concrete usage",
                suggestion="Add realistic code examples showing typical usage patterns"
            ))
            return 0.3

        # Check example length (toy problems are usually short)
        avg_example_length = sum(len(ex.split()) for ex in code_blocks) / len(code_blocks)
        if avg_example_length < 10:
            self.issues.append(SkillAuditIssue(
                category="example",
                severity="medium",
                title="Examples too simple",
                description=f"Examples average {int(avg_example_length)} words (toy problems)",
                suggestion="Use realistic, production-like examples that show real pain points"
            ))
            return 0.4

        score = min(0.95, 0.5 + (avg_example_length / 100))
        return score

    def _audit_resource_completeness(self, markdown: str) -> float:
        """Score: 0-1. Has links, references, further reading."""
        # Count links
        links = re.findall(r"\[.*?\]\(.*?\)", markdown)

        if not links:
            self.issues.append(SkillAuditIssue(
                category="resource",
                severity="medium",
                title="No resource links",
                description="Skill has no links to documentation, examples, or references",
                suggestion="Add links to official docs, tutorials, or related resources"
            ))
            return 0.2

        score = min(0.95, 0.3 + (len(links) / 10))  # 10+ links = excellent
        return score

    def _generate_suggestions(self, metrics: SkillAuditMetrics) -> list[str]:
        """Generate improvement suggestions based on audit."""
        suggestions = []

        thresholds = {
            "completeness": 0.75,
            "description_clarity": 0.80,
            "instruction_quality": 0.80,
            "example_realism": 0.70,
            "resource_completeness": 0.60,
        }

        if metrics.completeness < thresholds["completeness"]:
            suggestions.append("Add missing sections to improve completeness")

        if metrics.description_clarity < thresholds["description_clarity"]:
            suggestions.append("Refine description to better explain when/why skill activates")

        if metrics.instruction_quality < thresholds["instruction_quality"]:
            suggestions.append("Restructure instructions as numbered steps")

        if metrics.example_realism < thresholds["example_realism"]:
            suggestions.append("Use more realistic, production-like examples")

        if metrics.resource_completeness < thresholds["resource_completeness"]:
            suggestions.append("Add links to documentation and resources")

        if metrics.overall_score < 0.7:
            suggestions.append(f"Overall quality is {metrics.overall_score:.1%} — prioritize skill for improvement")

        return suggestions

    def audit_to_dict(self, audit: SkillAuditReport) -> dict:
        """Convert SkillAuditReport to dict for JSON serialization."""
        return {
            "skill_name": audit.skill_name,
            "file_path": str(audit.file_path),
            "metrics": {
                "completeness": round(audit.metrics.completeness, 2),
                "description_clarity": round(audit.metrics.description_clarity, 2),
                "instruction_quality": round(audit.metrics.instruction_quality, 2),
                "example_realism": round(audit.metrics.example_realism, 2),
                "resource_completeness": round(audit.metrics.resource_completeness, 2),
                "overall_score": round(audit.metrics.overall_score, 2),
            },
            "issues": [
                {
                    "category": issue.category,
                    "severity": issue.severity,
                    "title": issue.title,
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                }
                for issue in audit.issues
            ],
            "suggestions": audit.suggestions,
        }
