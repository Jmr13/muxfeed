# Changelog

All notable changes to muxfeed are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Version numbers reflect the feature set: `v1.0.0` marks the release where the
core feature set was complete (fetch → parse → cache → TUI), patch releases
carry fixes and internal work, and the next minor (`1.1.0`) will land the
roadmap features (read/unread tracking, parallel fetching, disk cache limits).

---

## [Unreleased] — next planned: 1.0.1

Work since `v1.0.0` (2026-06-15 → 2026-09-09). No user-facing features added;
all changes are internal, so this ships as a patch release.

### Changed

- Feed parser strategy selection improved for more reliable format dispatch
- `compile_files.py`: raised `MAX_FILE_SIZE`, added files to ignore lists

### Chores

- Added team agent definitions under `.qwen/agents/`
- Ignored `.qwen/tmp` scratch directory

### Docs

- README updates

---

## [1.0.0] - 2026-06-15

First tagged release. The core feature set is complete: a terminal RSS/Atom
reader that fetches feeds with resilient HTTP, caches responses two-tier,
parses all three major feed formats, and renders them in a curses TUI.

### Added

- **Feed parsing** — modular `FeedParser` dispatching to Atom, RSS 2.0, and
  RSS 1.0 (RDF) parsers, with a `BaseFeedParser` interface and parametrized tests
- **Strategy-based date parsing** — ISO 8601, RFC 822, and timezone-abbreviation
  formats (PST/PDT/UTC/CET/IST/JST/AEST) normalized to local time via
  `DateParser` + `DateParseStrategy` classes with a selection resolver
- **Two-tier HTTP cache** — in-memory cache plus JSON persistence on disk
  (`~/.cache/muxfeed/`), SHA-256 URL keys, size-capped memory eviction
- **Conditional GET** — ETag / Last-Modified headers, `304 Not Modified`
  handling, and stale-while-revalidate
- **Resilient fetching** — `requests` + `urllib3.Retry` with backoff,
  retry on connect/read/status for 408/429/5xx, timeout handling, and
  Chrome-style User-Agent spoofing
- **Curses TUI** — MVC architecture with the Command pattern and a component
  factory; scrollable feed list with horizontal title scrolling (`h`/`l`)
  and a scrollable full-content article viewer
- **Article extraction** — `PageParser` extracts readable text from source
  pages with BeautifulSoup (`<article>`/`<main>` → `<p>` text)
- **CLI feed management** — `cli.add_rss`, `cli.remove_rss`, `cli.list_rss`
  with comma-separated bulk operations, duplicate/validation checks
- **Feed URL persistence** — `src/feeds.json`, gitignored, user-local
- **Tests** — offline unit tests for cache (`tests/cache_test.py`) and date
  parsing (`tests/date_parser_test.py`); live tests for fetcher, feed parser,
  and page parser; integration test for fetch → parse → render with a
  `FakeStdscr` stand-in
- **Documentation** — README (installation, usage, keyboard controls,
  compatibility), class diagrams, and a cache-retrieval sequence diagram

### Changed

- Fetcher rewritten onto `requests` with the Retry adapter (replacing the
  legacy custom implementation)
- Cache simplified: JSON persistence replacing pickle; memory and disk
  eviction separated into dedicated methods (disk eviction prepared but
  disabled); stats tracking removed
- Project structure: `pyproject.toml` removed in favor of plain
  `requirements.txt` + absolute `src` package imports; `lxml` dropped for
  the stdlib `xml.etree.ElementTree`
- TUI reworked into MVC + Command + Factory; `FeedApp`/`FeedManager` wired
  with dependency injection for fetchers and parsers
- Type hints and method signatures tightened across modules

### Fixed

- Entry details text wrapping to terminal width and scrollable range in the
  article view
- `FeedSorter` sort-by-date logic (display-string round-trip via `strptime`)
- Page parser tests: corrected live URL and assertions
- Cache eviction ordering (oldest entries evicted first)
- Removed debug logging and unused imports

### Security

- No telemetry, no accounts, no cloud: the app only contacts subscribed feed
  and article URLs; everything else runs locally

---

## [0.1.0] - 2026-01-10

Initial codebase — project scaffolding only.

- Basic project structure
- Feed fetching/parsing skeleton and initial TUI integration
- Dependency cleanup (`lxml` → stdlib `ElementTree`)