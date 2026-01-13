import pytest
from fetchers.fetcher import URLFetcher
from parsers.feed_parser import FeedItem, FeedParser
from data import SOURCE, TITLE, DATE, LINK, ATOM_XML, RSS1_XML, RSS2_XML

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
    
def test_parse_atom_feed(url_fetcher):
    result = url_fetcher.fetch(ATOM_XML)
    parser = FeedParser(result.content)
    items = [item.to_dict() for item in parser.parse()]
    
    for item in items:
        assert item.get('source') is not None
        assert item.get('title') is not None
        assert item.get('date') is not None
        assert item.get('link') is not None

def test_parse_rss1_feed(url_fetcher):
    result = url_fetcher.fetch(RSS1_XML)
    parser = FeedParser(result.content)
    items = [item.to_dict() for item in parser.parse()]
    
    for item in items:
        assert item.get('source') is not None
        assert item.get('title') is not None
        assert item.get('date') is not None
        assert item.get('link') is not None
        
def test_parse_rss2_feed(url_fetcher):
    result = url_fetcher.fetch(RSS2_XML)
    parser = FeedParser(result.content)
    items = [item.to_dict() for item in parser.parse()]
    
    for item in items:
        assert item.get('source') is not None
        assert item.get('title') is not None
        assert item.get('date') is not None
        assert item.get('link') is not None