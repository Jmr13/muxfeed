from datetime import datetime

# fetcher.py
EXISTING_URL = "https://google.com"
NONEXISTING_URL = "http://this-domain-does-not-exist-123456789.com"

# parser.py
SOURCE = "RSS Feed"
TITLE = "Breaking News"
DATE = datetime(2026, 1, 12, 15, 30)
LINK = "https://example.com/news"

EXPECTED_DATE_TIME = "January 01, 2026 | 12:00 AM"
CASES = [
    ("2026-01-01T00:00:00Z", f"{EXPECTED_DATE_TIME}"),
    ("2026-01-01T00:00:00", f"{EXPECTED_DATE_TIME}"),
    ("2026-01-01T00:00:00+00:00", f"{EXPECTED_DATE_TIME}"),
    ("2026-01-01T00:00:00+08:00", f"{EXPECTED_DATE_TIME}"),
    ("2025-12-31T00:00:00-16:00", f"{EXPECTED_DATE_TIME}"),
    ("Thu, 01 Jan 2026 00:00:00", f"{EXPECTED_DATE_TIME}"),
    ("Thu, 01 Jan 2026 00:00:00 +0800", f"{EXPECTED_DATE_TIME}"),
    # This only works in my timezone
    # ("Wed, 31 Dec 2025 08:00:00 PST", f"{EXPECTED_DATE_TIME}"),
    (None, None),
    ("invalid date string", None)
]

ATOM_XML_FEEDS = [
    "https://rss.arxiv.org/atom/cs",
    "https://gist.githubusercontent.com/brucebolt/b91e348a928536dddd417829d2b4c0fd/raw/cop26.atom",
    "https://www.techstination.com/atom",
    "https://newpipe.net/blog/feeds/news.atom"
]
    
RSS1_XML_FEEDS = [
    "https://rss.slashdot.org/Slashdot/slashdotMain"
]

RSS2_XML_FEEDS = [
    "https://www.inquirer.net/fullfeed/",
    "https://www.engadget.com/rss.xml",
    "https://www.cnet.com/rss/news/"
]