"""
Data models for PaperGuard Agent.

This module defines the core data structures used throughout the application,
including issue severity levels and audit issue representation.
"""

from enum import Enum
from .schemas import AuditIssue

# Re-export AuditIssue from schemas for backward compatibility
__all__ = ['AuditIssue', 'IssueSeverity']


class IssueSeverity(Enum):
    """Severity levels for audit issues."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
