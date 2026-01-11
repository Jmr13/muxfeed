import requests
from typing import Optional
from config import HEADERS

def fetch_url(url: str, *, timeout: float = 10) -> Optional[bytes]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.content
    except (requests.RequestException, requests.Timeout):
        return None