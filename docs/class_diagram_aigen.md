classDiagram

%% ==========================
%% Configuration
%% ==========================

class config {
    <<module>>
    +FEEDS_FILE: Path
    +FEED_URLS: List[str]
    +NS: Dict
    +TZ_OFFSETS: Dict

    +load_feed_urls() List[str]
    +save_feed_urls(urls: List[str]) None
}


%% ==========================
%% Fetching
%% ==========================

class URLFetcher {
    -timeout: float
    -retries: int
    -backoff_factor: float
    -status_forcelist: Sequence[int]
    -headers: Dict[str,str]
    -cache_config: CacheConfig
    -cache: Cache
    -session: requests.Session

    +fetch(url: str, force_refresh: bool=False) FetchResult
    +fetch_batch(urls: list, force_refresh: bool=False) Dict
    +clear_cache() None

    -_default_headers() Dict
    -_create_session() Session
    -_prepare_headers(cached) Dict
}


class FetchResult {
    +ok: bool
    +content: bytes
    +status_code: int
    +error: str
    +from_cache: bool
    +age: float
}


class Cache {
    -config: CacheConfig
    -_memory_cache: Dict[str,CachedResponse]

    +get(url: str, allow_stale: bool=False) CachedResponse
    +set(url: str, response: CachedResponse) None
    +delete(url: str) None
    +clear() None

    -_ensure_cache_dir() None
    -_get_cache_key(url: str) str
    -_get_persistent_path(key: str) Path
    -_save_persistent(key,response) None
    -_load_persistent(key) CachedResponse
    -_evict_if_needed() None
}


class CacheConfig {
    +enabled: bool
    +ttl: timedelta
    +max_memory_items: int
    +persistent: bool
    +cache_dir: Path
    +respect_headers: bool
    +stale_while_revalidate: bool
}


class CachedResponse {
    +content: bytes
    +status_code: int
    +headers: Dict
    +cached_at: datetime
    +etag: str
    +last_modified: str

    +age() timedelta
    +is_fresh(ttl) bool
    +to_dict() Dict
    +from_dict(data) CachedResponse
}


%% ==========================
%% Feed Parsing
%% ==========================

class FeedItem {
    +source: str
    +title: str
    +date: datetime
    +link: str
}


class FeedParser {
    -root: Element
    -parser: BaseFeedParser

    +parse() List[FeedItem]

    -_get_feed_parser_strategy() BaseFeedParser
}


class BaseFeedParser {
    #root: Element

    +parse() List[FeedItem]

    #_get_text(elem,tags,default) str
}


class AtomParser {
    +parse() List[FeedItem]

    -_get_atom_link(entry) str
}


class RSS1Parser {
    +parse() List[FeedItem]
}


class RSS2Parser {
    +parse() List[FeedItem]
}


BaseFeedParser <|-- AtomParser
BaseFeedParser <|-- RSS1Parser
BaseFeedParser <|-- RSS2Parser

FeedParser --> BaseFeedParser
FeedParser --> FeedItem


%% ==========================
%% Feed Application
%% ==========================

class FeedApp {
    -feed_service: FeedManager
    -ui_factory: UIComponentFactory
    -page_parser: PageParser

    +run() None
}


class FeedManager {
    -urls: List[str]
    -fetcher: FeedFetcher
    -parser: FeedProcessor
    -sorter: FeedSorter

    +get_entries() List[Dict]
}


class FeedFetcher {
    -fetcher: URLFetcher

    +fetch(url:str) bytes
}


class FeedProcessor {
    -parser_class: FeedParser

    +parse(xml_bytes:bytes) List[FeedItem]
}


class FeedSorter {
    +sort(items) List[FeedItem]

    -_parse_date(date_str:str) datetime
}


FeedApp --> FeedManager
FeedManager --> FeedFetcher
FeedManager --> FeedProcessor
FeedManager --> FeedSorter

FeedFetcher --> URLFetcher
FeedProcessor --> FeedParser


%% ==========================
%% Page Parsing
%% ==========================

class PageParser {
    -fetcher: URLFetcher
    -url: str
    -page_content: bytes
    -paragraphs: List[str]

    +get_content(url:str) str

    -_fetch() bool
    -_parse() None
}


PageParser --> URLFetcher


%% ==========================
%% TUI MVC
%% ==========================

class UI {
    -model: UIModel
    -renderer: UIRenderer
    -controller: UIController

    +launch() None
}


class UIModel {
    -_entries: List
    -_selected: int
    -_start_index: int
    -_scroll_x: int

    +entries()
    +selected()
    +start_index()
    +scroll_x()

    +move_down(visible_count:int)
    +move_up()
    +scroll_title_left()
    +scroll_title_right(max_width:int)
    +get_selected_entry()
    +reset_selection()
}


class UIController {
    -model: UIModel
    -renderer: UIRenderer
    -title_text: str
    -running: bool
    -view_mode: str
    -list_commands: Dict
    -details_commands: Dict

    +run(stdscr)

    -_init_commands()
}


class UIRenderer {
    -factory: UIComponentFactory
    -page_parser: PageParser
    -current_details: EntryDetails

    +draw(stdscr,model,title_text)
    +draw_details(stdscr,entry)
}


class UIComponentFactory {
    +create_component(component_type,**kwargs) UIComponent
}


class UIComponent {
    +draw(stdscr)
}


class TitleBar {
    -text: str

    +draw(stdscr)
}


class EntryList {
    -entries: List
    -selected: int
    -start_index: int
    -scroll_x: int

    +draw(stdscr)
}


class EntryDetails {
    -entry: FeedItem
    -page_parser: PageParser
    -raw_lines: List[str]
    -lines: List[str]
    -start_line: int

    +draw(stdscr,height,width)

    -_load_content()
    -_format_header(width)
    -_wrap_content(width)
}


UIComponent <|-- TitleBar
UIComponent <|-- EntryList

UI --> UIModel
UI --> UIController
UI --> UIRenderer

UIRenderer --> UIComponentFactory
UIRenderer --> EntryDetails

EntryDetails --> PageParser