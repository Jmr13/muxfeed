classDiagram

%% =======================
%% CLI MODULES
%% =======================

class AddRSSCLI {
    +main()
    +is_valid_url(url: str) bool
}

class ListRSSCLI {
    +main()
}

class RemoveRSSCLI {
    +main()
}

AddRSSCLI --> Config
ListRSSCLI --> Config
RemoveRSSCLI --> Config

%% =======================
%% CONFIG
%% =======================

class Config {
    +load_feed_urls() List[str]
    +save_feed_urls(urls: List[str]) void
    +FEED_URLS: List[str]
    +NS: Dict
    +TZ_OFFSETS: Dict
}

%% =======================
%% APP CORE
%% =======================

class FeedApp {
    -feed_service: FeedManager
    -ui_factory: UIComponentFactory
    -page_parser: PageParser
    +run()
}

FeedApp --> FeedManager
FeedApp --> URLFetcher
FeedApp --> PageParser
FeedApp --> UI
FeedApp --> UIComponentFactory

class FeedManager {
    -urls: List[str]
    -fetcher: FeedFetcher
    -parser: FeedParser
    -sorter: FeedSorter
    +get_entries() List[FeedItem]
}

FeedManager --> FeedFetcher
FeedManager --> FeedParser
FeedManager --> FeedSorter
FeedManager --> FeedItem

class FeedFetcher {
    -fetcher: URLFetcher
    +fetch(url: str) bytes
}

FeedFetcher --> URLFetcher

class FeedProcessor {
    -parser_class: FeedParser
    +parse(xml_bytes: bytes) List[FeedItem]
}

FeedProcessor --> FeedParser

class FeedSorter {
    +sort(items) List
}

FeedSorter --> FeedItem

%% =======================
%% FETCHING + CACHE
%% =======================

class URLFetcher {
    -session: Session
    -cache: Cache
    +fetch(url: str) FetchResult
    +fetch_batch(urls: list) Dict
}

URLFetcher --> Cache
URLFetcher --> CachedResponse
URLFetcher --> FetchResult

class Cache {
    -_memory_cache: Dict
    +get(url: str) CachedResponse
    +set(url: str, response: CachedResponse)
    +delete(url: str)
    +clear()
}

Cache --> CachedResponse
Cache --> CacheConfig

class CacheConfig {
    +enabled: bool
    +ttl: timedelta
    +persistent: bool
}

class CachedResponse {
    +content: bytes
    +status_code: int
    +headers: Dict
    +cached_at: datetime
    +is_fresh(ttl) bool
}

class FetchResult {
    +ok: bool
    +content: bytes
    +status_code: int
    +error: str
}

%% =======================
%% PARSERS
%% =======================

class FeedParser {
    -root: Element
    +parse() List[FeedItem]
}

FeedParser --> AtomParser
FeedParser --> RSS1Parser
FeedParser --> RSS2Parser
FeedParser --> FeedItem

class BaseFeedParser {
    <<abstract>>
    -root: Element
    +parse() List[FeedItem]
}

BaseFeedParser <|-- AtomParser
BaseFeedParser <|-- RSS1Parser
BaseFeedParser <|-- RSS2Parser

class DateParser {
    +parse(date_str: str) str
}

BaseFeedParser --> DateParser

class FeedItem {
    +source: str
    +title: str
    +date: datetime
    +link: str
}

class PageParser {
    -fetcher: URLFetcher
    +get_content(url: str) str
}

PageParser --> URLFetcher

%% =======================
%% TUI LAYER
%% =======================

class UI {
    -model: UIModel
    -renderer: UIRenderer
    -controller: UIController
    +launch()
}

UI --> UIModel
UI --> UIRenderer
UI --> UIController

class UIModel {
    -entries: List
    -selected: int
    +move_up()
    +move_down()
    +get_selected_entry()
}

class UIRenderer {
    -factory: UIComponentFactory
    -page_parser: PageParser
    +draw()
    +draw_details()
}

UIRenderer --> UIComponentFactory
UIRenderer --> PageParser
UIRenderer --> EntryDetails

class UIController {
    -model: UIModel
    -renderer: UIRenderer
    +run()
}

UIController --> UIModel
UIController --> UIRenderer

class UIComponentFactory {
    +create_component(type, kwargs) UIComponent
}

UIComponentFactory --> UIComponent

class UIComponent {
    <<abstract>>
    +draw()
}

UIComponent <|-- TitleBar
UIComponent <|-- EntryList
UIComponent <|-- EntryDetails

class TitleBar {
    +text: str
}

class EntryList {
    +entries: List
    +selected: int
    +draw()
}

class EntryDetails {
    +entry
    +page_parser: PageParser
    +draw()
}

EntryDetails --> PageParser
EntryDetails --> FeedItem

%% =======================
%% COMMAND PATTERN
%% =======================

class Command {
    <<abstract>>
    +execute(controller, stdscr)
}

Command <|-- MoveUpCommand
Command <|-- MoveDownCommand
Command <|-- ScrollLeftCommand
Command <|-- ScrollRightCommand
Command <|-- ShowDetailsCommand
Command <|-- QuitCommand
Command <|-- ScrollDownCommand
Command <|-- ScrollUpCommand
Command <|-- QuitDetailsCommand

UIController --> Command