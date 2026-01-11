from bs4 import BeautifulSoup
import fetcher
from typing import Optional

def get_page_content(url: str) -> str:
    page_bytes: Optional[bytes] = fetcher.fetch_url(url)
    if not page_bytes:
        return "Failed to fetch or parse page."

    soup = BeautifulSoup(page_bytes, "html.parser")

    paragraphs = []
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text:
            paragraphs.append(text)

    if paragraphs:
        return "\n\n".join(paragraphs)

    return "No readable content found."
