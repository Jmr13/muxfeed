import logging
from dataclasses import dataclass
from typing import Optional, Dict
import requests
from requests.adapters import HTTPAdapter, Retry
from collections.abc import Sequence

@dataclass
class FetchResult:
    ok: bool
    content: Optional[bytes] = None
    status_code: Optional[int] = None
    error: Optional[str] = None

class URLFetcher:
    def __init__(
        self,
        timeout: float = 10.0,
        retries: int = 3,
        backoff_factor: float = 0.5,
        status_forcelist: Optional[Sequence[int]] = None,
        headers: Optional[Dict[str, str]] = None,
        session: Optional[requests.Session] = None,
    ):
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.status_forcelist = status_forcelist or [408, 429, 500, 502, 503, 504]
        self.headers = headers or {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        self.session = self._create_session()

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

    def fetch(self, url: str) -> FetchResult:
        try:
            response = self.session.get(url, timeout=self.timeout, headers=self.headers)
            response.raise_for_status()
            return FetchResult(
                ok=True,
                content=response.content,
                status_code=response.status_code,
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