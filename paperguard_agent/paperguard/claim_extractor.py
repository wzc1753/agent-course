"""Claim extraction module for PaperGuard Agent.

This module identifies high-risk claims in academic text that require citation
verification, including sentences with citations, strong claims, and numeric results.
"""

import re
from typing import List, Dict, Set, Literal


# Risk keywords that indicate strong claims requiring verification
HIGH_RISK_KEYWORDS = {
    'first', 'novel', 'prove', 'proves', 'proved', 'proven',
    'guarantee', 'guarantees', 'guaranteed',
    'always', 'never', 'all', 'none', 'every',
    'solves', 'solved', 'solve',
    'best', 'optimal', 'perfect',
    'impossible', 'certain', 'definitely'
}

MEDIUM_RISK_KEYWORDS = {
    'significantly', 'substantially', 'dramatically',
    'outperforms', 'outperform', 'outperformed',
    'sota', 'state-of-the-art', 'state of the art',
    'superior', 'better', 'improved',
    'achieves', 'achieve', 'achieved'
}


class ClaimExtractor:
    """Extracts verifiable claims from academic text."""

    # Citation patterns
    NUMERIC_CITATION = r'\[\d+(?:\s*,\s*\d+)*(?:\s*-\s*\d+)?\]'
    LATEX_CITATION = r'\\cite\{[^}]+\}'

    # Numeric result patterns (e.g., "95.3%", "10x faster", "5.2 points")
    NUMERIC_RESULT_PATTERN = r'\d+\.?\d*\s*(?:%|×|x|points?|pp|percent)\b'

    # Comparison patterns
    COMPARISON_PATTERN = r'\b(?:outperform|exceed|surpass|improve|increase|decrease|reduce|better than|worse than|higher than|lower than)\b'

    def __init__(self):
        """Initialize the claim extractor."""
        self.high_risk_keywords = HIGH_RISK_KEYWORDS
        self.medium_risk_keywords = MEDIUM_RISK_KEYWORDS

    def _split_into_sentences(self, text: str) -> List[Dict[str, any]]:
        """Split text into sentences with position tracking.

        Args:
            text: Input text to split

        Returns:
            List of dicts with 'text', 'start', 'end' keys
        """
        # Simple sentence splitting (could be improved with nltk/spacy)
        # Handles common abbreviations to avoid false splits
        sentences = []

        # Replace common abbreviations temporarily
        text_processed = text
        abbreviations = ['Dr.', 'Prof.', 'et al.', 'i.e.', 'e.g.', 'etc.', 'vs.', 'Fig.', 'Table']
        for i, abbr in enumerate(abbreviations):
            text_processed = text_processed.replace(abbr, f'__ABBR{i}__')

        # Split on sentence boundaries
        pattern = r'([.!?]+)\s+'
        parts = re.split(pattern, text_processed)

        current_pos = 0
        current_sentence = ''

        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Text part
                current_sentence += part
            else:
                # Punctuation part
                current_sentence += part

                # Restore abbreviations
                restored = current_sentence
                for j, abbr in enumerate(abbreviations):
                    restored = restored.replace(f'__ABBR{j}__', abbr)

                sentence_text = restored.strip()
                if sentence_text:
                    start = text.find(sentence_text, current_pos)
                    if start == -1:
                        # Fallback if exact match fails
                        start = current_pos
                    end = start + len(sentence_text)

                    sentences.append({
                        'text': sentence_text,
                        'start': start,
                        'end': end
                    })
                    current_pos = end

                current_sentence = ''

        # Handle last sentence if no ending punctuation
        if current_sentence.strip():
            restored = current_sentence
            for j, abbr in enumerate(abbreviations):
                restored = restored.replace(f'__ABBR{j}__', abbr)
            sentence_text = restored.strip()

            if sentence_text:
                start = text.find(sentence_text, current_pos)
                if start == -1:
                    start = current_pos
                end = start + len(sentence_text)

                sentences.append({
                    'text': sentence_text,
                    'start': start,
                    'end': end
                })

        return sentences

    def _has_citation(self, sentence: str) -> bool:
        """Check if sentence contains a citation.

        Args:
            sentence: Sentence text to check

        Returns:
            True if citation found
        """
        has_numeric = bool(re.search(self.NUMERIC_CITATION, sentence))
        has_latex = bool(re.search(self.LATEX_CITATION, sentence))
        return has_numeric or has_latex

    def _extract_citations(self, sentence: str) -> List[str]:
        """Extract citation markers from sentence.

        Args:
            sentence: Sentence text

        Returns:
            List of citation strings found
        """
        citations = []

        # Find numeric citations
        for match in re.finditer(self.NUMERIC_CITATION, sentence):
            citations.append(match.group(0))

        # Find LaTeX citations
        for match in re.finditer(self.LATEX_CITATION, sentence):
            citations.append(match.group(0))

        return citations

    def _find_keywords(self, sentence: str) -> Dict[str, Set[str]]:
        """Find risk keywords in sentence.

        Args:
            sentence: Sentence text (case-insensitive search)

        Returns:
            Dict with 'high' and 'medium' sets of found keywords
        """
        sentence_lower = sentence.lower()

        # Tokenize roughly (split on word boundaries)
        words = re.findall(r'\b\w+(?:[-\s]\w+)*\b', sentence_lower)
        sentence_tokens = set(words)

        # Also check for multi-word phrases
        found_high = set()
        found_medium = set()

        for keyword in self.high_risk_keywords:
            if keyword in sentence_tokens or keyword in sentence_lower:
                found_high.add(keyword)

        for keyword in self.medium_risk_keywords:
            if keyword in sentence_tokens or keyword in sentence_lower:
                found_medium.add(keyword)

        return {
            'high': found_high,
            'medium': found_medium
        }

    def _has_numeric_result(self, sentence: str) -> bool:
        """Check if sentence contains numeric results or comparisons.

        Args:
            sentence: Sentence text

        Returns:
            True if numeric results found
        """
        has_numeric = bool(re.search(self.NUMERIC_RESULT_PATTERN, sentence, re.IGNORECASE))
        has_comparison = bool(re.search(self.COMPARISON_PATTERN, sentence, re.IGNORECASE))

        # Consider it a numeric result if both pattern and comparison exist
        return has_numeric and has_comparison

    def _calculate_risk_level(
        self,
        has_citation: bool,
        keywords_found: Dict[str, Set[str]],
        has_numeric: bool
    ) -> Literal['HIGH', 'MEDIUM', 'LOW']:
        """Calculate risk level for a claim.

        Args:
            has_citation: Whether sentence has citations
            keywords_found: Dict of keyword sets by risk level
            has_numeric: Whether sentence has numeric results

        Returns:
            Risk level string
        """
        # High risk: Strong claims with citations OR numeric results with citations
        if keywords_found['high'] and has_citation:
            return 'HIGH'

        if has_numeric and has_citation:
            return 'HIGH'

        # Medium risk: Medium keywords with citations OR strong claims without citations
        if keywords_found['medium'] and has_citation:
            return 'MEDIUM'

        if keywords_found['high'] and not has_citation:
            return 'MEDIUM'

        # Low risk: Has citation but no strong indicators
        if has_citation:
            return 'LOW'

        # Low risk: Has indicators but no citation
        if keywords_found['medium'] or has_numeric:
            return 'LOW'

        return 'LOW'

    def extract_claims(
        self,
        text: str,
        citations: List[str] = None,
        max_claims: int = None
    ) -> List[Dict]:
        """Extract verifiable claims from text.

        Args:
            text: Academic text to analyze
            citations: Optional list of known citation markers (not used in current impl)
            max_claims: Maximum number of claims to return (highest risk first)

        Returns:
            List of claim dicts with keys:
                - sentence: The sentence text
                - risk_level: 'HIGH', 'MEDIUM', or 'LOW'
                - keywords_found: List of risk keywords found
                - has_citation: Boolean
                - citations: List of citation markers
                - has_numeric_result: Boolean
                - position: Dict with 'start' and 'end' char positions
        """
        sentences = self._split_into_sentences(text)
        claims = []

        for sent_info in sentences:
            sentence = sent_info['text']

            # Check for citations
            has_citation = self._has_citation(sentence)
            citation_markers = self._extract_citations(sentence)

            # Check for risk keywords
            keywords_found = self._find_keywords(sentence)

            # Check for numeric results
            has_numeric = self._has_numeric_result(sentence)

            # Calculate risk level
            risk_level = self._calculate_risk_level(
                has_citation=has_citation,
                keywords_found=keywords_found,
                has_numeric=has_numeric
            )

            # Only include if there's something notable (citation, keyword, or numeric)
            if has_citation or keywords_found['high'] or keywords_found['medium'] or has_numeric:
                all_keywords_found = list(keywords_found['high'].union(keywords_found['medium']))

                claims.append({
                    'sentence': sentence,
                    'risk_level': risk_level,
                    'keywords_found': all_keywords_found,
                    'has_citation': has_citation,
                    'citations': citation_markers,
                    'has_numeric_result': has_numeric,
                    'position': {
                        'start': sent_info['start'],
                        'end': sent_info['end']
                    }
                })

        # Sort by risk level (HIGH > MEDIUM > LOW) and then by position
        risk_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        claims.sort(key=lambda c: (risk_order[c['risk_level']], c['position']['start']))

        # Limit if max_claims specified
        if max_claims is not None and max_claims > 0:
            claims = claims[:max_claims]

        return claims


def extract_claims(
    text: str,
    citations: List[str] = None,
    max_claims: int = None
) -> List[Dict]:
    """Convenience function to extract claims from text.

    Args:
        text: Academic text to analyze
        citations: Optional list of known citation markers
        max_claims: Maximum number of claims to return

    Returns:
        List of claim dictionaries

    Example:
        >>> text = "Our method achieves 95% accuracy [1]. This is the first approach to solve this problem."
        >>> claims = extract_claims(text, max_claims=5)
        >>> len(claims)
        2
        >>> claims[0]['risk_level']
        'HIGH'
    """
    extractor = ClaimExtractor()
    return extractor.extract_claims(text, citations, max_claims)
