import urllib.request
import urllib.error
from typing import Optional
from config import HEADERS

def fetch_url(url: str, *, timeout: float = 10) -> Optional[bytes]:
    request = urllib.request.Request(url, headers=HEADERS, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except (urllib.error.URLError, urllib.error.HTTPError):
        return None