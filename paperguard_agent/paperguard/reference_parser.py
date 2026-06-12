"""
Reference Parser Module for PaperGuard Agent

Parses citations from plain text and BibTeX formats, extracting structured metadata
including title, authors, year, venue, DOI, and arXiv IDs.
"""

import re
from typing import List, Optional, Dict, Any

# Import ReferenceEntry from schemas to avoid duplicate definitions
from .schemas import ReferenceEntry


def parse_references(ref_section: str) -> List[ReferenceEntry]:
    """
    Parse references from a plain text reference section.

    Handles common citation formats including:
    - IEEE style: [1] Author, "Title," Venue, Year.
    - ACM/APA style: Author (Year). Title. Venue.
    - Numbered lists with various punctuation

    Args:
        ref_section: String containing the references section

    Returns:
        List of ReferenceEntry objects with extracted metadata
    """
    references = []

    # Split into individual references
    # Try multiple splitting strategies
    ref_items = _split_references(ref_section)

    for idx, ref_text in enumerate(ref_items):
        if not ref_text.strip():
            continue

        # Extract ref_id from text
        ref_id_match = re.match(r'^\s*[\[\(](\d+|[A-Za-z]\w*)[\]\)]', ref_text)
        ref_id = ref_id_match.group(1) if ref_id_match else str(idx + 1)

        # Extract all metadata
        title = _extract_title(ref_text)
        authors = _extract_authors(ref_text)
        year = _extract_year(ref_text)
        venue = _extract_venue(ref_text)
        doi = _extract_doi(ref_text)
        arxiv_id = _extract_arxiv_id(ref_text)

        # Create ReferenceEntry with all fields at once (Pydantic style)
        entry = ReferenceEntry(
            ref_id=ref_id,
            raw_text=ref_text.strip(),
            title=title,
            authors=authors if authors else [],
            year=year,
            venue=venue,
            doi=doi,
            arxiv_id=arxiv_id
        )

        references.append(entry)

    return references


def parse_bibtex(bib_content: str) -> List[ReferenceEntry]:
    """
    Parse references from BibTeX content.

    Args:
        bib_content: String containing BibTeX entries

    Returns:
        List of ReferenceEntry objects with extracted metadata
    """
    try:
        import bibtexparser
        from bibtexparser.bparser import BibTexParser
        from bibtexparser.customization import convert_to_unicode
    except ImportError:
        # Fallback to manual parsing if bibtexparser not available
        return _parse_bibtex_manual(bib_content)

    references = []

    try:
        parser = BibTexParser(common_strings=True)
        parser.customization = convert_to_unicode
        bib_database = bibtexparser.loads(bib_content, parser=parser)

        for idx, bib_entry in enumerate(bib_database.entries):
            # Use BibTeX key as ref_id, fallback to index
            ref_id = bib_entry.get('ID', f'bib_{idx + 1}')

            # Extract fields from BibTeX
            title = _clean_bibtex_field(bib_entry.get('title'))
            year = _parse_year_from_string(bib_entry.get('year'))
            doi = bib_entry.get('doi')

            # Extract authors
            authors = []
            if 'author' in bib_entry:
                authors = _parse_bibtex_authors(bib_entry['author'])

            # Extract venue
            venue = (bib_entry.get('journal') or
                    bib_entry.get('booktitle') or
                    bib_entry.get('publisher'))

            # Extract arXiv ID
            arxiv_id = None
            if 'eprint' in bib_entry:
                arxiv_id = bib_entry['eprint']
            elif 'archiveprefix' in bib_entry and bib_entry['archiveprefix'].lower() == 'arxiv':
                arxiv_id = bib_entry.get('eprint')

            # Create ReferenceEntry
            entry = ReferenceEntry(
                ref_id=ref_id,
                raw_text=_format_bibtex_entry(bib_entry),
                title=title,
                authors=authors,
                year=year,
                venue=venue,
                doi=doi,
                arxiv_id=arxiv_id
            )

            references.append(entry)
            entry.publisher = bib_entry.get('publisher')

            # Extract authors
            author_str = bib_entry.get('author', '')
            if author_str:
                entry.authors = _parse_bibtex_authors(author_str)

            # Extract venue based on entry type
            entry.venue = _extract_bibtex_venue(bib_entry)

            # Extract arXiv ID from various fields
            arxiv_id = bib_entry.get('eprint') or bib_entry.get('arxiv')
            if arxiv_id:
                entry.arxiv_id = arxiv_id
            elif entry.url:
                entry.arxiv_id = _extract_arxiv_id(entry.url)

            references.append(entry)

    except Exception as e:
        # Fallback to manual parsing on error
        return _parse_bibtex_manual(bib_content)

    return references


def _split_references(ref_section: str) -> List[str]:
    """
    Split reference section into individual references.
    Robust for various PDF extraction formats.
    """
    # Clean up: remove section headers and common artifacts
    ref_section = re.sub(r'^(Refer\s*ences?.*?|References?.*?|Bibliography.*?|Works Cited.*?)(?=\[|\d\.|\n)',
                         '', ref_section, flags=re.IGNORECASE)

    # Remove line numbers at end of lines (PDF artifact: "text. 451")
    ref_section = re.sub(r'\s+\d{3,5}\s*$', '', ref_section, flags=re.MULTILINE)

    # Strategy 1: Split by [N] markers (most common)
    if re.search(r'\[\d+\]', ref_section):
        # Split before each [N] that starts a reference
        refs = re.split(r'(?=\[\d+\]\s*[A-Z])', ref_section)
        refs = [r.strip() for r in refs if r.strip() and len(r.strip()) > 20]
        if len(refs) > 1:
            return refs

    # Strategy 2: Split by "N." at line start
    if re.search(r'^\d+\.\s+[A-Z]', ref_section, re.MULTILINE):
        refs = re.split(r'\n(?=\d+\.\s+[A-Z])', ref_section)
        refs = [r.strip() for r in refs if r.strip() and len(r.strip()) > 20]
        if len(refs) > 1:
            return refs

    # Strategy 3: Split by double newlines
    refs = re.split(r'\n\s*\n', ref_section)
    refs = [r.strip() for r in refs if r.strip() and len(r.strip()) > 20]
    if len(refs) > 1:
        return refs

    # Strategy 4: Heuristic - merge short lines
    lines = ref_section.split('\n')
    merged = []
    current = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # If line starts with [N] or N., it's a new reference
        if re.match(r'^\[\d+\]', line) or re.match(r'^\d+\.\s+[A-Z]', line):
            if current:
                merged.append(current)
            current = line
        else:
            # Continuation of previous reference
            if current:
                current += " " + line
            else:
                current = line

    if current:
        merged.append(current)

    return merged if len(merged) > 0 else [ref_section]


def _extract_title(text: str) -> Optional[str]:
    """Extract title from reference text."""
    # Title often in quotes or after author names before venue

    # Try quoted title
    quoted = re.search(r'["""]([^"""]+)["""]', text)
    if quoted:
        return quoted.group(1).strip()

    # Try title in italics (markdown or HTML)
    italic = re.search(r'[*_]([^*_]{20,})[*_]', text)
    if italic:
        return italic.group(1).strip()

    # Try extracting title pattern: after author(s) and year, before "In" or venue
    # Pattern: Author et al. (2020). Title text here. In Proceedings...
    pattern = r'\.\s+([A-Z][^.]+?)\.\s+(?:In|Proceedings|Journal|arXiv|Available)'
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()

    # Try: after year in parentheses
    pattern = r'\(\d{4}\)\.\s+([A-Z][^.]+?)\.(?:\s+In|\s+Proceedings|\s+Journal|$)'
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()

    return None


def _extract_authors(text: str) -> List[str]:
    """Extract author names from reference text."""
    authors = []

    # Remove citation number prefix
    text = re.sub(r'^\[\d+\]\s*', '', text)
    text = re.sub(r'^\d+\.\s*', '', text)

    # Try to extract authors before year or title
    # Pattern: Last, F., Last, F., and Last, F. (Year)
    pattern = r'^([^.]+(?:,\s*[A-Z]\.|[A-Z]\.\s*[A-Z]\.).*?)(?:\(|\d{4}|["""])'
    match = re.search(pattern, text)

    if match:
        author_str = match.group(1).strip()
        # Split by common separators
        if ' and ' in author_str:
            author_list = re.split(r',\s*and\s+|,\s+and\s+|\s+and\s+', author_str)
        elif ';' in author_str:
            author_list = author_str.split(';')
        else:
            author_list = author_str.split(',')

        # Clean up author names
        for author in author_list:
            author = author.strip()
            # Remove "et al."
            author = re.sub(r'\s*et\s+al\.?\s*$', '', author, flags=re.IGNORECASE)
            if author and len(author) > 2:
                authors.append(author)

    return authors[:10]  # Limit to first 10 authors


def _extract_year(text: str) -> Optional[int]:
    """Extract publication year from reference text."""
    # Try year in parentheses
    match = re.search(r'\((\d{4})\)', text)
    if match:
        return int(match.group(1))

    # Try standalone 4-digit year
    match = re.search(r'\b(19\d{2}|20[0-2]\d)\b', text)
    if match:
        return int(match.group(1))

    return None


def _extract_venue(text: str) -> Optional[str]:
    """Extract venue/journal/conference from reference text."""
    # Try pattern after "In" keyword
    match = re.search(r'\bIn\s+(?:Proceedings of\s+)?([^,.\d]+?)(?:[,.\d]|\d{4})', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Try pattern with "Proceedings"
    match = re.search(r'(Proceedings of[^,.\d]+?)(?:[,.\d]|\d{4})', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Try pattern with common journal/conference indicators
    match = re.search(r'\b(Journal of[^,.\d]+?|Conference on[^,.\d]+?|Transactions on[^,.\d]+?)(?:[,.\d]|\d{4})', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


def _extract_doi(text: str) -> Optional[str]:
    """Extract DOI from reference text."""
    # DOI pattern: 10.xxxx/xxxxx
    match = re.search(r'\b(10\.\d{4,}/[^\s]+)', text)
    if match:
        doi = match.group(1)
        # Clean trailing punctuation
        doi = re.sub(r'[.,;)\]]+$', '', doi)
        return doi

    # DOI in URL format
    match = re.search(r'doi\.org/(10\.\d{4,}/[^\s]+)', text)
    if match:
        doi = match.group(1)
        doi = re.sub(r'[.,;)\]]+$', '', doi)
        return doi

    return None


def _extract_arxiv_id(text: str) -> Optional[str]:
    """Extract arXiv ID from reference text."""
    # New format: arXiv:YYMM.NNNNN
    match = re.search(r'arXiv:(\d{4}\.\d{4,5})', text, re.IGNORECASE)
    if match:
        return match.group(1)

    # Old format: arXiv:arch-ive/YYMMNNN
    match = re.search(r'arXiv:([a-z\-]+/\d{7})', text, re.IGNORECASE)
    if match:
        return match.group(1)

    # In URL format
    match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', text, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def _extract_url(text: str) -> Optional[str]:
    """Extract URL from reference text."""
    match = re.search(r'(https?://[^\s]+)', text)
    if match:
        url = match.group(1)
        # Clean trailing punctuation
        url = re.sub(r'[.,;)\]]+$', '', url)
        return url

    return None


def _extract_pages(text: str) -> Optional[str]:
    """Extract page numbers from reference text."""
    # Pattern: pp. 123-456 or pages 123-456
    match = re.search(r'(?:pp\.|pages?)\s*(\d+(?:[-–]\d+)?)', text, re.IGNORECASE)
    if match:
        return match.group(1)

    # Pattern: standalone page range
    match = re.search(r'\b(\d{1,4}[-–]\d{1,4})\b', text)
    if match:
        return match.group(1)

    return None


def _extract_volume(text: str) -> Optional[str]:
    """Extract volume number from reference text."""
    # Pattern: vol. 12 or volume 12
    match = re.search(r'(?:vol\.|volume)\s*(\d+)', text, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def _parse_bibtex_manual(bib_content: str) -> List[ReferenceEntry]:
    """Manual BibTeX parsing fallback when bibtexparser is unavailable."""
    references = []

    # Split into individual entries
    entries = re.split(r'\n@', bib_content)

    for entry_text in entries:
        if not entry_text.strip():
            continue

        # Add back @ if it was split
        if not entry_text.startswith('@'):
            entry_text = '@' + entry_text

        entry = ReferenceEntry(raw_text=entry_text.strip())

        # Extract entry type and key
        match = re.match(r'@(\w+)\s*\{\s*([^,]+),', entry_text, re.IGNORECASE)
        if match:
            entry.entry_type = match.group(1).lower()
            entry.bibtex_key = match.group(2).strip()

        # Extract fields
        entry.title = _extract_bibtex_field(entry_text, 'title')
        entry.year = _parse_year_from_string(_extract_bibtex_field(entry_text, 'year'))
        entry.doi = _extract_bibtex_field(entry_text, 'doi')
        entry.url = _extract_bibtex_field(entry_text, 'url')
        entry.pages = _extract_bibtex_field(entry_text, 'pages')
        entry.volume = _extract_bibtex_field(entry_text, 'volume')
        entry.number = _extract_bibtex_field(entry_text, 'number')
        entry.publisher = _extract_bibtex_field(entry_text, 'publisher')

        # Extract authors
        author_str = _extract_bibtex_field(entry_text, 'author')
        if author_str:
            entry.authors = _parse_bibtex_authors(author_str)

        # Extract venue
        venue = (_extract_bibtex_field(entry_text, 'journal') or
                _extract_bibtex_field(entry_text, 'booktitle') or
                _extract_bibtex_field(entry_text, 'conference'))
        entry.venue = venue

        # Extract arXiv ID
        arxiv_id = (_extract_bibtex_field(entry_text, 'eprint') or
                   _extract_bibtex_field(entry_text, 'arxiv'))
        if arxiv_id:
            entry.arxiv_id = arxiv_id
        elif entry.url:
            entry.arxiv_id = _extract_arxiv_id(entry.url)

        references.append(entry)

    return references


def _extract_bibtex_field(entry_text: str, field_name: str) -> Optional[str]:
    """Extract a field value from BibTeX entry text."""
    # Pattern: field = {value} or field = "value"
    pattern = rf'{field_name}\s*=\s*[{{"]([^}}\"]+)[}}\"]'
    match = re.search(pattern, entry_text, re.IGNORECASE)
    if match:
        return _clean_bibtex_field(match.group(1))

    return None


def _clean_bibtex_field(value: Optional[str]) -> Optional[str]:
    """Clean BibTeX field value by removing LaTeX commands and extra whitespace."""
    if not value:
        return None

    # Remove common LaTeX commands
    value = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', value)  # \textbf{text} -> text
    value = re.sub(r'\\[a-zA-Z]+', '', value)  # \LaTeX -> LaTeX
    value = re.sub(r'[{}]', '', value)  # Remove braces
    value = re.sub(r'\s+', ' ', value)  # Normalize whitespace

    return value.strip()


def _parse_bibtex_authors(author_str: str) -> List[str]:
    """Parse author string from BibTeX format."""
    # Split by "and"
    authors = re.split(r'\s+and\s+', author_str, flags=re.IGNORECASE)

    cleaned_authors = []
    for author in authors:
        author = author.strip()
        # Remove extra whitespace and LaTeX commands
        author = _clean_bibtex_field(author)
        if author and len(author) > 2:
            cleaned_authors.append(author)

    return cleaned_authors[:10]  # Limit to first 10


def _extract_bibtex_venue(bib_entry: Dict[str, str]) -> Optional[str]:
    """Extract venue from BibTeX entry based on entry type."""
    entry_type = bib_entry.get('ENTRYTYPE', '').lower()

    if entry_type in ['article']:
        return bib_entry.get('journal')
    elif entry_type in ['inproceedings', 'conference']:
        return bib_entry.get('booktitle')
    elif entry_type in ['book', 'inbook']:
        return bib_entry.get('publisher')
    elif entry_type in ['phdthesis', 'mastersthesis']:
        return bib_entry.get('school')
    elif entry_type in ['techreport']:
        return bib_entry.get('institution')

    # Fallback: try common venue fields
    return (bib_entry.get('journal') or
            bib_entry.get('booktitle') or
            bib_entry.get('howpublished'))


def _format_bibtex_entry(bib_entry: Dict[str, str]) -> str:
    """Format BibTeX entry dict back to string representation."""
    entry_type = bib_entry.get('ENTRYTYPE', 'misc')
    bib_key = bib_entry.get('ID', 'unknown')

    lines = [f"@{entry_type}{{{bib_key},"]

    for key, value in bib_entry.items():
        if key not in ['ENTRYTYPE', 'ID']:
            lines.append(f"  {key} = {{{value}}},")

    lines.append("}")

    return '\n'.join(lines)


def _parse_year_from_string(year_str: Optional[str]) -> Optional[int]:
    """Parse year from string, handling various formats."""
    if not year_str:
        return None

    # Extract 4-digit year
    match = re.search(r'\b(19\d{2}|20[0-2]\d)\b', str(year_str))
    if match:
        return int(match.group(1))

    return None
