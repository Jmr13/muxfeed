from ui import launch_ui
from parser import PageParser, FeedParser
from fetcher import URLFetcher
from datetime import datetime
from config import FEED_URLS

def main():
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

    launch_ui(all_entries)
    
if __name__ == "__main__":
    main()