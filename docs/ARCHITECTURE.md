# muxfeed — Architecture

This document visualizes the current muxfeed architecture. All diagrams are
[Mermaid](https://mermaid.js.org/) and render on GitHub.

Four layers:

1. **Fetchers** — `URLFetcher` (retry/backoff, conditional GET) backed by a two-tier `Cache` (memory + JSON on disk)
2. **Parsers** — `FeedParser` dispatching to Atom / RSS1 / RSS2 parsers, a strategy-based `DateParser`, and a `PageParser` (BeautifulSoup article extraction)
3. **Application** — `FeedFetcher → FeedProcessor → FeedSorter → FeedManager`
4. **TUI** — curses MVC: `UIModel` (state), `UIRenderer` + components (view), `UIController` + commands (Command pattern), `UIComponentFactory` (Factory)

---

## 1. System Overview

```mermaid
flowchart TB
    subgraph Tools["CLI"]
        Add["cli.add_rss"]
        Remove["cli.remove_rss"]
        List["cli.list_rss"]
    end

    Feeds[("src/feeds.json")]
    CacheDisk[("~/.cache/muxfeed/*.cache")]
    Net[("Internet feeds / articles")]

    Tools <--> Feeds

    Main["src/main.py"] --> App["FeedApp (composition root)"]
    App --> Mgr["FeedManager"]
    Mgr --> Fetch["URLFetcher + Cache"]
    Mgr --> Parse["FeedProcessor → FeedParser (Atom/RSS1/RSS2) + DateParser"]
    Mgr --> Sort["FeedSorter"]

    Fetch <--> Net
    Fetch <--> CacheDisk

    Parse --> Items["FeedItem list (sorted, newest first)"]
    Sort --> Items

    App --> TUI["TUI — UI / UIModel / UIRenderer / UIController"]
    TUI --> PageParser["PageParser (article text extraction)"]
    PageParser --> Net
    Items --> TUI
```

Notes on the current wiring:

- `FEED_URLS` is read from `src/feeds.json` **once at import** in `src/config.py` — CLI changes only take effect after a restart.
- `src/feeds.json` is gitignored (user-local subscription list).
- Overall the app touches the network only for subscribed feeds and opened articles — no telemetry, no accounts.

---

## 2. Class Diagram

```mermaid
classDiagram
    direction LR

    class FeedApp {
        +run()
    }
    class FeedManager {
        +get_entries()
    }
    class FeedFetcher {
        +fetch(url)
    }
    class FeedProcessor {
        +parse(xml_bytes)
    }
    class FeedSorter {
        +sort(items)
    }
    class URLFetcher {
        +fetch(url, force_refresh)
        +fetch_batch(urls)
        +clear_cache()
    }
    class FetchResult {
        +ok
        +content
        +status_code
        +error
        +from_cache
    }
    class Cache {
        +get(url, allow_stale)
        +set(url, response)
        +delete(url)
        +clear()
    }
    class CacheConfig {
        +enabled
        +ttl
        +max_memory_items
        +persistent
        +cache_dir
    }
    class CachedResponse {
        +age
        +is_fresh(ttl)
    }

    class FeedParser {
        +parse()
    }
    class BaseFeedParser {
        <<abstract>>
    }
    class AtomParser
    class RSS1Parser
    class RSS2Parser
    class FeedItem {
        +source
        +title
        +date
        +link
        +to_dict()
    }
    class DateParser {
        +parse(date_str)
    }
    class DateParseStrategy {
        <<abstract>>
    }
    class ISOFormatStrategy
    class ISOFormatTzStrategy
    class RFCFormatStrategy
    class RFCFormatTz1Strategy
    class RFCFormatTz2Strategy

    class PageParser {
        +get_content(url)
    }

    class UI {
        +launch()
    }
    class UIModel {
        +move_up()
        +move_down(visible_count)
        +scroll_title_left()
        +scroll_title_right(max_width)
        +get_selected_entry()
    }
    class UIRenderer {
        +draw(stdscr, model, title)
        +draw_details(stdscr, entry)
    }
    class UIController {
        +run(stdscr)
    }
    class Command {
        <<abstract>>
        +execute(controller, stdscr)
    }
    class MoveUpCommand
    class MoveDownCommand
    class ShowDetailsCommand
    class QuitCommand
    class QuitDetailsCommand
    class ScrollUpCommand
    class ScrollDownCommand
    class ScrollLeftCommand
    class ScrollRightCommand
    class UIComponentFactory {
        +create_component(component_type, kwargs)
    }
    class TitleBar
    class EntryList
    class EntryDetails

    FeedApp --> FeedManager
    FeedApp --> PageParser
    FeedApp --> UIComponentFactory

    FeedManager --> FeedFetcher
    FeedManager --> FeedProcessor
    FeedManager --> FeedSorter
    FeedFetcher --> URLFetcher

    URLFetcher --> FetchResult
    URLFetcher --> Cache
    Cache --> CacheConfig
    Cache o-- CachedResponse

    FeedProcessor --> FeedParser
    FeedParser --> BaseFeedParser
    FeedParser --> DateParser
    DateParser --> DateParseStrategy
    DateParseStrategy <|-- ISOFormatStrategy
    DateParseStrategy <|-- ISOFormatTzStrategy
    DateParseStrategy <|-- RFCFormatStrategy
    DateParseStrategy <|-- RFCFormatTz1Strategy
    DateParseStrategy <|-- RFCFormatTz2Strategy
    BaseFeedParser <|-- AtomParser
    BaseFeedParser <|-- RSS1Parser
    BaseFeedParser <|-- RSS2Parser
    BaseFeedParser --> FeedItem

    UI --> UIModel
    UI --> UIRenderer
    UI --> UIController
    UIModel --> FeedItem
    UIController --> Command
    Command <|-- MoveUpCommand
    Command <|-- MoveDownCommand
    Command <|-- ShowDetailsCommand
    Command <|-- QuitCommand
    Command <|-- QuitDetailsCommand
    Command <|-- ScrollUpCommand
    Command <|-- ScrollDownCommand
    Command <|-- ScrollLeftCommand
    Command <|-- ScrollRightCommand
    UIRenderer --> UIComponentFactory
    UIComponentFactory --> TitleBar
    UIComponentFactory --> EntryList
    UIComponentFactory --> EntryDetails
    EntryDetails --> PageParser
    EntryDetails --> FeedItem
```

Known annotation mismatches that are intentional in the code today (see
`docs/feature_status.md` and `docs/arch_decision_records.md`):

- `FeedManager.parser` is annotated `FeedParser` but receives a `FeedProcessor` (works by duck typing — issue **A2**).
- `FeedItem.date` is annotated `Optional[datetime]` but holds a display string (see **ADR-001**, issue **A1**).
- `NS` maps RSS 1.0 under `rss1`; real RDF feeds use `rdf` (issue **A3**).

---

## 3. Startup Data Flow (fetch → parse → sort → display)

```mermaid
sequenceDiagram
    autonumber
    participant Main as src/main.py
    participant App as FeedApp
    participant Mgr as FeedManager
    participant FF as FeedFetcher
    participant UF as URLFetcher
    participant C as Cache
    participant Net as Internet
    participant FP as FeedProcessor
    participant P as FeedParser
    participant FS as FeedSorter
    participant UI as UI / UIModel

    Main->>App: FeedApp().run()
    App->>Mgr: get_entries()
    loop over FEED_URLS
        Mgr->>FF: fetch(url)
        FF->>UF: fetch(url)
        UF->>C: get(url, allow_stale=True)
        alt cache hit (fresh, or stale with stale-while-revalidate)
            C-->>UF: CachedResponse content
        else cache miss / expired
            UF->>Net: GET url (conditional headers)
            Net-->>UF: 200 + content | 304
            UF->>C: set(url, response)
        end
        UF-->>FF: FetchResult(ok, content)
        FF-->>Mgr: bytes | None (skip on failure)
        Mgr->>FP: parse(xml_bytes)
        FP->>P: FeedParser(xml_bytes).parse()
        P-->>FP: List[FeedItem]
        FP-->>Mgr: List[FeedItem]
    end
    Mgr->>FS: sort(items)
    FS-->>Mgr: sorted newest-first
    Mgr-->>App: List[FeedItem]
    App->>UI: UI(entries, factory, page_parser).launch()
```

---

## 4. Article View Flow (fetch-on-open)

```mermaid
sequenceDiagram
    autonumber
    participant Ctrl as UIController
    participant Cmd as ShowDetailsCommand
    participant R as UIRenderer
    participant D as EntryDetails
    participant PP as PageParser
    participant UF as URLFetcher
    participant Net as Internet
    participant Std as stdscr

    Ctrl->>Cmd: execute(controller, stdscr)
    Cmd->>Ctrl: model.get_selected_entry()
    Cmd->>R: draw_details(stdscr, entry)
    R->>D: EntryDetails(entry, page_parser)
    D->>PP: get_content(entry.link)
    PP->>UF: fetch(url)
    UF->>Net: GET article page
    Net-->>UF: HTML
    PP-->>D: extracted paragraphs (or "Failed to fetch page.")
    D-->>R: wrapped header + content lines
    R-->>Std: addstr / addnstr
```

> **Note:** the article fetch in step 8 happens **inside the draw path** and
> blocks the TUI until the page loads — this is **ADR-002**'s "fetch-on-open"
> problem (issue **A4**). Scrolling the article view is handled by
> `ScrollDownCommand` / `ScrollUpCommand` operating on `EntryDetails.start_line`.

---

## 5. Related Documents

- `docs/feature_status.md` — feature list, open issues (A1–C2), roadmap, sprint plan
- `docs/arch_decision_records.md` — **ADR-001** (canonical date representation), **ADR-002** (fetch-on-open article loading)
- `docs/code_review.md` — full code review findings
- `docs/test_automation.md` — testing standards and patterns
- `CHANGELOG.md` — release history