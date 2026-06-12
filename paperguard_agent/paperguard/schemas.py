"""
Pydantic schemas for PaperGuard Agent.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ReferenceEntry(BaseModel):
    """Parsed reference from bibliography."""
    ref_id: str
    raw_text: str
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None


class CitationMention(BaseModel):
    """Citation mention in paper text."""
    mention_id: str
    raw_marker: str
    ref_ids: List[str]
    sentence: str
    section: Optional[str] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None


class ExternalCandidate(BaseModel):
    """Candidate from external database search."""
    source: str
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    raw: dict = Field(default_factory=dict)


class CitationVerificationResult(BaseModel):
    """Result of verifying a reference."""
    ref_id: str
    status: Literal["VERIFIED", "NOT_FOUND", "METADATA_MISMATCH", "LOW_CONFIDENCE", "MISSING_IN_REFERENCES", "UNUSED_REFERENCE"]
    confidence: float
    best_candidate: Optional[ExternalCandidate] = None
    mismatches: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    suggestion: Optional[str] = None


class ClaimVerificationResult(BaseModel):
    """Result of verifying claim-citation support."""
    mention_id: str
    claim: str
    cited_ref_ids: List[str]
    verdict: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "NOT_ENOUGH_INFO"]
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    reason: str
    evidence_used: List[str] = Field(default_factory=list)
    suggested_revision: Optional[str] = None


class AuditIssue(BaseModel):
    """An issue detected during audit."""
    issue_id: str
    issue_type: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    location: str
    original_text: str
    diagnosis: str
    evidence: List[str]
    recommendation: str
    verifier_trace: List[dict] = Field(default_factory=list)
