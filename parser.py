import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional
from config import NS

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date strings from RSS/Atom feeds and return a UTC datetime object."""
    if not date_str:
        return None

    dt = None

    # 1️⃣ ISO 8601 (Atom)
    try:
        if date_str.endswith("Z"):
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(date_str)
    except ValueError:
        pass

    # 2️⃣ RFC 2822 / RSS2 with timezone name (e.g., "GMT")
    if dt is None:
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
            dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    # 3️⃣ RFC 2822 / RSS2 with numeric offset (e.g., "+0000")
    if dt is None:
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            pass

    # 4️⃣ Fallback without timezone
    if dt is None:
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S")
            dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    # Normalize to UTC and return as datetime
    return dt.astimezone(timezone.utc)
    
# -----------------------
# XML helpers
# -----------------------
def _get_text(elem, *tags, default=""):
    for tag in tags:
        text = elem.findtext(tag, default=None, namespaces=NS)
        if text and text.strip():
            return text.strip()
    return default

def _get_atom_link(entry):
    for link in entry.findall("atom:link", NS):
        if link.get("rel") == "alternate" and link.get("href"):
            return link.get("href").strip()
    first = entry.find("atom:link", NS)
    return first.get("href").strip() if first is not None else None

# -----------------------
# Feed parsers
# -----------------------
def _parse_atom(root):
    items = []
    feed_title = _get_text(root, "atom:title") or ""
    for entry in root.findall(".//atom:entry", NS):
        title = _get_text(entry, "atom:title", default="No title")
        date = parse_date(_get_text(entry, "atom:published", "atom:updated"))
        link = _get_atom_link(entry)
        if link:
            items.append({"source": feed_title, "title": title, "date": date, "link": link})
    return items

def _parse_rss1(root):
    items = []
    feed_title = _get_text(root, ".//rss1:title") or ""
    for item in root.findall(".//rss1:item", NS):
        title = _get_text(item, "rss1:title", default="No title")
        date = parse_date(_get_text(item, "rss1:pubDate", "dc:date"))
        link = _get_text(item, "rss1:link")
        if link:
            items.append({"source": feed_title, "title": title, "date": date, "link": link})
    return items

def _parse_rss2(root):
    items = []
    feed_title = _get_text(root, ".//channel/title") or ""
    for item in root.findall(".//item"):
        title = _get_text(item, "title", default="No title")
        date = parse_date(_get_text(item, "pubDate", "dc:date"))
        link = _get_text(item, "link")
        if link:
            items.append({
                "source": feed_title,
                "title": title,
                "date": date,
                "link": link,
            })
    return items

# -----------------------
# Public API
# -----------------------
def parse_feed(xml_bytes: bytes):
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []
    return _parse_atom(root) + _parse_rss1(root) + _parse_rss2(root)