"""
Citation matching and verification logic for PaperGuard Agent.

This module provides functions to compare reference citations with candidate
citations from search results and compute match scores based on multiple fields.
"""

import re
from typing import List, Dict, Any
from rapidfuzz import fuzz


def normalize_text(s: str) -> str:
    """
    Normalize text by converting to lowercase and removing punctuation.

    Args:
        s: Input string to normalize

    Returns:
        Normalized string with lowercase letters and no punctuation
    """
    if not s:
        return ""

    # Convert to lowercase
    s = s.lower()

    # Remove punctuation (keep alphanumeric and spaces)
    s = re.sub(r'[^\w\s]', ' ', s)

    # Collapse multiple spaces
    s = re.sub(r'\s+', ' ', s)

    return s.strip()


def title_similarity(a: str, b: str) -> float:
    """
    Calculate similarity between two titles using token set ratio.

    This method is robust to word order differences and handles
    partial matches well.

    Args:
        a: First title string
        b: Second title string

    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not a or not b:
        return 0.0

    # Normalize both titles
    a_norm = normalize_text(a)
    b_norm = normalize_text(b)

    if not a_norm or not b_norm:
        return 0.0

    # Use token_set_ratio for fuzzy matching (0-100 scale)
    score = fuzz.token_set_ratio(a_norm, b_norm)

    # Convert to 0.0-1.0 scale
    return score / 100.0


def author_overlap(ref_authors: List[str], cand_authors: List[str]) -> float:
    """
    Calculate overlap between two author lists.

    Compares normalized author names and returns the ratio of matching
    authors to the total number of unique authors.

    Args:
        ref_authors: List of author names from reference citation
        cand_authors: List of author names from candidate citation

    Returns:
        Overlap score between 0.0 and 1.0
    """
    if not ref_authors or not cand_authors:
        return 0.0

    # Normalize author names
    ref_norm = {normalize_text(author) for author in ref_authors if author}
    cand_norm = {normalize_text(author) for author in cand_authors if author}

    if not ref_norm or not cand_norm:
        return 0.0

    # Calculate Jaccard similarity (intersection / union)
    intersection = len(ref_norm & cand_norm)
    union = len(ref_norm | cand_norm)

    if union == 0:
        return 0.0

    return intersection / union


def compute_match_score(ref: Dict[str, Any], cand: Dict[str, Any]) -> float:
    """
    Compute overall match score between reference and candidate citation.

    Uses weighted combination of multiple fields:
    - Title: 50%
    - Authors: 20%
    - Year: 15%
    - DOI: 15%

    Args:
        ref: Reference citation dictionary with keys: title, authors, year, doi
        cand: Candidate citation dictionary with keys: title, authors, year, doi

    Returns:
        Overall match score between 0.0 and 1.0
    """
    score = 0.0

    # Handle both dict and Pydantic object
    def get_field(obj, field, default=None):
        if hasattr(obj, field):
            return getattr(obj, field, default)
        elif isinstance(obj, dict):
            return obj.get(field, default)
        return default

    # Title similarity (50% weight)
    title_score = title_similarity(
        get_field(ref, 'title', ''),
        get_field(cand, 'title', '')
    )
    score += 0.50 * title_score

    # Author overlap (20% weight)
    author_score = author_overlap(
        get_field(ref, 'authors', []),
        get_field(cand, 'authors', [])
    )
    score += 0.20 * author_score

    # Year match (15% weight)
    ref_year = get_field(ref, 'year')
    cand_year = get_field(cand, 'year')

    if ref_year and cand_year:
        try:
            # Exact match gives full score
            if str(ref_year) == str(cand_year):
                year_score = 1.0
            # Off by 1 year gives partial score
            elif abs(int(ref_year) - int(cand_year)) == 1:
                year_score = 0.5
            else:
                year_score = 0.0
        except (ValueError, TypeError):
            year_score = 0.0
    else:
        year_score = 0.0

    score += 0.15 * year_score

    # DOI match (15% weight)
    ref_doi = normalize_text(get_field(ref, 'doi', ''))
    cand_doi = normalize_text(get_field(cand, 'doi', ''))

    if ref_doi and cand_doi:
        # DOI match is binary - either exact or not
        doi_score = 1.0 if ref_doi == cand_doi else 0.0
    else:
        # No penalty if DOI is missing (use 0 to not contribute)
        doi_score = 0.0

    score += 0.15 * doi_score

    return score


def classify_status(score: float) -> str:
    """
    Classify verification status based on match score.

    Thresholds:
    - >= 0.85: VERIFIED (high confidence match)
    - 0.65-0.85: LOW_CONFIDENCE (possible match, needs review)
    - 0.40-0.65: METADATA_MISMATCH (some overlap but significant differences)
    - < 0.40: NOT_FOUND (no meaningful match)

    Args:
        score: Match score between 0.0 and 1.0

    Returns:
        Status string: "VERIFIED", "LOW_CONFIDENCE", "METADATA_MISMATCH", or "NOT_FOUND"
    """
    if score >= 0.85:
        return "VERIFIED"
    elif score >= 0.65:
        return "LOW_CONFIDENCE"
    elif score >= 0.40:
        return "METADATA_MISMATCH"
    else:
        return "NOT_FOUND"
