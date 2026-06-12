"""
PaperGuard Agent Pipeline Module

Main orchestration module that coordinates the entire citation verification workflow.
Integrates parsing, extraction, matching, external verification, and claim verification.
"""

import logging
from typing import List, Dict, Optional, Literal
from datetime import datetime

from .parser import load_paper, split_paper
from .citation_extractor import CitationExtractor, CitationMention
from .reference_parser import parse_references, parse_bibtex, ReferenceEntry
from .matcher import compute_match_score, classify_status
from .metadata_clients import search_all_sources
from .claim_extractor import ClaimExtractor
from .claim_verifier import verify_claim
from .schemas import AuditIssue
from .report import AuditReport
from .config import Config

logger = logging.getLogger(__name__)

# Type alias for audit modes
AuditMode = Literal["Quick", "Standard", "Full"]


def run_audit(
    paper_content: str,
    bib_content: Optional[str] = None,
    mode: AuditMode = "Standard",
    max_claims: Optional[int] = None
) -> AuditReport:
    """
    Run a complete citation audit on an academic paper.

    This is the main entry point for PaperGuard. It orchestrates the entire
    verification pipeline from parsing to final report generation.

    Args:
        paper_content: Full text of the paper or path to paper file
        bib_content: Bibliography content (plain text or BibTeX) or path to .bib file
        mode: Audit mode - "Quick", "Standard", or "Full"
            - Quick: Citation-reference consistency only (no external verification)
            - Standard: Quick + external database verification
            - Full: Standard + claim-citation alignment verification
        max_claims: Maximum number of claims to verify (for Full mode). None = all claims

    Returns:
        AuditReport object containing all detected issues and summary statistics

    Example:
        >>> with open("paper.txt") as f:
        ...     paper = f.read()
        >>> with open("references.bib") as f:
        ...     bib = f.read()
        >>> report = run_audit(paper, bib, mode="Full", max_claims=10)
        >>> print(f"Found {report.total_issues} issues")
        >>> report.save_markdown("audit_report.md")
    """
    logger.info(f"Starting audit in {mode} mode")
    start_time = datetime.now()

    # Initialize report
    report = AuditReport(
        paper_path=paper_content if len(paper_content) < 100 else "inline_content",
        timestamp=start_time,
        metadata={
            "mode": mode,
            "max_claims": max_claims if mode == "Full" else None
        }
    )

    try:
        # Step 1: Parse paper content
        logger.info("Step 1: Loading and parsing paper")
        paper_text = load_paper(paper_content)
        body, references_section = split_paper(paper_text)

        if not body:
            logger.error("Failed to extract paper body")
            report.metadata["error"] = "Failed to extract paper body"
            return report

        # Step 2: Extract citations from paper body
        logger.info("Step 2: Extracting citations from paper body")
        citation_extractor = CitationExtractor()
        citations = citation_extractor.extract_citations(body)
        cited_keys = citation_extractor.get_all_cited_keys(body)

        logger.info(f"Found {len(citations)} citation mentions ({len(cited_keys)} unique citations)")
        report.metadata["citations_found"] = len(citations)
        report.metadata["unique_citations"] = len(cited_keys)

        # Step 3: Parse reference entries
        logger.info("Step 3: Parsing reference entries")
        reference_entries = _parse_references_from_content(bib_content, references_section)

        logger.info(f"Parsed {len(reference_entries)} reference entries")
        report.metadata["references_found"] = len(reference_entries)

        # Step 4: Check citation-reference consistency
        logger.info("Step 4: Checking citation-reference consistency")
        consistency_issues = _check_citation_reference_consistency(
            citations, cited_keys, reference_entries
        )
        report.add_issues(consistency_issues)
        logger.info(f"Found {len(consistency_issues)} consistency issues")

        # Step 5: External verification (Standard and Full modes)
        if mode in ["Standard", "Full"]:
            logger.info("Step 5: Verifying references against external databases")
            verification_issues = _verify_references_externally(reference_entries)
            report.add_issues(verification_issues)
            logger.info(f"Found {len(verification_issues)} verification issues")
        else:
            logger.info("Step 5: Skipped (Quick mode)")

        # Step 6: Claim verification (Full mode only)
        if mode == "Full":
            logger.info("Step 6: Verifying claim-citation alignment")
            claim_issues = _verify_claims(body, reference_entries, max_claims)
            report.add_issues(claim_issues)
            logger.info(f"Found {len(claim_issues)} claim verification issues")
        else:
            logger.info("Step 6: Skipped (not Full mode)")

        # Finalize report metadata
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        report.metadata["duration_seconds"] = round(duration, 2)

        logger.info(f"Audit complete. Total issues: {report.total_issues}")
        logger.info(f"Duration: {duration:.2f}s")

    except Exception as e:
        logger.error(f"Audit failed with error: {e}", exc_info=True)
        report.metadata["error"] = str(e)

    return report


def _parse_references_from_content(
    bib_content: Optional[str],
    references_section: str
) -> List[ReferenceEntry]:
    """
    Parse references from provided bibliography or extracted reference section.

    Args:
        bib_content: External bibliography content (may be BibTeX or plain text)
        references_section: Reference section extracted from paper

    Returns:
        List of parsed ReferenceEntry objects
    """
    reference_entries = []

    # Try parsing external bibliography first
    if bib_content:
        bib_text = load_paper(bib_content)

        # Detect format: BibTeX vs plain text
        if "@" in bib_text and "{" in bib_text:
            # Looks like BibTeX
            logger.debug("Parsing bibliography as BibTeX")
            reference_entries = parse_bibtex(bib_text)
        else:
            # Plain text references
            logger.debug("Parsing bibliography as plain text")
            reference_entries = parse_references(bib_text)

    # If no external bib or parsing failed, use references section from paper
    if not reference_entries and references_section:
        logger.debug("Parsing references from paper's reference section")
        reference_entries = parse_references(references_section)

    return reference_entries


def _check_citation_reference_consistency(
    citations: List[CitationMention],
    cited_keys: set,
    reference_entries: List[ReferenceEntry]
) -> List[AuditIssue]:
    """
    Check consistency between in-text citations and reference list.

    Detects:
    - Citations in text that have no corresponding reference
    - References that are never cited in text

    Args:
        citations: List of citation mentions from paper body
        cited_keys: Set of all unique citation keys
        reference_entries: List of parsed references

    Returns:
        List of AuditIssue objects for consistency problems
    """
    issues = []

    # Build reference lookup (handle both numeric and BibTeX keys)
    reference_keys = set()
    for i, ref in enumerate(reference_entries, start=1):
        # Add numeric index
        reference_keys.add(str(i))
        # Add BibTeX key if available (check both bibtex_key and ref_id)
        bibtex_key = getattr(ref, 'bibtex_key', None) or getattr(ref, 'ref_id', None)
        if bibtex_key and bibtex_key != str(i):  # Avoid duplicate numeric keys
            reference_keys.add(bibtex_key)

    # Check for citations without references (MISSING_IN_REFERENCES)
    missing_refs = cited_keys - reference_keys

    for missing_key in missing_refs:
        # Find example citation context
        example_citation = next(
            (c for c in citations if missing_key in c.citation_keys),
            None
        )

        context = example_citation.context if example_citation else ""

        issue = AuditIssue(
            issue_id=f"missing_ref_{missing_key}",
            issue_type="MISSING_IN_REFERENCES",
            severity="HIGH",
            location=f"Citation [{missing_key}]",
            original_text=context[:200],
            diagnosis=f"Citation [{missing_key}] appears in text but has no corresponding entry in the reference list",
            evidence=[
                f"Citation key: {missing_key}",
                f"Found in {len([c for c in citations if missing_key in c.citation_keys])} locations"
            ],
            recommendation=f"Add reference entry for [{missing_key}] or remove the citation from text",
            verifier_trace=[]
        )
        issues.append(issue)

    # Check for unused references (UNUSED_REFERENCE)
    unused_refs = []
    for i, ref in enumerate(reference_entries, start=1):
        ref_id = str(i)
        bibtex_key = getattr(ref, 'bibtex_key', None) or getattr(ref, 'ref_id', None)

        # Check if this reference is cited
        is_cited = (
            ref_id in cited_keys or
            (bibtex_key and bibtex_key in cited_keys)
        )

        if not is_cited:
            unused_refs.append((ref_id, ref))

    for ref_id, ref in unused_refs:
        issue = AuditIssue(
            issue_id=f"unused_ref_{ref_id}",
            issue_type="UNUSED_REFERENCE",
            severity="LOW",
            location=f"Reference [{ref_id}]",
            original_text=ref.raw_text[:200] if ref.raw_text else (ref.title or "")[:200],
            diagnosis=f"Reference [{ref_id}] is never cited in the paper",
            evidence=[
                f"Reference title: {ref.title or 'N/A'}",
                f"Authors: {', '.join(ref.authors[:3]) if ref.authors else 'N/A'}"
            ],
            recommendation="Remove this reference or add citations where appropriate",
            verifier_trace=[]
        )
        issues.append(issue)

    return issues


def _verify_references_externally(
    reference_entries: List[ReferenceEntry]
) -> List[AuditIssue]:
    """
    Verify references against external scholarly databases.

    Searches CrossRef, Semantic Scholar, OpenAlex, and arXiv to verify that
    references point to actual published works with matching metadata.

    Args:
        reference_entries: List of reference entries to verify

    Returns:
        List of AuditIssue objects for verification problems
    """
    issues = []

    for i, ref in enumerate(reference_entries, start=1):
        # Skip if no title (can't search effectively)
        if not ref.title:
            logger.debug(f"Skipping reference {i}: no title")
            continue

        try:
            # Search all external sources
            candidates = search_all_sources(
                title=ref.title,
                authors=ref.authors,
                year=ref.year,
                max_results_per_source=3
            )

            if not candidates:
                # No candidates found - potentially invalid reference
                issue = AuditIssue(
                    issue_id=f"not_found_{i}",
                    issue_type="NOT_FOUND",
                    severity="MEDIUM",
                    location=f"Reference [{i}]",
                    original_text=ref.raw_text[:200] if ref.raw_text else (ref.title or "")[:200],
                    diagnosis=f"Could not find this reference in external databases (CrossRef, Semantic Scholar, OpenAlex, arXiv)",
                    evidence=[
                        f"Title searched: {ref.title}",
                        f"Authors: {', '.join(ref.authors[:3]) if ref.authors else 'N/A'}",
                        f"Year: {ref.year or 'N/A'}"
                    ],
                    recommendation="Verify the reference details are correct. Check for typos in title or author names.",
                    verifier_trace=[]
                )
                issues.append(issue)
                continue

            # Find best match
            best_candidate = None
            best_score = 0.0

            for candidate in candidates:
                ref_dict = {
                    "title": ref.title,
                    "authors": ref.authors,
                    "year": ref.year,
                    "doi": ref.doi
                }
                cand_dict = {
                    "title": candidate.title,
                    "authors": candidate.authors,
                    "year": candidate.year,
                    "doi": candidate.doi
                }

                score = compute_match_score(ref_dict, cand_dict)

                if score > best_score:
                    best_score = score
                    best_candidate = candidate

            # Classify based on score
            status = classify_status(best_score)

            # Create issues for non-verified references
            if status == "LOW_CONFIDENCE":
                issue = AuditIssue(
                    issue_id=f"low_confidence_{i}",
                    issue_type="LOW_CONFIDENCE",
                    severity="MEDIUM",
                    location=f"Reference [{i}]",
                    original_text=ref.raw_text[:200] if ref.raw_text else (ref.title or "")[:200],
                    diagnosis=f"Reference match has low confidence (score: {best_score:.2f}). Possible metadata issues.",
                    evidence=[
                        f"Your title: {ref.title}",
                        f"Found title: {best_candidate.title}",
                        f"Match score: {best_score:.2f}",
                        f"Source: {best_candidate.source}"
                    ],
                    recommendation="Review the reference details. Consider checking the DOI or venue information.",
                    verifier_trace=[{"match_score": best_score, "source": best_candidate.source}]
                )
                issues.append(issue)

            elif status == "METADATA_MISMATCH":
                issue = AuditIssue(
                    issue_id=f"mismatch_{i}",
                    issue_type="METADATA_MISMATCH",
                    severity="HIGH",
                    location=f"Reference [{i}]",
                    original_text=ref.raw_text[:200] if ref.raw_text else (ref.title or "")[:200],
                    diagnosis=f"Significant metadata mismatch with external databases (score: {best_score:.2f})",
                    evidence=[
                        f"Your title: {ref.title}",
                        f"Found title: {best_candidate.title}",
                        f"Your authors: {', '.join(ref.authors[:3]) if ref.authors else 'N/A'}",
                        f"Found authors: {', '.join(best_candidate.authors[:3]) if best_candidate.authors else 'N/A'}",
                        f"Your year: {ref.year or 'N/A'}",
                        f"Found year: {best_candidate.year or 'N/A'}",
                        f"Match score: {best_score:.2f}"
                    ],
                    recommendation=f"Verify the reference details. Suggested correction - Title: {best_candidate.title}, Authors: {', '.join(best_candidate.authors[:3]) if best_candidate.authors else 'N/A'}, Year: {best_candidate.year}",
                    verifier_trace=[{"match_score": best_score, "source": best_candidate.source}]
                )
                issues.append(issue)

            elif status == "NOT_FOUND":
                issue = AuditIssue(
                    issue_id=f"not_found_{i}",
                    issue_type="NOT_FOUND",
                    severity="HIGH",
                    location=f"Reference [{i}]",
                    original_text=ref.raw_text[:200] if ref.raw_text else (ref.title or "")[:200],
                    diagnosis=f"No matching publication found in external databases (best score: {best_score:.2f})",
                    evidence=[
                        f"Title: {ref.title}",
                        f"Authors: {', '.join(ref.authors[:3]) if ref.authors else 'N/A'}",
                        f"Year: {ref.year or 'N/A'}",
                        f"Best match score: {best_score:.2f}"
                    ],
                    recommendation="This reference may be incorrect or fabricated. Verify it exists and check for typos.",
                    verifier_trace=[{"match_score": best_score}]
                )
                issues.append(issue)

        except Exception as e:
            logger.warning(f"Error verifying reference {i}: {e}")
            continue

    return issues


def _verify_claims(
    body: str,
    reference_entries: List[ReferenceEntry],
    max_claims: Optional[int]
) -> List[AuditIssue]:
    """
    Verify that claims in the paper are properly supported by citations.

    Uses LLM-based verification to check if the cited papers actually support
    the claims being made.

    Args:
        body: Main paper content
        reference_entries: List of reference entries
        max_claims: Maximum number of claims to verify (None = all)

    Returns:
        List of AuditIssue objects for claim verification problems
    """
    issues = []

    # Extract claims from paper body
    claim_extractor = ClaimExtractor()
    claims = claim_extractor.extract_claims(body, max_claims=max_claims)

    logger.info(f"Extracted {len(claims)} claims for verification")

    # Build reference lookup (by index and BibTeX key)
    ref_lookup = {}
    for i, ref in enumerate(reference_entries, start=1):
        ref_lookup[str(i)] = ref
        bibtex_key = getattr(ref, 'bibtex_key', None) or getattr(ref, 'ref_id', None)
        if bibtex_key and bibtex_key != str(i):
            ref_lookup[bibtex_key] = ref

    for claim_idx, claim in enumerate(claims, start=1):
        if not claim["has_citation"] or not claim["citations"]:
            continue

        claim_text = claim["sentence"]
        citation_markers = claim["citations"]

        # Extract citation keys from markers (e.g., "[1]" -> "1", "\cite{key}" -> "key")
        citation_keys = set()
        for marker in citation_markers:
            # Numeric citations: [1], [1,2], [1-3]
            import re
            numeric_match = re.findall(r'\d+', marker)
            citation_keys.update(numeric_match)

            # LaTeX citations: \cite{key}
            latex_match = re.findall(r'\\cite\{([^}]+)\}', marker)
            for keys_str in latex_match:
                citation_keys.update(k.strip() for k in keys_str.split(','))

        # Verify each cited reference supports the claim
        for cite_key in citation_keys:
            ref = ref_lookup.get(cite_key)

            if not ref:
                continue  # Already handled by consistency check

            # Skip if no abstract available (need abstract for verification)
            # Try to get abstract from external search if not in reference
            abstract = None

            # First, check if we need to fetch abstract
            if ref.title:
                try:
                    candidates = search_all_sources(
                        title=ref.title,
                        authors=ref.authors,
                        max_results_per_source=1
                    )

                    for candidate in candidates:
                        if candidate.abstract:
                            abstract = candidate.abstract
                            break
                except Exception as e:
                    logger.warning(f"Failed to fetch abstract for reference {cite_key}: {e}")

            if not abstract:
                logger.debug(f"No abstract available for reference {cite_key}, skipping claim verification")
                continue

            # Verify claim against citation
            try:
                citation_metadata = {
                    "title": ref.title,
                    "authors": ref.authors,
                    "year": ref.year,
                    "venue": ref.venue
                }

                result = verify_claim(claim_text, citation_metadata, abstract)

                # Create issue if claim is not well-supported
                if result.verdict.value in ["PARTIALLY_SUPPORTED", "UNSUPPORTED"]:
                    severity_map = {
                        "LOW": "LOW",
                        "MEDIUM": "MEDIUM",
                        "HIGH": "HIGH"
                    }

                    issue = AuditIssue(
                        issue_id=f"claim_{claim_idx}_cite_{cite_key}",
                        issue_type=f"CLAIM_{result.verdict.value}",
                        severity=severity_map[result.severity.value],
                        location=f"Claim {claim_idx} citing [{cite_key}]",
                        original_text=claim_text[:200],
                        diagnosis=f"Citation [{cite_key}] {result.verdict.value.lower().replace('_', ' ')}: {result.reason}",
                        evidence=[
                            f"Claim: {claim_text[:150]}",
                            f"Cited paper: {ref.title}",
                            f"Verification verdict: {result.verdict.value}",
                            f"Severity: {result.severity.value}"
                        ],
                        recommendation=result.suggested_revision or "Revise the claim to better align with the cited source",
                        verifier_trace=[{
                            "verdict": result.verdict.value,
                            "severity": result.severity.value,
                            "reason": result.reason
                        }]
                    )
                    issues.append(issue)

                elif result.verdict.value == "NOT_ENOUGH_INFO":
                    # Lower severity for insufficient information
                    issue = AuditIssue(
                        issue_id=f"claim_{claim_idx}_cite_{cite_key}_info",
                        issue_type="CLAIM_INSUFFICIENT_INFO",
                        severity="LOW",
                        location=f"Claim {claim_idx} citing [{cite_key}]",
                        original_text=claim_text[:200],
                        diagnosis=f"Citation [{cite_key}] provides insufficient information to verify the claim: {result.reason}",
                        evidence=[
                            f"Claim: {claim_text[:150]}",
                            f"Cited paper: {ref.title}"
                        ],
                        recommendation="Consider adding additional citations or clarifying the claim",
                        verifier_trace=[{"verdict": result.verdict.value}]
                    )
                    issues.append(issue)

            except Exception as e:
                logger.warning(f"Failed to verify claim {claim_idx} against citation {cite_key}: {e}")
                continue

    return issues

