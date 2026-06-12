"""
Unit tests for utils module.
"""

import pytest
from pathlib import Path
from paperguard.utils import (
    validate_file,
    generate_file_hash,
    save_review_to_file
)
from paperguard.schemas import ReviewResult
import tempfile
import os


def test_validate_file_nonexistent():
    """Test validation of non-existent file."""
    is_valid, error = validate_file("nonexistent.pdf")
    assert not is_valid
    assert "does not exist" in error


def test_validate_file_extension():
    """Test validation of file extension."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        is_valid, error = validate_file(tmp_path)
        assert not is_valid
        assert "not allowed" in error
    finally:
        os.unlink(tmp_path)


def test_validate_file_size():
    """Test validation of file size."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        # Create a file larger than 1MB
        tmp.write(b"x" * (2 * 1024 * 1024))
        tmp_path = tmp.name

    try:
        is_valid, error = validate_file(tmp_path, max_size_mb=1)
        assert not is_valid
        assert "exceeds maximum" in error
    finally:
        os.unlink(tmp_path)


def test_validate_file_success():
    """Test successful file validation."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = tmp.name

    try:
        is_valid, error = validate_file(tmp_path)
        assert is_valid
        assert error is None
    finally:
        os.unlink(tmp_path)


def test_generate_file_hash():
    """Test file hash generation."""
    content1 = "This is test content"
    content2 = "This is different content"

    hash1 = generate_file_hash(content1)
    hash2 = generate_file_hash(content1)
    hash3 = generate_file_hash(content2)

    assert hash1 == hash2  # Same content produces same hash
    assert hash1 != hash3  # Different content produces different hash
    assert len(hash1) == 64  # SHA256 produces 64 character hex string


def test_save_review_to_file():
    """Test saving review to markdown file."""
    review = ReviewResult(
        summary="Test summary",
        strengths=["Strength 1", "Strength 2"],
        weaknesses=["Weakness 1"],
        overall_score=8.0,
        recommendation="Accept"
    )

    with tempfile.NamedTemporaryFile(mode='w', suffix=".md", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        save_review_to_file(review, tmp_path)

        # Verify file was created and contains expected content
        with open(tmp_path, 'r') as f:
            content = f.read()

        assert "# Paper Review" in content
        assert "Test summary" in content
        assert "Strength 1" in content
        assert "Weakness 1" in content
        assert "8.0/10" in content
        assert "Accept" in content
    finally:
        os.unlink(tmp_path)
