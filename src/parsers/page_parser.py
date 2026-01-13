from typing import Optional, List
from bs4 import BeautifulSoup
from src.fetchers.fetcher import URLFetcher

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