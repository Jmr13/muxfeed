from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from config import NS, TZ_MAP
from fetcher import URLFetcher

class DateParser:
    @staticmethod
    def parse(date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None
        dt = None

        if dt is None:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                pass
            
        if dt is None:
            try:
                dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
                dt = dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        if dt is None:
            try:
                dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                pass
            
        if dt is None:
            try:
                dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                try:
                    dt_part, tz_abbr = date_str.rsplit(" ", 1)
                    dt = datetime.strptime(dt_part, "%a, %d %b %Y %H:%M:%S")
                    if tz_abbr in TZ_MAP:
                        dt = dt.replace(tzinfo=tz_map[tz_abbr])
                except Exception:
                    pass

        if dt is None:
            try:
                dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S")
                dt = dt.replace(tzinfo=timezone.utc)
            except ValueError:
                return None

        dt_utc = dt.astimezone(timezone.utc)
        formatted = dt_utc.strftime("%B %-d, %Y | %-I:%M %p")
        
        return formatted

class FeedItem:
    def __init__(self, source: str, title: str, date: Optional[datetime], link: str):
        self.source = source
        self.title = title
        self.date = date
        self.link = link

    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "title": self.title,
            "date": self.date,
            "link": self.link,
        }
        
class FeedParser:
    def __init__(self, xml_bytes: bytes):
        if not xml_bytes:
            self.root: Optional[ET.Element] = None
            return
        try:
            self.root = ET.fromstring(xml_bytes)
        except ET.ParseError:
            self.root = None

    def parse(self) -> List[FeedItem]:
        if self.root is None:
            return []
        return self._parse_atom() + self._parse_rss1() + self._parse_rss2()

    def _get_text(self, elem, *tags, default="") -> str:
        for tag in tags:
            text = elem.findtext(tag, default=None, namespaces=NS)
            if text and text.strip():
                return text.strip()
        return default

    def _get_atom_link(self, entry) -> Optional[str]:
        for link in entry.findall("atom:link", NS):
            if link.get("rel") == "alternate" and link.get("href"):
                return link.get("href").strip()
        first = entry.find("atom:link", NS)
        return first.get("href").strip() if first is not None else None

    def _parse_atom(self) -> List[FeedItem]:
        items = []
        feed_title = self._get_text(self.root, "atom:title") or ""
        for entry in self.root.findall(".//atom:entry", NS):
            title = self._get_text(entry, "atom:title", default="No title")
            date = DateParser.parse(self._get_text(entry, "atom:published", "atom:updated"))
            link = self._get_atom_link(entry)
            if link:
                items.append(FeedItem(feed_title, title, date, link))
        return items

    def _parse_rss1(self) -> List[FeedItem]:
        items = []
        feed_title = self._get_text(self.root, ".//rss1:title") or ""
        for item in self.root.findall(".//rss1:item", NS):
            title = self._get_text(item, "rss1:title", default="No title")
            date = DateParser.parse(self._get_text(item, "rss1:pubDate", "dc:date"))
            link = self._get_text(item, "rss1:link")
            if link:
                items.append(FeedItem(feed_title, title, date, link))
        return items

    def _parse_rss2(self) -> List[FeedItem]:
        items = []
        feed_title = self._get_text(self.root, ".//channel/title") or ""
        for item in self.root.findall(".//item"):
            title = self._get_text(item, "title", default="No title")
            date = DateParser.parse(self._get_text(item, "pubDate", "dc:date"))
            link = self._get_text(item, "link")
            if link:
                items.append(FeedItem(feed_title, title, date, link))
        return items

class PageParser:
    def __init__(self, url: Optional[str] = None):
        self.url: Optional[str] = url
        self.page_content: Optional[bytes] = None
        self.paragraphs: List[str] = []

    def _fetch(self) -> bool:
        if not self.url:
            return False
        self.page_content = URLFetcher().fetch(self.url).content
        return bool(self.page_content)

    def _parse(self) -> None:
        if not self.page_content:
            self.paragraphs = []
            return

        soup = BeautifulSoup(self.page_content, "html.parser")
        body_text = soup.body.get_text(separator="\n", strip=True) if soup.body else ""
        self.paragraphs = [line for line in body_text.splitlines() if line]

    def get_content(self, url: str) -> str:
        self.url = url
        self.page_content = None
        self.paragraphs = []

        if not self._fetch():
            return "Failed to fetch page."

        self._parse()
        return "\n\n".join(self.paragraphs) if self.paragraphs else "No readable content found."