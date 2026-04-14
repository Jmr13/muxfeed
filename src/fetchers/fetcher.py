import requests
from dataclasses import dataclass
from typing import Optional, Dict, Sequence, Union
from datetime import datetime
from requests.adapters import HTTPAdapter, Retry
from src.fetchers.cache import Cache, CacheConfig, CachedResponse

@dataclass
class FetchResult:
    ok: bool
    content: Optional[bytes] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    cached: bool = False
    from_cache: bool = False
    age: Optional[float] = None

class URLFetcher:
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
        
        if isinstance(cache_config, dict):
            cache_config = CacheConfig(**cache_config)
        self.cache_config = cache_config or CacheConfig()
        self.cache = Cache(self.cache_config)
        
        self.session = self._create_session()
    
    def _default_headers(self) -> Dict[str, str]:
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
        headers = self.headers.copy()
        
        if cached and self.cache_config.respect_headers:
            if cached.etag:
                headers['If-None-Match'] = cached.etag
            if cached.last_modified:
                headers['If-Modified-Since'] = cached.last_modified
        
        return headers
    
    def fetch(self, url: str, force_refresh: bool = False) -> FetchResult:
        cached = None
    
        if not force_refresh and self.cache_config.enabled:
            cached = self.cache.get(url, allow_stale=True)
    
        headers = self._prepare_headers(cached)
    
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                headers=headers
            )
    
            if response.status_code == 304 and cached:
                cached.cached_at = datetime.now()
                self.cache.set(url, cached)
                return FetchResult(
                    ok=True,
                    content=cached.content,
                    status_code=200,
                    from_cache=True,
                    age=cached.age.total_seconds()
                )
    
            response.raise_for_status()
            content = response.content
    
            new_cached = CachedResponse(
                content=content,
                status_code=response.status_code,
                headers=dict(response.headers),
                cached_at=datetime.now(),
                etag=response.headers.get("ETag"),
                last_modified=response.headers.get("Last-Modified")
            )
    
            if self.cache_config.enabled:
                self.cache.set(url, new_cached)
    
            return FetchResult(
                ok=True,
                content=content,
                status_code=response.status_code,
                from_cache=False,
            )
    
        except requests.Timeout:
            return FetchResult(ok=False, error="timeout")
    
        except requests.HTTPError as e:
            return FetchResult(
                ok=False,
                status_code=e.response.status_code,
                error=f"HTTP {e.response.status_code}",
            )
    
        except requests.RequestException as e:
            return FetchResult(ok=False, error=str(e))
    
    def fetch_batch(self, urls: list, force_refresh: bool = False) -> Dict[str, FetchResult]:
        results = {}
        for url in urls:
            results[url] = self.fetch(url, force_refresh)
        return results
    
    def clear_cache(self):
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict:
        return self.cache.get_stats()