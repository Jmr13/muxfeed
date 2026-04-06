from typing import Optional, List
from bs4 import BeautifulSoup
from src.fetchers.fetcher import URLFetcher

class PageParser:
    def __init__(self, fetcher: URLFetcher):
        self.fetcher = fetcher
        self.url: Optional[str] = None
        self.page_content: Optional[bytes] = None
        self.paragraphs: List[str] = []

    def _fetch(self) -> bool:
        if not self.url:
            return False

        result = self.fetcher.fetch(self.url)
        if not result or not result.ok:
            return False

        self.page_content = result.content
        return bool(self.page_content)

    def _parse(self) -> None:
        if not self.page_content:
            self.paragraphs = []
            return
    
        soup = BeautifulSoup(self.page_content, "html.parser")
    
        for tag in soup.select("script, style, nav, header, footer, aside, form, noscript"):
            tag.decompose()

        main_content = soup.find(["article", "main"]) or soup.body
        if not main_content:
            self.paragraphs = []
            return

        paragraphs = [p.get_text(strip=True) for p in main_content.find_all("p")]
        if not paragraphs:
            body_text = main_content.get_text(separator="\n", strip=True)
            paragraphs = [line for line in body_text.splitlines() if line.strip()]
    
        self.paragraphs = [p for p in paragraphs if len(p.split()) > 3]

    def get_content(self, url: str) -> str:
        self.url = url
        self.page_content = None
        self.paragraphs = []

        if not self._fetch():
            return "Failed to fetch page."

        self._parse()
        return "\n\n".join(self.paragraphs) if self.paragraphs else "No readable content found."