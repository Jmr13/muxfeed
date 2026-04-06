from src.app.feed_manager import FeedFetcher, FeedManager, FeedParser, FeedSorter
from src.fetchers.fetcher import URLFetcher
from src.parsers.page_parser import PageParser
from src.tui.ui import UI
from src.tui.ui_component_factory import UIComponentFactory
from src.config import FEED_URLS

class FeedApp:
    def __init__(self):
        url_fetcher = URLFetcher()
        page_parser = PageParser(url_fetcher)
        factory = UIComponentFactory()

        fetcher = FeedFetcher(url_fetcher)
        parser = FeedParser()
        sorter = FeedSorter()

        self.feed_service = FeedManager(
            FEED_URLS,
            fetcher,
            parser,
            sorter
        )

        self.ui_factory = factory
        self.page_parser = page_parser
    
    def run(self):
        ui = UI(
            self.feed_service.get_entries(),
            self.ui_factory,
            self.page_parser
        )
        ui.launch()