# muxfeed — Feature Status & Priorities

**Reviewed:** 2026-09-09
**Branch:** `trial6`

---

## Features — Done ✅

Implemented, functional, and shipped.

| # | Feature | Location | Notes |
|---|---------|----------|-------|
| 1 | RSS 2.0 parsing | `src/parsers/feed_parser.py` `RSS2Parser` | Works for all three feed formats |
| 2 | RSS 1.0 (RDF) parsing | `src/parsers/feed_parser.py` `RSS1Parser` | ⚠️ Namespace prefix may not match real feeds (see A1) |
| 3 | Atom feed parsing | `src/parsers/feed_parser.py` `AtomParser` | Covers `<link>` variants, rel=alternate |
| 4 | HTTP fetch with retry/backoff | `src/fetchers/fetcher.py` `URLFetcher` | `requests` + `urllib3.Retry`, status_forcelist 408/429/5xx |
| 5 | Two-tier HTTP cache (memory + disk) | `src/fetchers/cache.py` | SHA-256 keyed, `~/.cache/muxfeed/*.cache` |
| 6 | Conditional GET (ETag / Last-Modified) | `src/fetchers/fetcher.py` `_prepare_headers` | 304 Not Modified refreshes cache timestamp |
| 7 | Stale-while-revalidate | `src/fetchers/cache.py` `CacheConfig.stale_while_revalidate` | Stale entries still served on fetch |
| 8 | LRU memory eviction | `src/fetchers/cache.py` `_evict_if_needed` | Evicts oldest 20% at 100-item cap |
| 9 | Interactive TUI (curses) | `src/tui/` MVC layer | Full MVC, scrollable, keyboard-driven |
| 10 | Scrollable feed list | `src/tui/ui_components.py` `EntryList` | Horizontal scroll for long titles |
| 11 | Full-content article viewer | `src/tui/ui_components.py` `EntryDetails` | Fetches and renders page text |
| 12 | HTML article text extraction | `src/parsers/page_parser.py` | BeautifulSoup; extracts `<article>`/`<main>` → `<p>` text |
| 13 | Command pattern keyboard input | `src/tui/ui_controller_commands.py` | 9 commands: Move, Scroll, Show, Quit |
| 14 | Component factory (TUI widgets) | `src/tui/ui_component_factory.py` | TitleBar, EntryList, EntryDetails |
| 15 | Strategy-based date parsing | `src/parsers/date_parser.py` | 5 strategies: ISO, ISO+TZ, RFC, RFC+TZ1, RFC+TZ2 |
| 16 | Timezone normalization to local | `src/parsers/date_parser.py` | Handles PST/PDT/UTC/CET/IST/JST/AEST abbreviations |
| 17 | CLI: add feeds | `cli/add_rss.py` | Comma-separated bulk add, duplicate/validation |
| 18 | CLI: remove feeds | `cli/remove_rss.py` | Comma-separated bulk remove |
| 19 | CLI: list feeds | `cli/list_rss.py` | Prints all configured URLs |
| 20 | User-Agent spoofing | `src/fetchers/fetcher.py` | Chrome UA, Accept headers, keep-alive |
| 21 | Feed URL persistence (JSON) | `src/config.py` + `src/feeds.json` | Gitignored; user-local subscription list |
| 22 | Architecture diagrams | `docs/ARCHITECTURE.md` | Mermaid — layer overview, class diagram, sequence diagrams |
| 23 | Integration tests | `tests/integration_test.py` | End-to-end: fetch → parse → render with FakeStdscr |
| 24 | Unit tests: cache | `tests/cache_test.py` | Offline; set/get/miss/eviction |
| 25 | Unit tests: date parser | `tests/date_parser_test.py` | Offline; parametrized across all date formats |
| 26 | Live tests: fetcher | `tests/fetcher_test.py` | Online; existing + nonexistent URLs |
| 27 | Live tests: feed parser | `tests/feed_parser_test.py` | Online; parametrized Atom/RSS1/RSS2 |
| 28 | Live tests: page parser | `tests/page_parser_test.py` | Online; success + failure |
| 29 | Comprehensive README | `README.md` | Installation, commands, keyboard controls, architecture, compatibility |
| 30 | Architecture decisions documented | `docs/ADR-001`, `docs/ADR-002`, `docs/code_review.md` | Date contract, fetch-on-open, full review |

---

## Features Needing Attention 🚨

### 🔴 Critical — Blockers (wrong behavior or crash risk)

| # | Issue | File | Impact | Fix effort |
|---|-------|------|--------|-----------|
| A1 | **Date type mismatch across layers** | `feed_parser.py`, `feed_manager.py`, `date_parser.py` | `FeedItem.date` typed `datetime` but holds formatted string. Contract broken; any datetime consumer crashes. See **ADR-001**. | Small |
| A2 | **`FeedManager.parser` type annotation wrong** | `feed_manager.py` | Annotated `FeedParser`, receives `FeedProcessor`. Works by accident (duck typing). | Trivial |
| A3 | **RSS 1.0 namespace prefix mismatch** | `feed_parser.py` `NS` dict + `RSS1Parser` | `rss1` prefix won't match real-world `rdf`-prefixed RDF feeds. Silent data loss: empty titles, no dates. | Small |
| A4 | **UI blocking I/O in draw path** | `ui_components.py` `EntryDetails._load_content` | Network fetch blocks curses during draw. TUI freezes on slow articles. See **ADR-002**. | Small |

### 🟡 Should Fix — Quality / Correctness

| # | Issue | File | Impact | Fix effort |
|---|-------|------|--------|-----------|
| B1 | **`FEED_URLS` loaded once at import, never refreshed** | `config.py` | CLI feed changes require full restart. | Small |
| B2 | **Silent exception swallowing in cache persistence** | `cache.py` `_save/persistent` | Disk-full or corruption errors vanish with zero trace. | Trivial |
| B3 | **`config.py` is a god-module (mixed concerns)** | `config.py` | Holds paths, I/O, XML namespaces, TZ offsets — imported by every layer. | Medium |
| B4 | **`FeedFetcher`/`FeedProcessor` are pass-through wrappers** | `feed_manager.py` | Each wraps a single try/except; failure mode lost (timeout/500/parse error → same `None`). | Small |
| B5 | **Unused imports** | `config.py` (`Enum`), `feed_parser.py` (duplicates) | Dead code, lint noise. | Trivial |
| B6 | **`is not` used for integer comparison in tests** | `fetcher_test.py` | `assert result.status_code is not 200` — semantic identity check, may warn in Python 3.14+. | Trivial |

### 💭 Nice to Have

| # | Issue | File | Impact | Fix effort |
|---|-------|------|--------|-----------|
| C1 | **`list_rss.py` prints nothing for empty list (missing return)** | `cli/list_rss.py` | Functionally fine, inconsistent with other CLI tools. | Trivial |
| C2 | **`UIComponentFactory` adds abstraction without clear value** | `ui_component_factory.py` | Conditional factory; `UIRenderer` could construct components directly. | Trivial |

---

## Roadmap — Not Yet Implemented

From README `## Future Improvements` — none started.

| # | Feature | User Value | Effort | Notes |
|---|---------|-----------|--------|-------|
| R1 | **Read/unread tracking** | High | Medium | Core UX expectation; needs local state persistence (JSON or SQLite) |
| R2 | **Parallel fetching** | High | Medium | Currently sequential; slow on 5+ feeds; `concurrent.futures` needed |
| R3 | **Disk size limit (cache auto-cleanup)** | High | Small | Important for Termux (limited storage); memory eviction exists but not disk |
| R4 | **Cache corruption recovery (atomic writes)** | Medium | Small | Write to `.tmp`, then rename — one-line fix |
| R5 | **Search support** | Medium | Small | Useful for large feed lists; low complexity with existing data model |
| R6 | **Cache compression (gzip)** | Low | Small | Diminishing returns for XML/HTML text; defer until disk limits are in |
| R7 | **Pagination** | Low | Small | Virtual scrolling already works; only needed for 100+ feeds |

---

## Recommended Sprint Plan

Ordered by risk reduction × effort ratio.

### Sprint 1 — Fix the data contract (ADR-001)
**Effort: Small | Risk reduction: HIGH**

- [ ] Make `DateParser.parse()` return `Optional[datetime]` (not formatted string)
- [ ] Fix `FeedItem.date` type hint to `Optional[datetime]`
- [ ] Remove `FeedSorter._parse_date()` round-trip; sort on datetime directly
- [ ] Move display formatting to `EntryDetails` only
- [ ] Update `tests/data.py` expected values
- [ ] Clean up duplicate imports (`feed_parser.py`) and unused `Enum` (`config.py`)
- [ ] Fix `is not 200` → `!= 200` in `fetcher_test.py`

### Sprint 2 — Move fetch out of the view (ADR-002)
**Effort: Small | Risk reduction: MEDIUM**

- [ ] Move article fetch from `EntryDetails.__init__` → `ShowDetailsCommand` or new `FeedReader.get_article()`
- [ ] Pass fetched content to `EntryDetails` as constructor argument
- [ ] Update `StubPageParser` in integration test

### Sprint 3 — Namespace + cache hardening
**Effort: Medium | Risk reduction: HIGH**

- [ ] Fix RSS 1.0 namespace: `rss1` → `rdf` in `NS` dict
- [ ] Add `logging.debug` to `_save_persistent` / `_load_persistent`
- [ ] Implement atomic cache writes (write `.tmp`, rename)
- [ ] Add disk size limit with LRU eviction

### Sprint 4 — Parallel fetching
**Effort: Medium | UX improvement: HIGH**

- [ ] Refactor `FeedManager.get_entries()` to use `concurrent.futures.ThreadPoolExecutor`
- [ ] Keep synchronous fallback for environments without threading

### Sprint 5 — Read/unread tracking
**Effort: Medium | UX improvement: HIGH**

- [ ] Design local state store (JSON in `~/.cache/muxfeed/`)
- [ ] Track last-seen entry links
- [ ] Visual indicator (bold/gray) in TUI feed list

### Backlog (no timeline)
- Search support
- Cache compression (gzip)
- Pagination
