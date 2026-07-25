from datetime import datetime

# fetcher.py
EXISTING_URL = "https://google.com"
NONEXISTING_URL = "http://this-domain-does-not-exist-123456789.com"

# parser.py
SOURCE = "RSS Feed"
TITLE = "Breaking News"
DATE = datetime(2026, 1, 12, 15, 30)
LINK = "https://example.com/news"

ATOM_XML_FEEDS = [
    "https://rss.arxiv.org/atom/cs",
    "https://gist.githubusercontent.com/brucebolt/b91e348a928536dddd417829d2b4c0fd/raw/cop26.atom",
    "https://www.techstination.com/atom",
    "https://newpipe.net/blog/feeds/news.atom"
]
    
RSS1_XML_FEEDS = [
    "https://rss.slashdot.org/Slashdot/slashdotMain",
    "https://www.inquirer.net/fullfeed/",
    "https://news.mit.edu/rss/topic/artificial-intelligence2",
    "https://nesslabs.com/feed",
    "http://neurosciencenews.com/feed/",
    "https://www.sciencedaily.com/rss/top/technology.xml",
    "http://rss.slashdot.org/Slashdot/slashdotMain"
]

RSS2_XML_FEEDS = [
    "https://www.inquirer.net/fullfeed/",
    "https://www.engadget.com/rss.xml",
    "https://www.cnet.com/rss/news/"
]