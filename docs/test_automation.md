---

# muxfeed Test Automation Guide

This document is the test automation playbook for muxfeed, derived from the `test-automation-engineer` agent definition (`.qwen/agents/test-automation-engineer.md`). It defines the testing standards: determinism, network isolation, test data ownership, and the offline/network test split.

**Quick reference**

```bash
pytest -m "not network"               # hermetic offline gate — must always pass
pytest -m network                     # live-network lane (requires internet)
pytest                                # full suite
pytest tests/integration_test.py -x -q  # TUI integration (module-scoped live pipeline)
```

---

## 1. The Test Pyramid

| Layer | Unit | App integration | TUI integration |
|-------|------|-----------------|-----------------|
| What it covers | `FeedParser` (Atom/RSS1/RSS2), `DateParser`, `Cache` | `FeedFetcher → FeedProcessor → FeedSorter → FeedManager` | List + details render paths |
| How it runs | Inline XML bytes, injected timestamps | Fake fetch seam (`FetchResult`) | `FakeStdscr` + `StubPageParser` |
| Network | **Never** | **Never** | Pipe through a module-scoped live pipeline (exception) |

Rule: never a live feed a unit test could have faked. The offline tests (`cache_test.py`, `date_parser_test.py`) are the model; live-network tests (`fetcher_test.py`, `feed_parser_test.py`, `page_parser_test.py`) are a documented, marked exception.

## 2. Critical Rules

1. **No sleeps, no wall-clock dependence.** `time.sleep(0.5)` in a cache eviction test is a crutch. Drive time explicitly: inject `CachedResponse.cached_at` or `monkeypatch` the clock. Assert on state, never on elapsed time.
2. **Tests own their data.** Inline XML strings, `tmp_path` cache dirs, fresh `Cache` objects per test. Never depend on `src/feeds.json`, the real `~/.cache/muxfeed`, another test's leftovers, or "the seed feed."
3. **Isolate the network at the fetch boundary.** Seams: `URLFetcher.fetch()` returning `FetchResult`; `FeedFetcher.fetch()` returning `bytes`. Substitute a fake at one of these seams with canned `FetchResult(ok=True, content=...)`.
4. **Offline tests must pass with the network unplugged.** Genuinely live tests get a `network` marker so `pytest -m "not network"` is always a green, hermetic gate.
5. **Assert behavior, not private internals.** Assert on `FeedItem.to_dict()`, rendered `FakeStdscr` output, and public results — not `Cache._memory_cache` layout, except when the test is specifically about eviction policy.
6. **Pin the loose typing explicitly.** `FeedItem.date` is a formatted string (`"%B %d, %Y | %-I:%M %p"`), not the `datetime` its annotation claims; `DateParser.parse()` returns `None` for unparseable input. Tests document what each layer *should* do with `None`.
7. **Cache persistence is a side effect.** `CacheConfig(persistent=True)` writes JSON to `cache_dir` (default `~/.cache/muxfeed`) on every `set()`. Tests must override it with `tmp_path`.
8. **TUI tests use `FakeStdscr`, never real curses.** Draw paths catch `curses.error` and skip drawing by design — do not add error handling to draw code, and don't write tests that need it.
9. **Respect timezone and platform assumptions.** `DateParser` converts to the *local* timezone; output uses `%-I` (Linux/Termux only, not Windows). Expected date strings must be computed via `astimezone()`, never hard-coded from UTC.
10. **Fixture scope discipline.** `scope="module"`/`"session"` only for expensive, immutable pipelines; stateful objects (`Cache`, `URLFetcher`, pipeline components) are function-scoped.

## 3. Fixture and Test Patterns

### 3.1 Deterministic Parser Test (inline XML, zero network)

Raw bytes into `FeedParser`, exact dict out. Expected date computed in local timezone:

```python
from datetime import datetime, timezone
from src.parsers.feed_parser import FeedParser

ATOM_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Docs News</title>
  <entry>
    <title>First item</title>
    <link href="https://example.com/1" rel="alternate"/>
    <published>2026-01-01T00:00:00Z</published>
  </entry>
</feed>"""

def test_atom_parse_is_deterministic_and_offline():
    parsed = [item.to_dict() for item in FeedParser(ATOM_XML).parse()]

    expected_date = datetime(2026, 1, 1, tzinfo=timezone.utc).astimezone().strftime(
        "%B %d, %Y | %-I:%M %p"
    )
    assert parsed == [{
        "source": "Docs News",
        "title": "First item",
        "date": expected_date,          # a string, NOT a datetime
        "link": "https://example.com/1",
    }]
```

Same pattern covers RSS 2.0 (`<channel><title>` + `<item>`) and RSS 1.0. **RSS 1.0 caveat:** `NS` maps RSS 1.0 under the `rss1` prefix while real-world RDF feeds use `rdf`, so `rss1:` queries may not match production feeds. Pin test fixtures to what the code dispatches on; keep live RDF coverage in the `network` lane.

### 3.2 Network Isolation Seam (fake `FetchResult` for the app layer)

`FeedFetcher` expects `FetchResult` from its fetcher. Fake at that seam and `FeedFetcher → FeedProcessor → FeedSorter → FeedManager` runs offline:

```python
from src.fetchers.fetcher import FetchResult
from src.app.feed_manager import FeedFetcher, FeedProcessor, FeedSorter, FeedManager

class FakeFetcher:
    """Canned FetchResults keyed by URL — records every request made."""
    def __init__(self, xml_by_url):
        self.xml_by_url = xml_by_url
        self.requested_urls = []

    def fetch(self, url, force_refresh=False):
        self.requested_urls.append(url)
        return FetchResult(ok=True, content=self.xml_by_url[url], status_code=200)

def test_manager_skips_unfetchable_feeds_and_sorts():
    xml = b"""<rss version="2.0"><channel><title>Src</title><item>
      <title>Old post</title>
      <link>https://example.com/old</link>
      <pubDate>Thu, 01 Jan 2026 00:00:00 +0000</pubDate>
    </item></channel></rss>"""
    fetcher = FakeFetcher({"https://example.com/a": xml})
    manager = FeedManager(
        ["https://example.com/a", "https://unreachable.example.com/b"],
        FeedFetcher(fetcher), FeedProcessor(), FeedSorter(),
    )

    entries = manager.get_entries()

    assert fetcher.requested_urls == ["https://example.com/a", "https://unreachable.example.com/b"]
    assert entries and entries[0].source == "Src"
```

### 3.3 Cache Isolation Fixture (`tmp_path`, never the real cache)

`CacheConfig(cache_dir=...)` is the lever. Drive freshness with injected `cached_at`:

```python
import pytest
from datetime import datetime, timedelta
from src.fetchers.cache import Cache, CacheConfig, CachedResponse

@pytest.fixture
def isolated_cache(tmp_path):
    """Cache backed by a disposable dir — ~/.cache/muxfeed is never touched."""
    return Cache(CacheConfig(cache_dir=tmp_path / "muxfeed-test"))

def test_stale_entry_is_served_only_when_allowed(isolated_cache):
    stale = CachedResponse(
        content=b"news", status_code=200, headers={},
        cached_at=datetime.now() - timedelta(hours=1),   # default ttl is 15 min
    )
    isolated_cache.set("https://example.com/feed", stale)

    assert isolated_cache.get("https://example.com/feed", allow_stale=False) is None
    assert isolated_cache.get("https://example.com/feed", allow_stale=True) is not None
```

### 3.4 Parametrized Date Cases (TZ-safe)

`date_parser_test.py` parametrizes over `CASES` in `data.py`. Extensions must stay hermetic: **UTC-anchored** inputs whose expectations are computed in the local zone (see the `-16:00` case in `data.py`), never live-URL cases in the offline parametrize list.

### 3.5 TUI Render Test (`FakeStdscr`)

Mirror `tests/integration_test.py`: `FakeStdscr` capturing `addstr`/`addnstr`, `StubPageParser` so details views don't hit the article URL, assertions on rendered text. No real curses anywhere.

## 4. Offline Gate and Network Lane

No `conftest.py` / `pytest.ini` exists today. Proposed marker setup:

```python
# conftest.py
import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "network: hits the live internet; excluded from the hermetic offline gate",
    )
```

CI treats the offline gate as the merge blocker and the network lane as non-blocking-but-reported:

```yaml
jobs:
  unit-offline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest -m "not network" --strict-markers
  network-lane:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest -m network
      - name: Upload failure logs
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          path: .pytest_cache/         # full verbosity output artifact on red
```

## 5. Flake Triage Table

| Symptom | Likely root cause | The fix (not the workaround) |
|---------|-------------------|------------------------------|
| Passes locally, fails in CI | Live feed changed / CI slower | Move the feed under a `network` marker; use inline XML fixtures offline |
| Fails only on some machines | `DateParser` local-timezone conversion; `%-I` platform dependence | Compute expected dates via `astimezone()`; keep Linux/Termux as the target platform |
| Fails ~1 in 20 | `time.sleep()`-based cache timing in tests | Inject `cached_at` / monkeypatch the clock; assert on state |
| Fails after an "unrelated" change | Loose typing drift: `None` date/date string leaking into a consumer | Pin the contract test (`FeedItem.date` string-or-`None`) and fix the consumer |
| "Passes on retry" | Shared mutable fixture state (e.g., module-scoped `Cache`) | Function-scope the stateful fixture; keep module scope only for immutable pipelines |
| Random network flake in parser tests | `feed_parser_test.py` uses live URLs | Replace with inline XML; keep one canonical live parse under `network` |

## 6. Known Issues

- **Details renderer crashes on `None` dates** — `ui_components.py` feeds `entry.date` (which can be `None` for unparseable feed dates) to `textwrap.wrap()`, raising `AttributeError: 'NoneType' object has no attribute 'expandtabs'`. `tests/integration_test.py::test_end_to_end_fetch_parse_display_details` fails on this. Fix side: renderer should skip the date line when `None`. Test side: regression test pinning the "details view renders without a date line for `None` dates" contract.
- **`integration_test.py` reads `entry.date_str`** — no such attribute on `FeedItem` (it is `.date`). Currently masked by the renderer crash above; would fail once that is fixed.

## 7. Workflow and Metrics

Workflow: map the risk surface (parsers by format, date normalization, cache freshness/eviction, render paths) → audit for network leakage (grep for `requests`, live `https://` URLs, `URLFetcher()` instantiations) → build fixtures first (`FakeFetcher`, inline XML, `isolated_cache`, `FakeStdscr` + `StubPageParser`) → write to the determinism bar → run the full suite (offline failures are defects, network failures are reports) → operate like a service (watch duration, offline gate greenness, which live sources rot).

Success metrics:

- Offline gate pass rate 100%, repeated runs, **zero `time.sleep()`** in the suite
- Every live-network test marked `network`; the lane holds only genuine fetch-layer coverage
- 100% of offline failures reproducible from the failure line alone
- Cache tests never touch `~/.cache/muxfeed`; every `Cache` in tests is `tmp_path`-backed
- Escaped defects on covered layers: zero — a `None` date breaking the renderer means the contract regression test is already in place