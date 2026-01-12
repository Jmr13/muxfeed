from datetime import timezone, timedelta

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

TZ_MAP = {
    "EST": timezone(timedelta(hours=-5)),
    "EDT": timezone(timedelta(hours=-4)),
    "CST": timezone(timedelta(hours=-6)),
    "CDT": timezone(timedelta(hours=-5)),
    "MST": timezone(timedelta(hours=-7)),
    "MDT": timezone(timedelta(hours=-6)),
    "PST": timezone(timedelta(hours=-8)),
    "PDT": timezone(timedelta(hours=-7)),
}