# muxfeed — Qwen Code Project Context

Terminal-based RSS/Atom feed reader for Android Termux and Linux. Built with Python 3.10+ (currently running 3.14), curses TUI, no cloud.

## Commands

```bash
python -m src.main              # launch TUI
pytest                          # run tests
python -m cli.add_rss <url>     # add feed(s), comma-separated
python -m cli.list_rss          # list feeds
python -m cli.remove_rss <url>  # remove feed(s), comma-separated
```

Tests: `cache_test.py`, `date_parser_test.py` are offline. `fetcher_test.py`, `feed_parser_test.py`, `page_parser_test.py` hit the live network — require internet.

## Architecture (4 layers)

1. **Fetchers** — `src/fetchers/fetcher.py` (`URLFetcher`: retry/backoff, conditional GET), `src/fetchers/cache.py` (two-tier memory + JSON disk cache in `~/.cache/muxfeed/`)
2. **Parsers** — `src/parsers/feed_parser.py` (Atom/RSS1/RSS2 dispatch), `date_parser.py` (strategy-based TZ normalization), `page_parser.py` (BeautifulSoup article text extraction)
3. **Application** — `src/app/feed_manager.py` (`FeedFetcher` → `FeedProcessor` → `FeedSorter` → `FeedManager`), `src/app/feed_app.py` wiring
4. **TUI** — `src/tui/` MVC: `ui_model.py` (state), `ui_renderer.py` + `ui_components.py` (view), `ui_controller.py` + `ui_controller_commands.py` (Command pattern), `ui_component_factory.py` (Factory)

## Key Conventions

- **Data types are loose — verify before relying.** `FeedItem.date` is typed `Optional[datetime]` but actually holds a formatted string (`"%B %d, %Y | %-I:%M %p"`); `DateParser.parse()` returns that string or `None`. `FeedManager.parser` is annotated `FeedParser` but is a `FeedProcessor`.
- **Feed dates** flow: `DateParser.parse` → string → `FeedItem.date` → `FeedSorter._parse_date()` re-parses with `strptime("%B %d, %Y | %I:%M %p")`.
- **`FEED_URLS` is loaded once at import** in `src/config.py` — stale after CLI feed changes until restart.
- **Namespace caveat:** `NS` maps RSS 1.0 under `rss1` prefix; real-world RDF feeds use `rdf`, so `rss1:` queries may not match.
- **Cache errors are silently swallowed** in `_save_persistent`/`_load_persistent` by design.
- Feeds list: `src/feeds.json` (gitignored, user-local).
- Date strings use `%-I` (strip leading zero) — platform-dependent; works on Linux/Termux, not Windows.
- Tests use bare `from data import ...` (tests dir is on sys.path via pytest rootdir/conftest). No `pyproject.toml`/`setup.py`.
- UI components catch `curses.error` and skip drawing — do not add error handling elsewhere in draw paths.