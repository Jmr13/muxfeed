from datetime import datetime

# fetcher.py
EXISTING_URL = "https://google.com"
NONEXISTING_URL = "https://xyz.com"

# parser.py
SOURCE = "RSS Feed"
TITLE = "Breaking News"
DATE = datetime(2026, 1, 12, 15, 30)
LINK = "https://example.com/news"

BASE_DATE = "January 12, 2026"
CASES = [
    ("2026-01-12T15:30:00Z", f"{BASE_DATE} | 3:30 PM"),
    ("2026-01-12T15:30:00+02:00", f"{BASE_DATE} | 1:30 PM"),
    ("Mon, 12 Jan 2026 15:30:00 UTC", f"{BASE_DATE} | 3:30 PM"),
    ("Mon, 12 Jan 2026 15:30:00 +0200", f"{BASE_DATE} | 1:30 PM"),
    ("Mon, 12 Jan 2026 15:30:00", f"{BASE_DATE} | 3:30 PM"),
    ("2026-01-12T15:30:00", f"{BASE_DATE} | 7:30 AM"),
    ("Mon, 12 Jan 2026 17:30:33 EST", f"{BASE_DATE} | 10:30 PM"),
    (None, None),
    ("invalid date string", None),
]

ATOM_XML = "https://gist.githubusercontent.com/brucebolt/b91e348a928536dddd417829d2b4c0fd/raw/cop26.atom"
RSS1_XML = "https://rss.slashdot.org/Slashdot/slashdotMain"
RSS2_XML = "https://www.inquirer.net/fullfeed/"