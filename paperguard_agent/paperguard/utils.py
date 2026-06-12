"""Utility functions for PaperGuard."""
import re
from typing import List


def split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text."""
    return re.sub(r'\s+', ' ', text).strip()


def extract_doi(text: str) -> str:
    """Extract DOI from text."""
    doi_pattern = r'10\.\d{4,}/[^\s]+'
    match = re.search(doi_pattern, text)
    return match.group(0) if match else None


def extract_arxiv_id(text: str) -> str:
    """Extract arXiv ID from text."""
    arxiv_pattern = r'arXiv:(\d{4}\.\d{4,5})'
    match = re.search(arxiv_pattern, text, re.IGNORECASE)
    return match.group(1) if match else None


def safe_get(d: dict, *keys, default=None):
    """Safely get nested dict value."""
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, {})
        else:
            return default
    return d if d != {} else default
