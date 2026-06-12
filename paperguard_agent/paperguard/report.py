"""
Report generation module for PaperGuard Agent.

Aggregates audit issues and generates formatted reports in multiple formats.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
import json

from .models import AuditIssue, IssueSeverity


@dataclass
class AuditReport:
    """
    Aggregates audit issues and provides formatted reporting.

    Attributes:
        issues: List of all audit issues found
        paper_path: Path to the paper being audited
        timestamp: When the audit was performed
        metadata: Additional metadata about the audit
    """

    issues: List[AuditIssue] = field(default_factory=list)
    paper_path: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_issue(self, issue: AuditIssue) -> None:
        """Add an issue to the report."""
        self.issues.append(issue)

    def add_issues(self, issues: List[AuditIssue]) -> None:
        """Add multiple issues to the report."""
        self.issues.extend(issues)

    @property
    def total_issues(self) -> int:
        """Total number of issues."""
        return len(self.issues)

    @property
    def critical_count(self) -> int:
        """Number of critical issues."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        """Number of high severity issues."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.HIGH)

    @property
    def medium_count(self) -> int:
        """Number of medium severity issues."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.MEDIUM)

    @property
    def low_count(self) -> int:
        """Number of low severity issues."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.LOW)

    @property
    def info_count(self) -> int:
        """Number of informational issues."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.INFO)

    def get_issues_by_severity(self, severity: IssueSeverity) -> List[AuditIssue]:
        """Get all issues of a specific severity."""
        return [issue for issue in self.issues if issue.severity == severity]

    def get_issues_by_type(self, issue_type: str) -> List[AuditIssue]:
        """Get all issues of a specific type."""
        return [issue for issue in self.issues if issue.issue_type == issue_type]

    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Generate summary statistics for the audit.

        Returns:
            Dictionary with counts and breakdowns
        """
        issue_types = Counter(issue.issue_type for issue in self.issues)

        return {
            "total_issues": self.total_issues,
            "severity_breakdown": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "info": self.info_count,
            },
            "issue_type_breakdown": dict(issue_types),
            "timestamp": self.timestamp.isoformat(),
            "paper_path": self.paper_path,
        }

    def to_markdown(self) -> str:
        """
        Generate a formatted markdown report.

        Returns:
            Markdown-formatted string
        """
        lines = []

        # Header
        lines.append("# PaperGuard Audit Report")
        lines.append("")
        lines.append(f"**Paper:** `{self.paper_path}`")
        lines.append(f"**Date:** {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"Total issues found: **{self.total_issues}**")
        lines.append("")

        # Severity breakdown
        lines.append("### Severity Breakdown")
        lines.append("")
        lines.append(f"- 🔴 Critical: {self.critical_count}")
        lines.append(f"- 🟠 High: {self.high_count}")
        lines.append(f"- 🟡 Medium: {self.medium_count}")
        lines.append(f"- 🟢 Low: {self.low_count}")
        lines.append(f"- ℹ️  Info: {self.info_count}")
        lines.append("")

        # Issue type breakdown
        if self.issues:
            issue_types = Counter(issue.issue_type for issue in self.issues)
            lines.append("### Issue Types")
            lines.append("")
            for issue_type, count in issue_types.most_common():
                lines.append(f"- {issue_type}: {count}")
            lines.append("")

        # Detailed issues by severity
        if self.issues:
            lines.append("## Detailed Issues")
            lines.append("")

            # Group by severity (critical to info)
            severity_order = [
                IssueSeverity.CRITICAL,
                IssueSeverity.HIGH,
                IssueSeverity.MEDIUM,
                IssueSeverity.LOW,
                IssueSeverity.INFO,
            ]

            for severity in severity_order:
                severity_issues = self.get_issues_by_severity(severity)
                if not severity_issues:
                    continue

                # Severity section header
                severity_emoji = {
                    IssueSeverity.CRITICAL: "🔴",
                    IssueSeverity.HIGH: "🟠",
                    IssueSeverity.MEDIUM: "🟡",
                    IssueSeverity.LOW: "🟢",
                    IssueSeverity.INFO: "ℹ️",
                }
                lines.append(f"### {severity_emoji.get(severity, '')} {severity.value.title()} Severity")
                lines.append("")

                for idx, issue in enumerate(severity_issues, 1):
                    lines.append(f"#### {idx}. {issue.issue_type}")
                    lines.append("")
                    lines.append(f"**Location:** {issue.location}")
                    lines.append("")
                    lines.append(f"{issue.message}")
                    lines.append("")

                    if issue.suggestion:
                        lines.append(f"**Suggestion:** {issue.suggestion}")
                        lines.append("")

                    if issue.context:
                        lines.append("**Context:**")
                        lines.append("```")
                        lines.append(issue.context)
                        lines.append("```")
                        lines.append("")

                    if issue.evidence:
                        lines.append("**Evidence:**")
                        for key, value in issue.evidence.items():
                            lines.append(f"- {key}: {value}")
                        lines.append("")

                    lines.append("---")
                    lines.append("")
        else:
            lines.append("## Results")
            lines.append("")
            lines.append("✅ No issues found. The paper passes all citation checks.")
            lines.append("")

        # Metadata
        if self.metadata:
            lines.append("## Audit Metadata")
            lines.append("")
            for key, value in self.metadata.items():
                lines.append(f"- **{key}:** {value}")
            lines.append("")

        return "\n".join(lines)

    def to_json(self) -> dict:
        """
        Generate a JSON-serializable report.

        Returns:
            Dictionary suitable for JSON serialization
        """
        return {
            "paper_path": self.paper_path,
            "timestamp": self.timestamp.isoformat(),
            "summary": self.get_summary_statistics(),
            "issues": [
                {
                    "issue_type": issue.issue_type,
                    "severity": issue.severity.value,
                    "location": issue.location,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                    "context": issue.context,
                    "evidence": issue.evidence,
                }
                for issue in self.issues
            ],
            "metadata": self.metadata,
        }

    def to_json_string(self, indent: int = 2) -> str:
        """
        Generate a formatted JSON string.

        Args:
            indent: Number of spaces for indentation

        Returns:
            JSON-formatted string
        """
        return json.dumps(self.to_json(), indent=indent, ensure_ascii=False)

    def save_markdown(self, output_path: str) -> None:
        """
        Save the markdown report to a file.

        Args:
            output_path: Path to save the markdown file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_markdown())

    def save_json(self, output_path: str, indent: int = 2) -> None:
        """
        Save the JSON report to a file.

        Args:
            output_path: Path to save the JSON file
            indent: Number of spaces for indentation
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json_string(indent=indent))

    def __str__(self) -> str:
        """String representation returns markdown format."""
        return self.to_markdown()

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"AuditReport(total_issues={self.total_issues}, "
            f"critical={self.critical_count}, high={self.high_count}, "
            f"medium={self.medium_count}, low={self.low_count}, "
            f"info={self.info_count})"
        )
