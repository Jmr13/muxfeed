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

1. **Fetchers** — `src/fetchers/fetcher.py` (`URLFetcher`: retry/backoff, conditional GET, SSRF validation (private/loopback/link-local IPs blocked), concurrent `fetch_batch()` via `ThreadPoolExecutor`, random User-Agent rotation), `src/fetchers/cache.py` (thread-safe two-tier memory + JSON disk cache in `~/.cache/muxfeed/`, atomic writes via temp+rename, base64-encoded storage with hex backward compat, stale-while-revalidate on disk)
2. **Parsers** — `src/parsers/feed_parser.py` (Atom/RSS1/RSS2 dispatch via `BaseFeedParser` ABC), `date_parser.py` (strategy-based TZ normalization, 9 strategy classes), `page_parser.py` (BeautifulSoup article text extraction)
3. **Application** — `src/app/feed_manager.py` (`FeedFetcher` → `FeedProcessor` → `FeedSorter` → `FeedManager`), `src/app/feed_app.py` wiring
4. **TUI** — `src/tui/` MVC: `ui_model.py` (state), `ui_renderer.py` + `ui_components.py` (view), `ui_controller.py` + `ui_controller_commands.py` (Command pattern), `ui_component_factory.py` (Factory)

## Key Conventions

- **Data types are loose — verify before relying.** `FeedItem.date` is typed `Optional[datetime]` but actually holds a formatted string (`"%B %d, %Y | %-I:%M %p"`); `DateParser.parse()` returns that string or `None`. `FeedManager.parser` is annotated `FeedParser` but is a `FeedProcessor`.
- **Feed dates** flow: `DateParser.parse` → string → `FeedItem.date` → `FeedSorter._parse_date()` re-parses with `strptime("%B %d, %Y | %I:%M %p")`.
- **`FEED_URLS` is loaded once at import** in `src/config.py` — stale after CLI feed changes until restart.
- **Namespace caveat:** `NS` maps RSS 1.0 under `rss1` prefix; real-world RDF feeds use `rdf`, so `rss1:` queries may not match.
- **Cache errors are silently swallowed** in `_save_persistent`/`_load_persistent` by design. `_load_persistent` loads without staleness check — `Cache.get()` handles freshness/staleness uniformly. Stale entries are evicted from memory only on `get()` miss, not from disk, preserving stale-while-revalidate across restarts.
- **Fetcher datetimes are UTC-aware.** All `cached_at` values use `datetime.now(timezone.utc)`. `CachedResponse.age` normalizes legacy naive datetimes to UTC before comparison.
- **HTTP 4xx does not serve stale content.** Only 5xx server errors fall back to stale cached entries; 4xx (404, 403, etc.) returns `ok=False` directly.
- **Retry/redirect settings apply to all sessions**, including caller-supplied ones — `max_redirects` and `HTTPAdapter` with retry strategy are always mounted.
- Feeds list: `src/feeds.json` (gitignored, user-local).
- Date strings use `%-I` (strip leading zero) — platform-dependent; works on Linux/Termux, not Windows.
- Tests use bare `from data import ...` (tests dir is on sys.path via pytest rootdir/conftest). No `pyproject.toml`/`setup.py`. `conftest.py` at project root is empty.
- UI components catch `curses.error` and skip drawing — do not add error handling elsewhere in draw paths.
- `cli/` has no `__init__.py` — not a proper package; modules work via `python -m cli.<name>` from project root.

## Docs & Tooling

- `docs/` — `ARCHITECTURE.md` (Mermaid diagrams, sequence flows), `arch_decision_records.md` (2 proposed ADRs), `code_review.md` (9 findings), `feature_status.md` (done list + sprint plan), `test_automation.md` (test pyramid + CI pipeline)
- `llm/compile_files.py` — utility to compile `.py` files into `.md` for LLM context (ignores `__pycache__`, `.git`, `.venv`, `tests`, `docs`)
- `.qwen/agents/` — 7 SDLC agents: sprint-prioritizer, software-architect, doc-first-engineer, test-automation-engineer, code-reviewer, technical-writer, devops-automator
