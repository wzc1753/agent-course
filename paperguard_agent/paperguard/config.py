"""
Configuration module for PaperGuard Agent.

Loads environment variables, defines thresholds for citation verification,
and provides utility methods for API configuration and validation.
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for PaperGuard Agent."""

    # API Keys from environment
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    CROSSREF_EMAIL: Optional[str] = os.getenv("CROSSREF_EMAIL")
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

    # Verification thresholds
    MATCH_THRESHOLD_VERIFIED: float = 0.85
    LOW_CONFIDENCE: float = 0.65
    MISMATCH: float = 0.40

    # Processing limits
    MAX_CLAIMS_DEFAULT: int = 10

    # Cache settings
    CACHE_TTL: int = 3600  # Time to live in seconds (1 hour)

    @classmethod
    def validate(cls) -> Dict[str, bool]:
        """
        Validate that required configuration values are set.

        Returns:
            Dict mapping configuration keys to their validity status.

        Example:
            >>> config_status = Config.validate()
            >>> if not config_status["OPENAI_API_KEY"]:
            ...     print("Warning: OPENAI_API_KEY not set")
        """
        validation_results = {
            "OPENAI_API_KEY": cls.OPENAI_API_KEY is not None and len(cls.OPENAI_API_KEY) > 0,
            "CROSSREF_EMAIL": cls.CROSSREF_EMAIL is not None and len(cls.CROSSREF_EMAIL) > 0,
            "SEMANTIC_SCHOLAR_API_KEY": cls.SEMANTIC_SCHOLAR_API_KEY is not None and len(cls.SEMANTIC_SCHOLAR_API_KEY) > 0,
        }
        return validation_results

    @classmethod
    def get_api_headers(cls, api_name: str) -> Dict[str, str]:
        """
        Get appropriate headers for API requests.

        Args:
            api_name: Name of the API ("openai", "semantic_scholar", "crossref")

        Returns:
            Dictionary of HTTP headers for the specified API.

        Raises:
            ValueError: If api_name is not recognized or required credentials are missing.

        Example:
            >>> headers = Config.get_api_headers("semantic_scholar")
            >>> # Returns headers with API key for Semantic Scholar
        """
        if api_name == "openai":
            if not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")
            return {
                "Authorization": f"Bearer {cls.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }

        elif api_name == "semantic_scholar":
            headers = {
                "Content-Type": "application/json"
            }
            if cls.SEMANTIC_SCHOLAR_API_KEY:
                headers["x-api-key"] = cls.SEMANTIC_SCHOLAR_API_KEY
            return headers

        elif api_name == "crossref":
            headers = {
                "Content-Type": "application/json"
            }
            if cls.CROSSREF_EMAIL:
                headers["User-Agent"] = f"PaperGuard/1.0 (mailto:{cls.CROSSREF_EMAIL})"
            return headers

        else:
            raise ValueError(f"Unknown API name: {api_name}. Must be one of: openai, semantic_scholar, crossref")

    @classmethod
    def is_valid(cls) -> bool:
        """
        Check if all required configuration values are valid.

        Returns:
            True if all required configurations are set, False otherwise.
        """
        validation = cls.validate()
        return all(validation.values())

    @classmethod
    def get_missing_configs(cls) -> list[str]:
        """
        Get a list of missing configuration keys.

        Returns:
            List of configuration keys that are not properly set.
        """
        validation = cls.validate()
        return [key for key, is_valid in validation.items() if not is_valid]


# Create a default instance for convenient imports
config = Config()
