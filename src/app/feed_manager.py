from datetime import datetime
from typing import List, Dict

from src.parsers.feed_parser import FeedParser
from src.fetchers.fetcher import URLFetcher

class FeedManager:
    def __init__(self, urls: List[str], fetcher: URLFetcher, parser_class=FeedParser):
        self.urls = urls
        self.fetcher = fetcher
        self.parser_class = parser_class

    def _fetch_feed(self, url: str):
        try:
            response = self.fetcher.fetch(url)
            if response and getattr(response, "content", None):
                return response.content
            print(f"Empty content from {url}")
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
        return None

    def _parse_feed(self, xml_bytes: bytes) -> List[Dict]:
        parser = self.parser_class(xml_bytes)
        return [item.to_dict() for item in parser.parse()]

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str, "%B %d, %Y | %I:%M %p")
        except Exception:
            return datetime.min
            
    def fetch_and_parse(self) -> List[Dict]:
        all_entries: List[Dict] = []

        for url in self.urls:
            result = self._fetch_feed(url)
            if not result:
                continue

            entries = self._parse_feed(result)
            all_entries.extend(entries)

        for entry in all_entries:
            entry["parsed_date"] = self._parse_date(entry.get("date"))

        all_entries.sort(key=lambda x: x["parsed_date"], reverse=True)
        return all_entries