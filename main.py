import config
import fetcher
import parser
import ui
from itertools import chain
from typing import Iterable
from config import FEED_URLS
from datetime import datetime

def _safe_parse(url: str):
    xml = fetcher.fetch_url(url)
    return parser.parse_feed(xml) if xml else []

def _collect_entries(urls: Iterable[str]):
    return list(chain.from_iterable(map(_safe_parse, urls)))

def main():
    entries = _collect_entries(FEED_URLS)

    # Remove entries without valid date
    entries = [e for e in entries if e["date"]]

    # Sort by date descending (latest first)
    entries.sort(key=lambda x: x["date"], reverse=True)

    # Optionally format date for display
    for e in entries:
        e["date_str"] = e["date"].strftime("%b %d %Y %H:%M")

    if not entries:
        print("No news found in feeds.")
        return

    ui.launch_ui(entries)

if __name__ == "__main__":
    main()
