"""Citation extraction module for PaperGuard Agent.

This module extracts citation mentions from academic text, supporting multiple
citation formats including numeric brackets [1], [1,2], [1-3] and LaTeX \cite{key}.
"""

import re
from dataclasses import dataclass
from typing import List, Set, Tuple


@dataclass
class CitationMention:
    """Represents a citation mention found in text.

    Attributes:
        citation_keys: Set of citation identifiers (numeric IDs or BibTeX keys)
        context: The sentence or text snippet containing the citation
        position: Character position in the original text
        format_type: Type of citation format ('numeric' or 'latex')
    """
    citation_keys: Set[str]
    context: str
    position: int
    format_type: str

    def __repr__(self) -> str:
        keys_str = ', '.join(sorted(self.citation_keys))
        return f"CitationMention(keys={{{keys_str}}}, pos={self.position}, format={self.format_type})"


class CitationExtractor:
    """Extracts citations from academic text."""

    # Regex patterns for different citation formats
    NUMERIC_PATTERN = r'\[(\d+(?:\s*,\s*\d+)*(?:\s*-\s*\d+)?)\]'
    LATEX_PATTERN = r'\\cite\{([^}]+)\}'

    # Context window: number of characters before/after citation
    CONTEXT_WINDOW = 150

    @staticmethod
    def _expand_numeric_range(range_str: str) -> Set[str]:
        """Expand numeric citation ranges like '1-3' to {'1', '2', '3'}.

        Args:
            range_str: String containing numbers, commas, and/or dashes (e.g., '1,2,5-7')

        Returns:
            Set of string-formatted citation numbers
        """
        citation_ids = set()

        # Split by commas first
        parts = [part.strip() for part in range_str.split(',')]

        for part in parts:
            if '-' in part:
                # Handle range like '5-7'
                try:
                    start, end = part.split('-')
                    start_num = int(start.strip())
                    end_num = int(end.strip())
                    citation_ids.update(str(i) for i in range(start_num, end_num + 1))
                except (ValueError, AttributeError):
                    # If parsing fails, skip this part
                    continue
            else:
                # Single number
                try:
                    citation_ids.add(str(int(part)))
                except ValueError:
                    # If parsing fails, skip this part
                    continue

        return citation_ids

    @staticmethod
    def _extract_sentence_context(text: str, position: int, window: int = CONTEXT_WINDOW) -> str:
        """Extract sentence context around a citation.

        Attempts to extract the full sentence containing the citation. If sentence
        boundaries cannot be determined, falls back to a character window.

        Args:
            text: The full text
            position: Character position of the citation
            window: Fallback character window size

        Returns:
            Context string containing the citation
        """
        # Try to find sentence boundaries (simple heuristic)
        # Look backwards for sentence start
        start = max(0, position - window)
        for i in range(position - 1, start, -1):
            if text[i] in '.!?' and i + 1 < len(text) and text[i + 1].isspace():
                start = i + 1
                break

        # Look forwards for sentence end
        end = min(len(text), position + window)
        for i in range(position, end):
            if text[i] in '.!?' and (i + 1 >= len(text) or text[i + 1].isspace()):
                end = i + 1
                break

        # Extract and clean up context
        context = text[start:end].strip()

        # Remove excessive whitespace
        context = re.sub(r'\s+', ' ', context)

        return context

    def extract_citations(self, text: str) -> List[CitationMention]:
        """Extract all citations from text.

        Supports multiple citation formats:
        - Numeric: [1], [2,3], [5-7], [1, 2, 5-7]
        - LaTeX: \cite{key}, \cite{key1,key2}

        Args:
            text: Academic text to extract citations from

        Returns:
            List of CitationMention objects, sorted by position
        """
        citations = []

        # Extract numeric citations [1], [1,2], [1-3]
        for match in re.finditer(self.NUMERIC_PATTERN, text):
            position = match.start()
            range_str = match.group(1)

            # Expand ranges and comma-separated lists
            citation_keys = self._expand_numeric_range(range_str)

            if citation_keys:  # Only add if we successfully parsed citations
                context = self._extract_sentence_context(text, position)
                citations.append(CitationMention(
                    citation_keys=citation_keys,
                    context=context,
                    position=position,
                    format_type='numeric'
                ))

        # Extract LaTeX citations \cite{key}
        for match in re.finditer(self.LATEX_PATTERN, text):
            position = match.start()
            keys_str = match.group(1)

            # Split multiple keys: \cite{key1,key2,key3}
            citation_keys = {key.strip() for key in keys_str.split(',') if key.strip()}

            if citation_keys:
                context = self._extract_sentence_context(text, position)
                citations.append(CitationMention(
                    citation_keys=citation_keys,
                    context=context,
                    position=position,
                    format_type='latex'
                ))

        # Sort by position in text
        citations.sort(key=lambda c: c.position)

        return citations

    def get_all_cited_keys(self, text: str) -> Set[str]:
        """Get all unique citation keys/IDs mentioned in text.

        Args:
            text: Academic text to extract citations from

        Returns:
            Set of all citation keys (as strings)
        """
        citations = self.extract_citations(text)
        all_keys = set()
        for citation in citations:
            all_keys.update(citation.citation_keys)
        return all_keys

    def count_citations(self, text: str) -> Tuple[int, int]:
        """Count citation mentions and unique citations.

        Args:
            text: Academic text to analyze

        Returns:
            Tuple of (mention_count, unique_citation_count)
        """
        citations = self.extract_citations(text)
        mention_count = len(citations)
        unique_keys = self.get_all_cited_keys(text)
        unique_count = len(unique_keys)
        return mention_count, unique_count


def extract_citations(text: str) -> List[CitationMention]:
    """Convenience function to extract citations from text.

    Args:
        text: Academic text to extract citations from

    Returns:
        List of CitationMention objects

    Example:
        >>> text = "Recent work [1,2] shows improvements. See [5-7] for details."
        >>> citations = extract_citations(text)
        >>> len(citations)
        2
        >>> citations[0].citation_keys
        {'1', '2'}
    """
    extractor = CitationExtractor()
    return extractor.extract_citations(text)
