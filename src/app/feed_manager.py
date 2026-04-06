from datetime import datetime
from typing import List, Dict, Optional, Type
from src.parsers.feed_parser import FeedParser
from src.fetchers.fetcher import URLFetcher
from src.parsers.feed_parser import FeedParser, FeedItem

class FeedFetcher:
    def __init__(self, fetcher: URLFetcher):
        self.fetcher = fetcher

    def fetch(self, url: str) -> Optional[bytes]:
        try:
            result = self.fetcher.fetch(url)
            if result and result.ok and result.content:
                return result.content
        except Exception:
            pass
        return None

class FeedParser:
    def __init__(self, parser_class: Type[FeedParser] = FeedParser):
        self.parser_class = parser_class

    def parse(self, xml_bytes: bytes) -> List[FeedItem]:
        parser = self.parser_class(xml_bytes)
        return parser.parse()

class FeedSorter:
    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        if not date_str:
            return datetime.min
        try:
            return datetime.strptime(date_str, "%B %d, %Y | %I:%M %p")
        except Exception:
            return datetime.min

    def sort(self, items):
        return sorted(items, key=lambda x: x.parsed_date(), reverse=True)
    
class FeedManager:
    def __init__(
        self,
        urls: List[str],
        fetcher: FeedFetcher,
        parser: FeedParser,
        sorter: FeedSorter
    ):
        self.urls = urls
        self.fetcher = fetcher
        self.parser = parser
        self.sorter = sorter

    def get_entries(self) -> List[Dict]:
        all_items: List[FeedItem] = []

        for url in self.urls:
            xml = self.fetcher.fetch(url)
            if not xml:
                continue

            items = self.parser.parse(xml)
            all_items.extend(items)

        sorted_items = self.sorter.sort(all_items)

        return sorted_items