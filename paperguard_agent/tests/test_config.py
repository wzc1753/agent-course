"""
Unit tests for configuration module.
"""

import pytest
import os
from paperguard.config import Config


def test_config_default_values():
    """Test default configuration values."""
    config = Config()
    assert config.model_name == "claude-opus-4-20250514"
    assert config.max_tokens == 4096
    assert config.temperature == 0.0
    assert config.max_file_size_mb == 10
    assert ".pdf" in config.allowed_extensions


def test_config_api_key_validation():
    """Test API key validation."""
    config = Config(anthropic_api_key="")
    assert not config.validate_api_key()

    config = Config(anthropic_api_key="sk-ant-test123")
    assert config.validate_api_key()


def test_config_from_env():
    """Test configuration from environment variables."""
    os.environ["ANTHROPIC_API_KEY"] = "test_key_from_env"
    config = Config()
    assert config.anthropic_api_key == "test_key_from_env"
    del os.environ["ANTHROPIC_API_KEY"]


def test_config_custom_values():
    """Test custom configuration values."""
    config = Config(
        anthropic_api_key="custom_key",
        model_name="claude-sonnet-4-20250514",
        max_tokens=8000,
        temperature=0.5
    )
    assert config.anthropic_api_key == "custom_key"
    assert config.model_name == "claude-sonnet-4-20250514"
    assert config.max_tokens == 8000
    assert config.temperature == 0.5
