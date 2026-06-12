"""
Unit tests for schemas module.
"""

import pytest
from paperguard.schemas import (
    ReviewType,
    ReviewAspect,
    ReviewRequest,
    ReviewSection,
    ReviewResult,
    ReviewHistory
)


def test_review_type_enum():
    """Test ReviewType enum values."""
    assert ReviewType.FULL.value == "full"
    assert ReviewType.QUICK.value == "quick"
    assert ReviewType.FOCUSED.value == "focused"


def test_review_aspect_enum():
    """Test ReviewAspect enum values."""
    assert ReviewAspect.NOVELTY.value == "novelty"
    assert ReviewAspect.METHODOLOGY.value == "methodology"
    assert ReviewAspect.ALL.value == "all"


def test_review_request_creation():
    """Test ReviewRequest model creation."""
    request = ReviewRequest(
        paper_content="This is a test paper content.",
        review_type=ReviewType.FULL,
        focus_aspects=[ReviewAspect.NOVELTY, ReviewAspect.METHODOLOGY]
    )
    assert request.paper_content == "This is a test paper content."
    assert request.review_type == ReviewType.FULL
    assert len(request.focus_aspects) == 2
    assert request.additional_instructions is None


def test_review_section_creation():
    """Test ReviewSection model creation."""
    section = ReviewSection(
        title="Introduction",
        content="The introduction is well-written.",
        severity="minor",
        line_references=[1, 2, 3]
    )
    assert section.title == "Introduction"
    assert section.content == "The introduction is well-written."
    assert section.severity == "minor"
    assert section.line_references == [1, 2, 3]


def test_review_result_creation():
    """Test ReviewResult model creation."""
    result = ReviewResult(
        summary="Good paper overall",
        strengths=["Novel approach", "Clear writing"],
        weaknesses=["Limited experiments"],
        overall_score=7.5,
        recommendation="Accept",
        confidence=4.0
    )
    assert result.summary == "Good paper overall"
    assert len(result.strengths) == 2
    assert len(result.weaknesses) == 1
    assert result.overall_score == 7.5
    assert result.recommendation == "Accept"
    assert result.confidence == 4.0
    assert result.timestamp is not None


def test_review_result_score_validation():
    """Test ReviewResult score validation."""
    # Valid scores
    result = ReviewResult(summary="Test", overall_score=5.5)
    assert result.overall_score == 5.5

    # Invalid scores should raise validation error
    with pytest.raises(Exception):
        ReviewResult(summary="Test", overall_score=11.0)

    with pytest.raises(Exception):
        ReviewResult(summary="Test", overall_score=0.5)


def test_review_history_creation():
    """Test ReviewHistory model creation."""
    history = ReviewHistory(
        paper_id="paper_123",
        paper_title="Test Paper"
    )
    assert history.paper_id == "paper_123"
    assert history.paper_title == "Test Paper"
    assert len(history.reviews) == 0
    assert history.created_at is not None
