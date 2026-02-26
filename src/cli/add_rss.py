#!/usr/bin/env python3
import sys
from urllib.parse import urlparse
from src.config import load_feed_urls, save_feed_urls

def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.cli.add <comma_separated_rss_urls>")
        return

    raw_input = " ".join(sys.argv[1:])
    urls_to_add = [url.strip() for url in raw_input.split(",") if url.strip()]

    if not urls_to_add:
        print("No URLs provided.")
        return

    existing_urls = load_feed_urls()
    added = []
    skipped = []
    invalid = []

    for url in urls_to_add:
        if not is_valid_url(url):
            invalid.append(url)
            continue

        if url in existing_urls:
            skipped.append(url)
        else:
            existing_urls.append(url)
            added.append(url)

    save_feed_urls(existing_urls)

    if added:
        print(f"Added: {', '.join(added)}")
    if skipped:
        print(f"Skipped (already existed): {', '.join(skipped)}")
    if invalid:
        print(f"Invalid URL format: {', '.join(invalid)}")

if __name__ == "__main__":
    main()