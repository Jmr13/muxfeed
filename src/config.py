from pathlib import Path
from enum import Enum
import json

FEEDS_FILE = Path(__file__).parent / "feeds.json"

def load_feed_urls() -> list[str]:
    if FEEDS_FILE.exists():
        try:
            with open(FEEDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_feed_urls(urls: list[str]) -> None:
    FEEDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDS_FILE, "w", encoding="utf-8") as f:
        json.dump(urls, f, indent=2)

FEED_URLS = load_feed_urls()

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