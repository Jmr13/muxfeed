# muxfeed

A terminal-based web feed (RSS/Atom) reader for Android Termux and Linux.

- muxfeed fetches web feeds, parses articles, caches responses, and gives you an interactive terminal UI for browsing and reading articles/blogs directly from your terminal — no cloud, no tracking, no data shared with anyone.

## Reason

- Many applications no longer fully support older Android versions (6.0 and below). While some of these apps are still available on the Google Play Store, I often encountered cases where they could be installed but failed to function properly. This was especially noticeable with android web feed readers. I built muxfeed as a lightweight alternative that is partially independent of mobile platform limitations and focuses on a simple, terminal-native experience. 
- There are growing concerns about how companies collect and use data to train their AI models. As AI adoption continues to expand, it has become increasingly difficult to use these tools without potentially compromising own's data. Therefore, maintaining sovereignty over our data has become a top priority.

## Features

- RSS 2.0, RSS 1.0, and Atom feed support
- Scrollable article list with a full-content article viewer (article text extracted from the source page)
- Two-tier HTTP cache (in-memory + persisted to disk) with conditional GET (ETag / Last-Modified) and `304 Not Modified` handling
- Retry handling with backoff for resilient fetching
- CLI commands for managing RSS feeds
- No accounts, no network beyond the feeds you subscribe to — everything runs locally

## Compatibility

| Platform | Status |
| --- | --- |
| Android Termux | ✅ Tested |
| Linux | ✅ Tested |
| Windows | ❌ Not tested 

## Architecture

The application is split into four layers:

1. **Fetching** — `URLFetcher` with retry/backoff, backed by a two-tier `Cache` (memory + JSON files on disk)
2. **Parsing** — format-agnostic `FeedParser` dispatching to Atom / RSS1 / RSS2 parsers, plus a strategy-based `DateParser` and a `PageParser` that extracts readable article text with BeautifulSoup
3. **Application** — `FeedManager` wires fetch → parse → sort into a single entry list
4. **TUI** — curses UI built with MVC, the Command pattern, and a component factory

### Diagrams

- [Architecture (Mermaid)](./docs/ARCHITECTURE.md) — layer overview, class diagram, and sequence diagrams — renders on GitHub

## Installation

Prerequisite: Python 3.10+

1. Clone the repository

```bash
git clone <repo-url>
cd muxfeed
```

2. Create and activate a virtual environment

Linux / Termux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python -m src.main
```

This launches the interactive terminal UI: a scrollable feed list, and a full article viewer when you open an entry.

## Managing RSS Feeds

Feeds are stored in `src/feeds.json` (gitignored — your subscription list stays local).

| Command | Purpose |
| --- | --- |
| `python -m cli.list_rss` | List all configured feed URLs |
| `python -m cli.add_rss https://example.com/rss` | Add a single feed |
| `python -m cli.add_rss https://site1.com/rss,https://site2.com/feed` | Add multiple feeds (comma-separated) |
| `python -m cli.remove_rss https://example.com/rss` | Remove a single feed |
| `python -m cli.remove_rss https://site1.com/rss,https://site2.com/feed` | Remove multiple feeds (comma-separated) |

Adding a feed that already exists, or removing one that isn't configured, is reported and skipped.

## Keyboard Controls

### Feed List View

| Key | Action |
| --- | --- |
| ↑ / k | Move up |
| ↓ / j | Move down |
| ← / h | Scroll title left |
| → / l | Scroll title right |
| Enter | Open article |
| q / ESC | Quit |

### Article View

| Key | Action |
| --- | --- |
| ↑ / k | Scroll up |
| ↓ / j | Scroll down |
| q / ESC | Return to feed list |

## Running Tests

```bash
pytest
```

Note: `cache_test.py` and `date_parser_test.py` run offline. `fetcher_test.py`, `feed_parser_test.py`, and `page_parser_test.py` hit the live network and require an internet connection.

## Data Locations

| Data | Location |
| --- | --- |
| Feed URLs | `src/feeds.json` |
| HTTP cache | `~/.cache/muxfeed/` |

## Future Improvements

- Search support
- Read/unread tracking
- Pagination
- Parallel fetching of new articles and loading
- Disk size limit (auto cleanup in cache)
- Cache compression (gzip)
- Cache corruption recovery (atomic writes)

## License

MIT — see [LICENSE](./LICENSE).