from datetime import timezone, timedelta
from pathlib import Path
from enum import Enum

FEED_URLS = [
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://www.fastcompany.com/technology/rss",
    "https://www.inquirer.net/fullfeed/",
    "https://news.mit.edu/rss/topic/artificial-intelligence2",
    "https://nesslabs.com/feed",
    "http://neurosciencenews.com/feed/",
    "https://www.sciencedaily.com/rss/top/technology.xml",
    "http://rss.slashdot.org/Slashdot/slashdotMain",
    "https://www.slashgear.com/category/technology/feed/",
    "https://techcrunch.com/feed/",
    "https://www.theguardian.com/us/technology/rss",
    "https://www.theverge.com/rss/tech/index.xml",
    "http://venturebeat.com/feed/",
    "https://news.ycombinator.com/rss"
]

NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'rss1': 'http://purl.org/rss/1.0/',
    'dc': 'http://purl.org/dc/elements/1.1/'
}

TZ_OFFSETS = {
    "PST": -8,
    "PDT": -7,
    "MST": -7,
    "MDT": -6,
    "CST": -6,
    "CDT": -5,
    "EST": -5,
    "EDT": -4,
    "GMT": 0,
    "UTC": 0,
    "CET": 1,
    "CEST": 2,
    "IST": 5.5,
    "JST": 9,
    "AEST": 10,
    "AEDT": 11
}

class CacheStrategy(Enum):
    MEMORY_ONLY = "memory_only"
    PERSISTENT = "persistent"
    HYBRID = "hybrid"