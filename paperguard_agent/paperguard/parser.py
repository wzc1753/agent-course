"""
PaperGuard Agent - Parser Module

Handles loading and parsing academic papers in various formats.
Extracts paper body and references section for citation verification.
"""

import re
from pathlib import Path
from typing import Tuple, Optional


def load_paper(file_path_or_content: str) -> str:
    """
    Load paper content from file path or return content directly.

    Args:
        file_path_or_content: Either a file path (str) or paper content (str)

    Returns:
        str: The paper content as text

    Raises:
        FileNotFoundError: If file path provided but file doesn't exist
        ValueError: If file format is not supported
    """
    # Check if input looks like a file path
    if '\n' not in file_path_or_content and len(file_path_or_content) < 500:
        path = Path(file_path_or_content)
        if path.exists():
            return _load_from_file(path)

    # Otherwise treat as content
    return file_path_or_content


def _load_from_file(path: Path) -> str:
    """
    Load content from a file based on extension.

    Args:
        path: Path object to the file

    Returns:
        str: File content as text

    Raises:
        ValueError: If file format is not supported
    """
    suffix = path.suffix.lower()

    if suffix == '.txt':
        return path.read_text(encoding='utf-8')

    elif suffix == '.md':
        return path.read_text(encoding='utf-8')

    elif suffix == '.tex':
        return path.read_text(encoding='utf-8')

    elif suffix == '.pdf':
        try:
            import PyPDF2

            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = []
                print(f"\n[PDF DEBUG] Extracting {len(reader.pages)} pages")
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    text.append(page_text)
                    if i == 0:
                        print(f"[PDF DEBUG] Page 1 first 200 chars: {page_text[:200]}")
                    if i == len(reader.pages) - 1:
                        print(f"[PDF DEBUG] Last page first 200 chars: {page_text[:200]}")

                full_text = '\n'.join(text)
                print(f"[PDF DEBUG] Total extracted text length: {len(full_text)}")

                # Check for "References" or "Refer ences"
                if 'eferences' in full_text.lower():
                    idx = full_text.lower().find('eferences')
                    print(f"[PDF DEBUG] Found 'eferences' at position {idx}")
                    print(f"[PDF DEBUG] Context: ...{full_text[max(0,idx-50):idx+100]}...")
                else:
                    print("[PDF DEBUG] 'eferences' not found in extracted text!")

                return full_text
        except ImportError:
            raise ValueError(
                "PDF support requires PyPDF2. Install with: pip install PyPDF2"
            )

    elif suffix in ['.docx', '.doc']:
        try:
            import docx
            doc = docx.Document(path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return '\n'.join(text)
        except ImportError:
            raise ValueError(
                "DOCX support requires python-docx. Install with: pip install python-docx"
            )

    else:
        # Try to read as plain text
        try:
            return path.read_text(encoding='utf-8')
        except Exception as e:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                f"Supported formats: .txt, .md, .tex, .pdf, .docx"
            ) from e


def split_paper(text: str) -> Tuple[str, str]:
    """
    Split paper into body and references section.

    Args:
        text: Full paper content

    Returns:
        Tuple[str, str]: (body, references_section)
            - body: Main paper content before references
            - references_section: References/Bibliography section content

    Note:
        If no references section is found, returns (full_text, empty_string)
    """
    print(f"\n[SPLIT DEBUG] Input text length: {len(text)}")

    # Preprocess text
    text = _preprocess_text(text)

    # Find references section
    split_point = _find_references_section(text)

    if split_point is None:
        # No references section found
        print("[SPLIT DEBUG] No references section found!")
        print(f"[SPLIT DEBUG] Text sample (first 500): {text[:500]}")
        print(f"[SPLIT DEBUG] Text sample (last 500): {text[-500:]}")
        return text, ""

    body = text[:split_point].strip()
    references = text[split_point:].strip()

    print(f"[SPLIT DEBUG] Split at position {split_point}")
    print(f"[SPLIT DEBUG] Body length: {len(body)}, Refs length: {len(references)}")
    print(f"[SPLIT DEBUG] Refs preview (first 300): {references[:300]}")

    return body, references


def _preprocess_text(text: str) -> str:
    """
    Basic text preprocessing.

    Args:
        text: Raw text content

    Returns:
        str: Preprocessed text
    """
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Remove excessive whitespace
    text = re.sub(r' +', ' ', text)

    # Remove excessive newlines (keep max 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def _find_references_section(text: str) -> Optional[int]:
    """
    Find the start position of the references section.
    Robust matching for various PDF extraction artifacts.

    Args:
        text: Paper content

    Returns:
        Optional[int]: Start index of references section, or None if not found
    """
    # Strategy 1: Find "References" (or similar) followed by citations
    # This is more robust than looking for exact formatting

    # Pattern: "References" (with various artifacts) followed by [1] or numbered list
    patterns = [
        # Standard: "References" followed by newline and [1]
        r'(?i)references?\s*\n\s*\[1\]',
        r'(?i)bibliography\s*\n\s*\[1\]',

        # PDF artifacts: "References" with line numbers, directly followed by [1]
        r'(?i)references?\d*\s*\n?\s*\[1\]',

        # With spaces in "Refer ences"
        r'(?i)refer\s+ences?\s*\n?\s*\[1\]',

        # Numbered format: "References" followed by "1."
        r'(?i)references?\s*\n\s*1\.',

        # Just "References" word boundary (last resort)
        r'(?i)\breferences?\b',
        r'(?i)\bbibliography\b',

        # LaTeX
        r'\\begin\{thebibliography\}',

        # Markdown headers
        r'^#+\s*references?',
    ]

    best_match = None
    best_score = 0

    for i, pattern in enumerate(patterns):
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            # Earlier patterns are more specific, give them priority
            score = len(patterns) - i
            if score > best_score:
                best_score = score
                best_match = match

    if best_match:
        return best_match.start()

    # Strategy 2: Find by dense citation pattern
    return _find_references_by_pattern(text)


def _find_references_by_pattern(text: str) -> Optional[int]:
    """
    Attempt to find references section by detecting citation patterns.
    Enhanced for PDF text with irregular formatting.

    Args:
        text: Paper content

    Returns:
        Optional[int]: Start index of likely references section, or None
    """
    lines = text.split('\n')

    # Look for clusters of lines that look like citations
    citation_patterns = [
        r'^\s*\[\d+\]',  # [1] Author et al.
        r'^\s*\d+\.\s+',  # 1. Author et al.
        r'^\s*[A-Z][a-z]+,\s+[A-Z]\..*\(\d{4}\)',  # Author, A. (2024)
        r'^\s*\[\d+\]\s+[A-Z]',  # [1] Capital letter start
    ]

    citation_density = []
    window_size = 10  # Larger window for better detection

    for i in range(len(lines) - window_size):
        window = lines[i:i + window_size]
        matches = 0

        for line in window:
            stripped = line.strip()
            if not stripped:  # Skip empty lines
                continue

            for pattern in citation_patterns:
                if re.match(pattern, stripped):
                    matches += 1
                    break

        # Calculate density (non-empty lines that match)
        non_empty = sum(1 for line in window if line.strip())
        if non_empty > 0:
            density = matches / non_empty
            citation_density.append((i, density))

    # Find the first window with high citation density (>50%)
    for i, density in citation_density:
        if density > 0.5:
            # Convert line number back to character position
            char_pos = len('\n'.join(lines[:i]))
            return char_pos

    return None


def extract_citations_from_body(body: str) -> list[str]:
    """
    Extract in-text citations from paper body.

    Args:
        body: Main paper content

    Returns:
        list[str]: List of citation strings found in body
    """
    citations = []

    # Pattern 1: [1], [2,3], [4-6]
    numeric_citations = re.findall(r'\[(\d+(?:\s*[-,]\s*\d+)*)\]', body)
    for citation in numeric_citations:
        # Expand ranges like "4-6" and lists like "2,3"
        citation = citation.replace(' ', '')
        if '-' in citation:
            parts = citation.split('-')
            if len(parts) == 2:
                try:
                    start, end = int(parts[0]), int(parts[1])
                    citations.extend([str(i) for i in range(start, end + 1)])
                except ValueError:
                    citations.append(citation)
        elif ',' in citation:
            citations.extend(citation.split(','))
        else:
            citations.append(citation)

    # Pattern 2: (Author, 2024), (Author et al., 2024)
    author_year = re.findall(
        r'\(([A-Z][a-z]+(?:\s+et\s+al\.)?),?\s+(\d{4}[a-z]?)\)',
        body
    )
    citations.extend([f"{author}, {year}" for author, year in author_year])

    return citations


def extract_reference_entries(references: str) -> list[dict]:
    """
    Parse reference entries from references section.

    Args:
        references: References section content

    Returns:
        list[dict]: List of reference entries with metadata
    """
    entries = []

    # Split by common reference patterns
    lines = references.split('\n')
    current_entry = []

    for line in lines:
        line = line.strip()
        if not line:
            if current_entry:
                entries.append(_parse_reference_entry('\n'.join(current_entry)))
                current_entry = []
        elif re.match(r'^\[\d+\]|^\d+\.|^[A-Z]', line):
            if current_entry:
                entries.append(_parse_reference_entry('\n'.join(current_entry)))
            current_entry = [line]
        else:
            current_entry.append(line)

    if current_entry:
        entries.append(_parse_reference_entry('\n'.join(current_entry)))

    return entries


def _parse_reference_entry(entry: str) -> dict:
    """
    Parse a single reference entry into structured data.

    Args:
        entry: Reference entry text

    Returns:
        dict: Structured reference data
    """
    # Basic parsing - can be extended for more sophisticated parsing
    return {
        'raw': entry,
        'authors': _extract_authors(entry),
        'year': _extract_year(entry),
        'title': _extract_title(entry),
    }


def _extract_authors(entry: str) -> Optional[str]:
    """Extract author names from reference entry."""
    # Simple pattern: text before year or before first period
    match = re.match(r'^(?:\[\d+\]\s*)?([^(]+?)(?:\(|\.|\d{4})', entry)
    if match:
        return match.group(1).strip()
    return None


def _extract_year(entry: str) -> Optional[str]:
    """Extract publication year from reference entry."""
    match = re.search(r'\b(19\d{2}|20\d{2})\b', entry)
    if match:
        return match.group(1)
    return None


def _extract_title(entry: str) -> Optional[str]:
    """Extract title from reference entry."""
    # Title often appears in quotes or after author/year
    match = re.search(r'"([^"]+)"', entry)
    if match:
        return match.group(1)
    return None
