import logging
import requests
from dataclasses import dataclass
from typing import Optional, Dict, Sequence, Union
from datetime import datetime
from requests.adapters import HTTPAdapter, Retry
from src.fetchers.cache import Cache, CacheConfig, CachedResponse

logger = logging.getLogger(__name__)

@dataclass
class FetchResult:
    """Result of a fetch operation."""
    ok: bool
    content: Optional[bytes] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    cached: bool = False
    from_cache: bool = False
    age: Optional[float] = None

class CachedURLFetcher:
    """URL fetcher with intelligent caching."""
    
    def __init__(
        self,
        timeout: float = 10.0,
        retries: int = 3,
        backoff_factor: float = 0.5,
        status_forcelist: Optional[Sequence[int]] = None,
        headers: Optional[Dict[str, str]] = None,
        cache_config: Optional[Union[CacheConfig, Dict]] = None,
    ):
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.status_forcelist = status_forcelist or [408, 429, 500, 502, 503, 504]
        self.headers = headers or self._default_headers()
        
        # Initialize cache
        if isinstance(cache_config, dict):
            cache_config = CacheConfig(**cache_config)
        self.cache_config = cache_config or CacheConfig()
        self.cache = Cache(self.cache_config)
        
        # Initialize session
        self.session = self._create_session()
    
    def _default_headers(self) -> Dict[str, str]:
        """Get default HTTP headers."""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.retries,
            connect=self.retries,
            read=self.retries,
            status=self.retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=self.status_forcelist,
            allowed_methods={"GET"},
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _prepare_headers(self, cached: Optional[CachedResponse] = None) -> Dict[str, str]:
        """Prepare headers with cache validation if needed."""
        headers = self.headers.copy()
        
        if cached and self.cache_config.respect_headers:
            if cached.etag:
                headers['If-None-Match'] = cached.etag
            if cached.last_modified:
                headers['If-Modified-Since'] = cached.last_modified
        
        return headers
    
    def fetch(self, url: str, force_refresh: bool = False) -> FetchResult:
        """
        Fetch URL with caching.
        
        Args:
            url: URL to fetch
            force_refresh: If True, bypass cache and force fresh fetch
        
        Returns:
            FetchResult with content and metadata
        """
        # Check cache first (unless forcing refresh)
        if not force_refresh and self.cache_config.enabled:
            cached = self.cache.get(url, allow_stale=True)
            if cached:
                logger.debug(f"Cache hit for {url}")
                return FetchResult(
                    ok=True,
                    content=cached.content,
                    status_code=cached.status_code,
                    from_cache=True,
                    age=cached.age.total_seconds()
                )
        
        logger.debug(f"Cache miss for {url}, fetching...")
        
        try:
            # Prepare request headers
            headers = self._prepare_headers()
            
            # Make the request
            response = self.session.get(
                url,
                timeout=self.timeout,
                headers=headers
            )
            
            # Handle 304 Not Modified (content hasn't changed)
            if response.status_code == 304:
                cached = self.cache.get(url, allow_stale=True)
                if cached:
                    logger.debug(f"Content not modified for {url}, using cached version")
                    return FetchResult(
                        ok=True,
                        content=cached.content,
                        status_code=200,
                        from_cache=True,
                        age=cached.age.total_seconds()
                    )
            
            response.raise_for_status()
            
            # Create cached response
            cached_response = CachedResponse(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                cached_at=datetime.now(),
                etag=response.headers.get('ETag'),
                last_modified=response.headers.get('Last-Modified')
            )
            
            # Cache the result
            if self.cache_config.enabled:
                self.cache.set(url, cached_response)
            
            return FetchResult(
                ok=True,
                content=response.content,
                status_code=response.status_code,
                from_cache=False
            )
            
        except requests.Timeout:
            logger.warning(f"Timeout fetching {url}")
            return FetchResult(ok=False, error="timeout")
            
        except requests.HTTPError as e:
            logger.warning(f"HTTP error fetching {url}: {e}")
            return FetchResult(
                ok=False,
                status_code=e.response.status_code,
                error=f"HTTP {e.response.status_code}",
            )
            
        except requests.RequestException as e:
            logger.error(f"Request error fetching {url}: {e}")
            return FetchResult(ok=False, error=str(e))
    
    def fetch_batch(self, urls: list, force_refresh: bool = False) -> Dict[str, FetchResult]:
        """Fetch multiple URLs."""
        results = {}
        for url in urls:
            results[url] = self.fetch(url, force_refresh)
        return results
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return self.cache.get_stats()

# Keep backward compatibility
URLFetcher = CachedURLFetcher