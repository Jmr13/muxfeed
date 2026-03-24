from src.tui.ui import UI
from src.tui.ui_component_factory import UIComponentFactory
from src.app.feed_manager import FeedManager, FeedFetcher, FeedParser, FeedSorter
from src.config import FEED_URLS

class FeedApp:
    def __init__(self):
        fetcher = FeedFetcher()
        parser = FeedParser()
        sorter = FeedSorter()

        self.feed_service = FeedManager(
            FEED_URLS,
            fetcher,
            parser,
            sorter
        )
        self.ui_factory = UIComponentFactory()
    
    def _get_entries(self):
        return self.feed_service.get_entries()
        
    def run(self):
        ui = UI(self._get_entries(), self.ui_factory)
        ui.launch()