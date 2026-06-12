"""
API clients for external metadata sources.

Provides unified interface to query CrossRef, Semantic Scholar, OpenAlex, and arXiv.
Handles rate limiting, error handling, and response normalization.
"""

import time
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .schemas import ExternalCandidate
from .config import Config

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter to prevent API throttling."""

    def __init__(self, calls_per_second: float = 1.0):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0

    def wait(self):
        """Wait if necessary to respect rate limit."""
        now = time.time()
        time_since_last = now - self.last_call
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        self.last_call = time.time()


def create_session(max_retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    """
    Create a requests session with retry logic.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Backoff factor for exponential retry

    Returns:
        Configured requests.Session object
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        backoff_factor=backoff_factor
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# Global session and rate limiters
_session = create_session()
_crossref_limiter = RateLimiter(calls_per_second=0.5)  # Conservative: 30 req/min
_semantic_scholar_limiter = RateLimiter(calls_per_second=10.0)  # 100 req/sec with API key
_openalex_limiter = RateLimiter(calls_per_second=10.0)  # Polite pool: 10 req/sec
_arxiv_limiter = RateLimiter(calls_per_second=0.33)  # Conservative: ~20 req/min


def search_crossref(
    title: Optional[str] = None,
    authors: Optional[List[str]] = None,
    year: Optional[int] = None,
    max_results: int = 5,
    timeout: int = 10
) -> List[ExternalCandidate]:
    """
    Search CrossRef API for bibliographic metadata.

    Args:
        title: Article title
        authors: List of author names
        year: Publication year
        max_results: Maximum number of results to return
        timeout: Request timeout in seconds

    Returns:
        List of ExternalCandidate objects
    """
    if not title and not authors:
        return []

    _crossref_limiter.wait()

    # Build query
    query_parts = []
    if title:
        query_parts.append(title)
    if authors:
        query_parts.extend(authors)

    query = " ".join(query_parts)

    url = "https://api.crossref.org/works"
    params = {
        "query": query,
        "rows": max_results
    }

    # Add polite email if configured
    if Config.CROSSREF_EMAIL:
        params["mailto"] = Config.CROSSREF_EMAIL

    # Add year filter if provided
    if year:
        params["filter"] = f"from-pub-date:{year},until-pub-date:{year}"

    try:
        response = _session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("message", {}).get("items", []):
            candidate = _parse_crossref_item(item)
            if candidate:
                results.append(candidate)

        logger.debug(f"CrossRef returned {len(results)} results for query: {query[:50]}...")
        return results

    except requests.exceptions.RequestException as e:
        logger.warning(f"CrossRef API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in CrossRef search: {e}")
        return []


def _parse_crossref_item(item: Dict[str, Any]) -> Optional[ExternalCandidate]:
    """Parse a CrossRef API response item into ExternalCandidate."""
    try:
        # Extract title
        title_list = item.get("title", [])
        title = title_list[0] if title_list else None
        if not title:
            return None

        # Extract authors
        authors = []
        for author in item.get("author", []):
            family = author.get("family", "")
            given = author.get("given", "")
            if family:
                full_name = f"{given} {family}".strip() if given else family
                authors.append(full_name)

        # Extract year
        year = None
        pub_date = item.get("published-print") or item.get("published-online")
        if pub_date and "date-parts" in pub_date:
            date_parts = pub_date["date-parts"][0]
            if date_parts:
                year = date_parts[0]

        # Extract venue
        venue_list = item.get("container-title", [])
        venue = venue_list[0] if venue_list else None

        # Extract DOI
        doi = item.get("DOI")

        # Extract abstract (if available)
        abstract = item.get("abstract")

        # Build URL
        url = f"https://doi.org/{doi}" if doi else item.get("URL")

        return ExternalCandidate(
            source="crossref",
            title=title,
            authors=authors,
            year=year,
            venue=venue,
            doi=doi,
            abstract=abstract,
            url=url,
            raw=item
        )

    except Exception as e:
        logger.warning(f"Error parsing CrossRef item: {e}")
        return None


def search_semantic_scholar(
    title: Optional[str] = None,
    max_results: int = 5,
    timeout: int = 10
) -> List[ExternalCandidate]:
    """
    Search Semantic Scholar API for paper metadata.

    Args:
        title: Paper title
        max_results: Maximum number of results to return
        timeout: Request timeout in seconds

    Returns:
        List of ExternalCandidate objects
    """
    if not title:
        return []

    _semantic_scholar_limiter.wait()

    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": title,
        "limit": max_results,
        "fields": "title,authors,year,venue,externalIds,abstract,url"
    }

    headers = {}
    if Config.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = Config.SEMANTIC_SCHOLAR_API_KEY

    try:
        response = _session.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("data", []):
            candidate = _parse_semantic_scholar_item(item)
            if candidate:
                results.append(candidate)

        logger.debug(f"Semantic Scholar returned {len(results)} results for: {title[:50]}...")
        return results

    except requests.exceptions.RequestException as e:
        logger.warning(f"Semantic Scholar API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in Semantic Scholar search: {e}")
        return []


def _parse_semantic_scholar_item(item: Dict[str, Any]) -> Optional[ExternalCandidate]:
    """Parse a Semantic Scholar API response item into ExternalCandidate."""
    try:
        title = item.get("title")
        if not title:
            return None

        # Extract authors
        authors = []
        for author in item.get("authors", []):
            name = author.get("name")
            if name:
                authors.append(name)

        # Extract year
        year = item.get("year")

        # Extract venue
        venue = item.get("venue")

        # Extract DOI from externalIds
        doi = None
        external_ids = item.get("externalIds", {})
        if external_ids:
            doi = external_ids.get("DOI")

        # Extract abstract
        abstract = item.get("abstract")

        # Extract URL
        url = item.get("url")

        return ExternalCandidate(
            source="semantic_scholar",
            title=title,
            authors=authors,
            year=year,
            venue=venue,
            doi=doi,
            abstract=abstract,
            url=url,
            raw=item
        )

    except Exception as e:
        logger.warning(f"Error parsing Semantic Scholar item: {e}")
        return None


def search_openalex(
    title: Optional[str] = None,
    authors: Optional[List[str]] = None,
    max_results: int = 5,
    timeout: int = 10
) -> List[ExternalCandidate]:
    """
    Search OpenAlex API for scholarly work metadata.

    Args:
        title: Work title
        authors: List of author names
        max_results: Maximum number of results to return
        timeout: Request timeout in seconds

    Returns:
        List of ExternalCandidate objects
    """
    if not title and not authors:
        return []

    _openalex_limiter.wait()

    # Build search filter
    filters = []
    if title:
        # OpenAlex uses display_name for title search
        filters.append(f"display_name.search:{title}")
    if authors:
        # Search for any of the authors
        author_query = " ".join(authors)
        filters.append(f"authorships.author.display_name.search:{author_query}")

    filter_str = ",".join(filters)

    url = "https://api.openalex.org/works"
    params = {
        "filter": filter_str,
        "per_page": max_results
    }

    # Add polite email to user agent if configured
    headers = {"User-Agent": "PaperGuard"}
    if Config.CROSSREF_EMAIL:
        headers["User-Agent"] = f"PaperGuard (mailto:{Config.CROSSREF_EMAIL})"

    try:
        response = _session.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", []):
            candidate = _parse_openalex_item(item)
            if candidate:
                results.append(candidate)

        logger.debug(f"OpenAlex returned {len(results)} results")
        return results

    except requests.exceptions.RequestException as e:
        logger.warning(f"OpenAlex API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in OpenAlex search: {e}")
        return []


def _parse_openalex_item(item: Dict[str, Any]) -> Optional[ExternalCandidate]:
    """Parse an OpenAlex API response item into ExternalCandidate."""
    try:
        title = item.get("display_name") or item.get("title")
        if not title:
            return None

        # Extract authors
        authors = []
        for authorship in item.get("authorships", []):
            author = authorship.get("author", {})
            name = author.get("display_name")
            if name:
                authors.append(name)

        # Extract year
        year = item.get("publication_year")

        # Extract venue (primary location)
        venue = None
        primary_location = item.get("primary_location", {})
        if primary_location:
            source = primary_location.get("source", {})
            venue = source.get("display_name")

        # Extract DOI
        doi = item.get("doi")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")

        # Extract abstract (OpenAlex provides inverted index)
        abstract = None
        abstract_inverted_index = item.get("abstract_inverted_index")
        if abstract_inverted_index:
            # Reconstruct abstract from inverted index
            abstract = _reconstruct_abstract(abstract_inverted_index)

        # Extract URL
        url = doi and f"https://doi.org/{doi}" or item.get("id")

        return ExternalCandidate(
            source="openalex",
            title=title,
            authors=authors,
            year=year,
            venue=venue,
            doi=doi,
            abstract=abstract,
            url=url,
            raw=item
        )

    except Exception as e:
        logger.warning(f"Error parsing OpenAlex item: {e}")
        return None


def _reconstruct_abstract(inverted_index: Dict[str, List[int]]) -> str:
    """Reconstruct abstract text from OpenAlex inverted index."""
    try:
        # Create list of (word, position) tuples
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))

        # Sort by position and join
        word_positions.sort(key=lambda x: x[0])
        abstract = " ".join([word for _, word in word_positions])
        return abstract

    except Exception as e:
        logger.warning(f"Error reconstructing abstract: {e}")
        return None


def search_arxiv(
    title: Optional[str] = None,
    max_results: int = 5,
    timeout: int = 10
) -> List[ExternalCandidate]:
    """
    Search arXiv API for preprint metadata.

    Args:
        title: Paper title
        max_results: Maximum number of results to return
        timeout: Request timeout in seconds

    Returns:
        List of ExternalCandidate objects
    """
    if not title:
        return []

    _arxiv_limiter.wait()

    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"ti:{quote(title)}",
        "start": 0,
        "max_results": max_results
    }

    try:
        response = _session.get(url, params=params, timeout=timeout)
        response.raise_for_status()

        # Parse XML response
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)

        # Define namespace
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom"
        }

        results = []
        for entry in root.findall("atom:entry", ns):
            candidate = _parse_arxiv_entry(entry, ns)
            if candidate:
                results.append(candidate)

        logger.debug(f"arXiv returned {len(results)} results for: {title[:50]}...")
        return results

    except requests.exceptions.RequestException as e:
        logger.warning(f"arXiv API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in arXiv search: {e}")
        return []


def _parse_arxiv_entry(entry, ns: Dict[str, str]) -> Optional[ExternalCandidate]:
    """Parse an arXiv API entry into ExternalCandidate."""
    try:
        # Extract title
        title_elem = entry.find("atom:title", ns)
        title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else None
        if not title:
            return None

        # Extract authors
        authors = []
        for author in entry.findall("atom:author", ns):
            name_elem = author.find("atom:name", ns)
            if name_elem is not None:
                authors.append(name_elem.text.strip())

        # Extract year from published date
        year = None
        published_elem = entry.find("atom:published", ns)
        if published_elem is not None:
            date_str = published_elem.text
            year = int(date_str[:4])

        # Extract arXiv ID and build URL
        arxiv_id = None
        url_elem = entry.find("atom:id", ns)
        if url_elem is not None:
            url = url_elem.text
            # Extract ID from URL (e.g., http://arxiv.org/abs/2101.12345v1)
            if "abs/" in url:
                arxiv_id = url.split("abs/")[-1]

        # Extract abstract
        abstract = None
        summary_elem = entry.find("atom:summary", ns)
        if summary_elem is not None:
            abstract = summary_elem.text.strip().replace("\n", " ")

        # Extract DOI if available
        doi = None
        doi_elem = entry.find("arxiv:doi", ns)
        if doi_elem is not None:
            doi = doi_elem.text.strip()

        return ExternalCandidate(
            source="arxiv",
            title=title,
            authors=authors,
            year=year,
            venue="arXiv",
            doi=doi,
            abstract=abstract,
            url=url,
            raw={"arxiv_id": arxiv_id}
        )

    except Exception as e:
        logger.warning(f"Error parsing arXiv entry: {e}")
        return None


def search_all_sources(
    title: Optional[str] = None,
    authors: Optional[List[str]] = None,
    year: Optional[int] = None,
    max_results_per_source: int = 3
) -> List[ExternalCandidate]:
    """
    Search all available metadata sources and combine results.

    Args:
        title: Paper title
        authors: List of author names
        year: Publication year
        max_results_per_source: Maximum results from each source

    Returns:
        Combined list of ExternalCandidate objects from all sources
    """
    all_candidates = []

    # Search each source
    if title:
        all_candidates.extend(search_crossref(title, authors, year, max_results_per_source))
        all_candidates.extend(search_semantic_scholar(title, max_results_per_source))
        all_candidates.extend(search_openalex(title, authors, max_results_per_source))
        all_candidates.extend(search_arxiv(title, max_results_per_source))

    logger.info(f"Found {len(all_candidates)} total candidates from all sources")
    return all_candidates
