import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from src.fetchers.cache import (
    Cache,
    CacheConfig,
    CachedResponse,
)

def make_response(content=b"test"):
    return CachedResponse(
        content = content,
        status_code = 200,
        headers = {},
        cached_at = datetime.now()
    )
    
def test_cache_set_and_get_returns_response():
    cache = Cache(CacheConfig())

    response = make_response(content=b"hello-cache")

    url = "https://example.com/feed"
    cache.set(url, response)

    result = cache.get(url, allow_stale=False)

    assert result is not None
    assert result.content == b"hello-cache"
    assert result.status_code == 200

def test_cache_returns_none_for_missing_cache():
    cache = Cache(CacheConfig())
    url = "https://missing.com"

    result = cache.get(url, allow_stale=True)

    assert result is None
    
def test_cache_returns_existing_cache():
    cache = Cache(CacheConfig())
    url = "https://example.com/feed"
    
    result = cache.get(url, allow_stale=True)

    assert result is not None
    
def test_cache_evicts_oldest_entries_from_memory():
    cache = Cache(
        CacheConfig(
            max_memory_items=5,
        )
    )

    for i in range(6):
        cache.set(
            f"https://example.com/{i}",
            make_response(content=b"test")
        )
        time.sleep(0.5)

    oldest_cache_url = "https://example.com/0"
    oldest_cache_key = hashlib.sha256(oldest_cache_url.encode()).hexdigest()

    assert len(cache._memory_cache) == 5
    assert oldest_cache_key not in cache._memory_cache