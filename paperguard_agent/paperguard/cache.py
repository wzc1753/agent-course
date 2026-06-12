"""
Cache module for PaperGuard Agent.

Provides simple JSON file-based caching with TTL support for metadata lookups.
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Any, Dict


# Default cache file location
CACHE_DIR = Path("outputs")
CACHE_FILE = CACHE_DIR / "metadata_cache.json"


def _ensure_cache_dir():
    """Ensure the cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _load_cache() -> Dict[str, Dict[str, Any]]:
    """
    Load the cache from disk.

    Returns:
        Dictionary containing cached entries with metadata.
    """
    if not CACHE_FILE.exists():
        return {}

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # If cache is corrupted, start fresh
        return {}


def _save_cache(cache_data: Dict[str, Dict[str, Any]]):
    """
    Save the cache to disk.

    Args:
        cache_data: Dictionary containing cached entries with metadata.
    """
    _ensure_cache_dir()

    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        # Log error but don't fail the operation
        print(f"Warning: Failed to save cache: {e}")


def cache_key(source: str, query: str) -> str:
    """
    Generate a unique cache key from source and query.

    Args:
        source: Source identifier (e.g., "crossref", "semantic_scholar")
        query: Query string (e.g., DOI, title, arXiv ID)

    Returns:
        A hash-based cache key string.
    """
    # Create a deterministic key by hashing source + query
    key_string = f"{source}:{query}"
    return hashlib.sha256(key_string.encode('utf-8')).hexdigest()


def cache_get(key: str) -> Optional[dict]:
    """
    Retrieve a value from the cache if it exists and hasn't expired.

    Args:
        key: Cache key to lookup.

    Returns:
        Cached value dictionary if found and valid, None otherwise.
    """
    cache_data = _load_cache()

    if key not in cache_data:
        return None

    entry = cache_data[key]

    # Check if entry has expired
    if 'expires_at' in entry and time.time() > entry['expires_at']:
        # Entry expired, remove it
        del cache_data[key]
        _save_cache(cache_data)
        return None

    return entry.get('value')


def cache_set(key: str, value: dict, ttl: int = 3600):
    """
    Store a value in the cache with an optional TTL (time-to-live).

    Args:
        key: Cache key under which to store the value.
        value: Dictionary value to cache.
        ttl: Time-to-live in seconds (default: 3600 = 1 hour).
             Set to 0 for no expiration.
    """
    cache_data = _load_cache()

    entry = {
        'value': value,
        'created_at': time.time()
    }

    # Set expiration time if TTL is specified
    if ttl > 0:
        entry['expires_at'] = time.time() + ttl

    cache_data[key] = entry
    _save_cache(cache_data)


def cache_clear():
    """
    Clear all cached entries.

    Useful for testing or forcing fresh lookups.
    """
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()


def cache_stats() -> Dict[str, Any]:
    """
    Get statistics about the current cache.

    Returns:
        Dictionary with cache statistics (total entries, expired entries, size).
    """
    cache_data = _load_cache()

    total_entries = len(cache_data)
    expired_entries = 0
    current_time = time.time()

    for entry in cache_data.values():
        if 'expires_at' in entry and current_time > entry['expires_at']:
            expired_entries += 1

    cache_size = 0
    if CACHE_FILE.exists():
        cache_size = CACHE_FILE.stat().st_size

    return {
        'total_entries': total_entries,
        'valid_entries': total_entries - expired_entries,
        'expired_entries': expired_entries,
        'cache_file_size_bytes': cache_size
    }
