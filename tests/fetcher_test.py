import sys
from pathlib import Path
import pytest
import requests
from src.fetchers.fetcher import URLFetcher, FetchResult
from data import EXISTING_URL, NONEXISTING_URL

@pytest.fixture
def url_fetcher():
    return URLFetcher()
    
def test_fetch_existing_url(url_fetcher):
    result = url_fetcher.fetch(EXISTING_URL)

    assert isinstance(result, FetchResult)
    assert result.ok is True
    assert result.status_code == 200
    assert isinstance(result.content, bytes)
    assert result.error is None

def test_fetch_non_existing_url(url_fetcher):
    result = url_fetcher.fetch(NONEXISTING_URL)
    
    assert isinstance(result, FetchResult)
    assert result.ok is False
    assert result.status_code is not 200
    assert result.error is not None