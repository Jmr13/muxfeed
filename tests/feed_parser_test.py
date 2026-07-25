import pytest
import xml.etree.ElementTree as ET
from src.fetchers.fetcher import URLFetcher
from src.parsers.feed_parser import FeedItem, FeedParser
from data import SOURCE, TITLE, DATE, LINK, ATOM_XML_FEEDS, RSS1_XML_FEEDS, RSS2_XML_FEEDS

@pytest.fixture
def url_fetcher():
    return URLFetcher()

def test_feeditem_initialization():
    item = FeedItem(SOURCE, TITLE, DATE, LINK)

    assert item.source == SOURCE
    assert item.title == TITLE
    assert item.date == DATE
    assert item.link == LINK

@pytest.mark.parametrize("feed_url", ATOM_XML_FEEDS)
def test_parse_atom_feed(feed_url, url_fetcher):
    result = url_fetcher.fetch(feed_url)
    parser = FeedParser(result.content)
    items = parser.parse()
    
    for item in items:
        assert item.source is not None
        assert item.title is not None
        assert item.date is not None
        assert item.link is not None

@pytest.mark.parametrize("feed_url", RSS1_XML_FEEDS)
def test_parse_rss1_feed(feed_url, url_fetcher):
    result = url_fetcher.fetch(feed_url)
    parser = FeedParser(result.content)
    items = [item for item in parser.parse()]
    
    for item in items:
        assert item.source is not None
        assert item.title is not None
        assert item.date is not None
        assert item.link is not None

@pytest.mark.parametrize("feed_url", RSS2_XML_FEEDS)
def test_parse_rss2_feed(feed_url, url_fetcher):
    result = url_fetcher.fetch(feed_url)
    parser = FeedParser(result.content)
    items = [item for item in parser.parse()]
    
    for item in items:
        assert item.source is not None
        assert item.title is not None
        assert item.date is not None
        assert item.link is not None