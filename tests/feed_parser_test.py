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

def test_feeditem_to_dict():
    item = FeedItem(SOURCE, TITLE, DATE, LINK)
    
    expected_dict = {
        "source": SOURCE,
        "title": TITLE,
        "date": DATE,
        "link": LINK
    }

    assert item.to_dict() == expected_dict

@pytest.mark.parametrize("feed_url", ATOM_XML_FEEDS)
def test_parse_atom_feed(feed_url, url_fetcher):
    result = url_fetcher.fetch(feed_url)
    root = ET.fromstring(result.content)
    parser = FeedParser(result.content)
    items = [item.to_dict() for item in parser.parse()]
    
    for item in items:
        assert item.get('source') is not None, "Missing source in feed item"
        assert item.get('title') is not None, "Missing title in feed item"
        assert item.get('date') is not None, "Missing date in feed item"
        assert item.get('link') is not None, "Missing link in feed item"

@pytest.mark.parametrize("feed_url", RSS1_XML_FEEDS)
def test_parse_rss1_feed(feed_url, url_fetcher):
    result = url_fetcher.fetch(feed_url)
    root = ET.fromstring(result.content)
    parser = FeedParser(result.content)
    items = [item.to_dict() for item in parser.parse()]
    
    for item in items:
        assert item.get('source') is not None
        assert item.get('title') is not None
        assert item.get('date') is not None
        assert item.get('link') is not None

@pytest.mark.parametrize("feed_url", RSS2_XML_FEEDS)
def test_parse_rss2_feed(feed_url, url_fetcher):
    result = url_fetcher.fetch(feed_url)
    root = ET.fromstring(result.content)
    parser = FeedParser(result.content)
    items = [item.to_dict() for item in parser.parse()]
    
    for item in items:
        assert item.get('source') is not None
        assert item.get('title') is not None
        assert item.get('date') is not None
        assert item.get('link') is not None