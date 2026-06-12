"""PaperGuard Agent - Citation verification for AI-assisted academic writing."""

__version__ = "1.0.0"

from .schemas import (
    ReferenceEntry,
    CitationMention,
    ExternalCandidate,
    CitationVerificationResult,
    ClaimVerificationResult,
    AuditIssue,
)

__all__ = [
    "ReferenceEntry",
    "CitationMention", 
    "ExternalCandidate",
    "CitationVerificationResult",
    "ClaimVerificationResult",
    "AuditIssue",
]
