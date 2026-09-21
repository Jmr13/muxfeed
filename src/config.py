from pathlib import Path
from enum import Enum
from typing import List
import json

FEEDS_FILE = Path(__file__).parent / "feeds.json"

def load_feed_urls() -> List[str]:
    if FEEDS_FILE.exists():
        try:
            with open(FEEDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_feed_urls(urls: List[str]) -> None:
    FEEDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDS_FILE, "w", encoding="utf-8") as f:
        json.dump(urls, f, indent=2)

FEED_URLS = load_feed_urls()

NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'rss1': 'http://purl.org/rss/1.0/',
    'dc': 'http://purl.org/dc/elements/1.1/'
}

