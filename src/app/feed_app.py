from typing import Dict, List
from src.tui.ui import UI
from src.tui.ui_component_factory import UIComponentFactory
from src.app.feed_manager import FeedManager
from src.fetchers.fetcher import URLFetcher
from src.config import FEED_URLS
from src.app.feed_manager import FeedManager

class FeedApp:
    def __init__(self):
        self.feed_manager = FeedManager(FEED_URLS, URLFetcher())
        self.ui_factory = UIComponentFactory()
    
    def _getEntries(self) -> List[Dict]:
        entries = self.feed_manager.fetch_and_parse()
        return entries
        
    def run(self):
        factory = UIComponentFactory()

        ui = UI(self._getEntries(), self.ui_factory)
        ui.launch()