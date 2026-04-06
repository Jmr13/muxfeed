from data import EXISTING_URL, NONEXISTING_URL
from src.parsers.page_parser import PageParser
from src.fetchers.fetcher import URLFetcher

def test_page_parse_success():
    parser = PageParser(URLFetcher())
    result = parser.get_content(EXISTING_URL)
    assert result != "Failed to fetch page."
    
def test_page_parse_failure():
    parser = PageParser(URLFetcher())
    result = parser.get_content(NONEXISTING_URL)
    assert result == "Failed to fetch page."