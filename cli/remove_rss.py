#!/usr/bin/env python3
import sys
from src.config import load_feed_urls, save_feed_urls

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m cli.remove <comma_separated_rss_urls>")
        return

    raw_input = " ".join(sys.argv[1:])
    urls_to_remove = [url.strip() for url in raw_input.split(",") if url.strip()]

    if not urls_to_remove:
        print("No URLs provided.")
        return

    existing_urls = load_feed_urls()
    removed, skipped = [], []

    for url in urls_to_remove:
        if url in existing_urls:
            existing_urls.remove(url)
            removed.append(url)
        else:
            skipped.append(url)

    save_feed_urls(existing_urls)

    if removed:
        print(f"Removed: {', '.join(removed)}")
    if skipped:
        print(f"Skipped (not found): {', '.join(skipped)}")

if __name__ == "__main__":
    main()