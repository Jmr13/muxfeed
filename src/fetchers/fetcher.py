import ipaddress
import random
import socket
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Sequence, Union
from urllib.parse import urlparse

import requests
from dataclasses import dataclass
from datetime import datetime, timezone
from requests.adapters import HTTPAdapter, Retry

from src.fetchers.cache import Cache, CacheConfig, CachedResponse

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
    "Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.0; rv:121.0) "
    "Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) "
    "Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
    "AppleWebKit/605.1.15 Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) "
    "Gecko/20100101 Firefox/121.0",
]

@dataclass
class FetchResult:
    ok: bool
    content: Optional[bytes] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    from_cache: bool = False
    age: Optional[float] = None

def _validate_url(url: str) -> None:
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r}")

    hostname = parsed.hostname

    if not hostname:
        raise ValueError(f"Missing hostname in URL: {url!r}")

    _BLOCKED_HOSTS = {"localhost", "metadata.google.internal"}
    if hostname in _BLOCKED_HOSTS:
        raise ValueError(f"Blocked hostname: {hostname!r}")
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ValueError(f"Blocked private/reserved IP: {hostname!r}")
    except ValueError as e:
        if "Blocked private" in str(e):
            raise
        try:
            resolved = socket.getaddrinfo(hostname, None)
            for _, _, _, _, sockaddr in resolved:
                ip = ipaddress.ip_address(sockaddr[0])
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    raise ValueError(f"Hostname {hostname!r} resolves to blocked IP: {sockaddr[0]}")
        except socket.gaierror:
            pass

class URLFetcher:
    def __init__(
        self,
        timeout: float = 10.0,
        retries: int = 3,
        backoff_factor: float = 0.5,
        status_forcelist: Optional[Sequence[int]] = None,
        headers: Optional[Dict[str, str]] = None,
        cache_config: Optional[Union[CacheConfig, Dict]] = None,
        cache: Optional[Cache] = None,
        session: Optional[requests.Session] = None,
        max_redirects: int = 10,
    ):
        self.timeout = timeout
        self.status_forcelist = status_forcelist or [408, 429, 500, 502, 503, 504]
        self._custom_headers = headers is not None
        self.headers = headers or {
            "User-Agent": random.choice(_USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

        self.max_redirects = max_redirects

        if isinstance(cache_config, dict):
            cache_config = CacheConfig(**cache_config)

        self.cache_config = cache_config or CacheConfig()
        self.cache = cache or Cache(self.cache_config)

        if session is None:
            session = requests.Session()

        session.max_redirects = max_redirects
        retry_strategy = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            backoff_factor=backoff_factor,
            status_forcelist=self.status_forcelist,
            allowed_methods=frozenset({"GET"}),
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        self.session = session

    def fetch(self, url: str, force_refresh: bool = False,) -> FetchResult:
        try:
            _validate_url(url)
        except ValueError as e:
            return FetchResult(ok=False, error=str(e))

        stale = None

        if not force_refresh and self.cache_config.enabled:
            stale = self.cache.get(url, allow_stale=True)

        if stale and stale.is_fresh(self.cache_config.ttl):
            return FetchResult(
                ok=True,
                content=stale.content,
                status_code=stale.status_code,
                from_cache=True,
                age=stale.age.total_seconds(),
            )

        headers = self.headers.copy()
        if not self._custom_headers:
            headers["User-Agent"] = random.choice(_USER_AGENTS)

        if stale and self.cache_config.respect_headers:
            if stale.etag:
                headers["If-None-Match"] = stale.etag

            if stale.last_modified:
                headers["If-Modified-Since"] = stale.last_modified

        try:
            response = self.session.get(url, timeout=self.timeout, headers=headers, allow_redirects=True)

            if response.status_code == 304:
                if stale:
                    refreshed = CachedResponse(
                        content=stale.content,
                        status_code=stale.status_code,
                        headers=stale.headers,
                        cached_at=datetime.now(timezone.utc),
                        etag=stale.etag,
                        last_modified=stale.last_modified,
                    )
                    if self.cache_config.enabled:
                        self.cache.set(url, refreshed)
                    return FetchResult(
                        ok=True,
                        content=stale.content,
                        status_code=stale.status_code,
                        from_cache=True,
                        age=0.0,
                    )

                return FetchResult(
                    ok=False,
                    status_code=304,
                    error="304 without cached content",
                )

            response.raise_for_status()

            content = response.content

            new_cached = CachedResponse(
                content=content,
                status_code=response.status_code,
                headers=dict(response.headers),
                cached_at=datetime.now(timezone.utc),
                etag=response.headers.get("ETag"),
                last_modified=response.headers.get("Last-Modified"),
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
            if stale:
                return FetchResult(
                    ok=True,
                    content=stale.content,
                    status_code=stale.status_code,
                    from_cache=True,
                    age=stale.age.total_seconds(),
                )

            return FetchResult(
                ok=False,
                error="timeout",
            )

        except requests.HTTPError as e:
            status = e.response.status_code
            if stale and status >= 500:
                return FetchResult(
                    ok=True,
                    content=stale.content,
                    status_code=stale.status_code,
                    from_cache=True,
                    age=stale.age.total_seconds(),
                )

            return FetchResult(
                ok=False,
                status_code=status,
                error=f"HTTP {status}",
            )

        except requests.RequestException as e:
            if stale:
                return FetchResult(
                    ok=True,
                    content=stale.content,
                    status_code=stale.status_code,
                    from_cache=True,
                    age=stale.age.total_seconds(),
                )

            return FetchResult(
                ok=False,
                error=str(e),
            )

    def fetch_batch(self, urls: list, force_refresh: bool = False) -> Dict[str, FetchResult]:
        max_workers = min(8, len(urls)) if urls else 1
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.fetch, url, force_refresh): url for url in urls}
            return {futures[f]: f.result() for f in futures}

    def clear_cache(self):
        self.cache.clear()