from src.tui.ui import FeedUI
from src.parsers.feed_parser import FeedParser
from src.fetchers.fetcher import URLFetcher
from datetime import datetime
from src.config import FEED_URLS

def run():
    url_fetcher = URLFetcher()
    all_entries = []

    for url in FEED_URLS:
        result = url_fetcher.fetch(url)
        parser = FeedParser(result.content)
        entries = [item.to_dict() for item in parser.parse()]
        all_entries.extend(entries)

    for entry in all_entries:
        entry['parsed_date'] = datetime.strptime(entry['date'], "%B %d, %Y | %I:%M %p")

    all_entries.sort(key=lambda x: x['parsed_date'], reverse=True)

    ui = FeedUI(all_entries)
    ui.launch()
    
if __name__ == "__main__":
    run()