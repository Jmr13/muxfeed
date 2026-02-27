#!/usr/bin/env python3
from src.config import load_feed_urls

def main():
    urls = load_feed_urls()
    if not urls:
        print("No RSS feeds configured.")
    for u in urls:
        print(u)

if __name__ == "__main__":
    main()