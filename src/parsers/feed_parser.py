from typing import Optional, List, Dict
from datetime import datetime
import xml.etree.ElementTree as ET
from src.config import NS
from abc import ABC, abstractmethod
from typing import List, Optional
import xml.etree.ElementTree as ET

class FeedItem:
    def __init__(self, source: str, title: str, date: datetime, link: str):
        self.source = source
        self.title = title
        self.date = date
        self.link = link

class BaseFeedParser(ABC):
    def __init__(self, root: ET.Element):
        self.root = root

    @abstractmethod
    def parse(self) -> List[FeedItem]:
        raise NotImplementedError
    
    def _get_text(self, elem, *tags, default="") -> str:
        for tag in tags:
            text = elem.findtext(tag, default=None, namespaces=NS)
            if text and text.strip():
                return text.strip()
        return default

class AtomParser(BaseFeedParser):
    def _get_atom_link(self, entry) -> Optional[str]:
        for link in entry.findall("atom:link", NS):
            if link.get("rel") == "alternate" and link.get("href"):
                return link.get("href").strip()
        first = entry.find("atom:link", NS)
        href = first.get("href") if first is not None else None
        return href.strip() if href else None

    def parse(self) -> List[FeedItem]:
        items = []
        feed_title = self._get_text(self.root, "atom:title") or ""
        for entry in self.root.findall(".//atom:entry", NS):
            title = self._get_text(entry, "atom:title", default="No title")
            date = self._get_text(entry, "atom:published", "atom:updated")
            link = self._get_atom_link(entry)
            if link:
                items.append(FeedItem(feed_title, title, date, link))
        return items

class RSS1Parser(BaseFeedParser):
    def parse(self) -> List[FeedItem]:
        items = []
        feed_title = self._get_text(self.root, ".//rss1:title") or ""
        for item in self.root.findall(".//rss1:item", NS):
            title = self._get_text(item, "rss1:title", default="No title")
            date = self._get_text(item, "rss1:pubDate", "dc:date")
            link = self._get_text(item, "rss1:link")
            if link:
                items.append(FeedItem(feed_title, title, date, link))
        return items

class RSS2Parser(BaseFeedParser):
    def parse(self) -> List[FeedItem]:
        items = []
        feed_title = self._get_text(self.root, ".//channel/title") or ""
        for item in self.root.findall(".//item"):
            title = self._get_text(item, "title", default="No title")
            date = self._get_text(item, "pubDate", "dc:date")
            link = self._get_text(item, "link")
            if link:
                items.append(FeedItem(feed_title, title, date, link))
        return items

class FeedParser:
    def __init__(self, xml_bytes: Optional[bytes]):
        self.root = None
        self.parser: Optional[BaseFeedParser] = None

        if not xml_bytes:
            return

        try:
            self.root = ET.fromstring(xml_bytes)
            self.parser = self._get_feed_parser_strategy()
        except (ET.ParseError, ValueError):
            self.root = None
            self.parser = None

    def _get_feed_parser_strategy(self) -> BaseFeedParser:
        if self.root is None:
            raise ValueError("XML root is None")

        tag = self.root.tag.lower()

        # Atom
        if tag.endswith("feed"):
            return AtomParser(self.root)

        # RSS 2.0
        if tag == "rss" or tag.endswith("rss"):
            return RSS2Parser(self.root)

        # RSS 1.0 (RDF)
        if tag.endswith("rdf"):
            return RSS1Parser(self.root)

        raise ValueError(f"Unsupported feed format: {self.root.tag}")

    def parse(self) -> List[FeedItem]:
        if self.parser is None:
            return []

        return self.parser.parse()