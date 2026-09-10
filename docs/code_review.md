# Code Review — muxfeed

**Reviewer:** Qwen Code
**Date:** 2026-09-09
**Branch reviewed:** `trial6`

---

## Opening Summary

muxfeed is a well-structured terminal-based RSS/Atom reader built in Python with curses. The architecture is clean — four distinct layers (fetch → parse → app → TUI), proper use of Strategy and Command patterns, and sensible separation of concerns. The code quality is generally good for a project of this size.

The top-level concern is a **data type mismatch in the date pipeline** that could cause crashes at runtime, plus several correctness issues in the feed parsers and type annotations.

---

## Findings

### 🔴 Blocker

#### 1. `FeedItem.date` type mismatch — runtime crash risk

**Location:** `src/parsers/feed_parser.py`, `FeedItem.__init__` + `src/parsers/date_parser.py`, `DateParser.parse`

**Why:** `FeedItem.__init__` type-hints `date` as `Optional[datetime]`, but `DateParser.parse()` returns `Optional[str]` (a formatted string like `"January 01, 2026 | 12:00 AM"`). The `FeedItem.to_dict()` method puts this value directly into the dict, and `FeedSorter._parse_date()` calls `datetime.strptime()` on it — which would fail if it actually received a `datetime` object. Currently it works by accident because the actual value is a string, but the type contract is wrong and any future code relying on `item.date` being a `datetime` will crash.

**Suggestion:** Either:

1. Change `FeedItem.date` to `Optional[str]` and update `FeedItem.__init__` type hint accordingly, or
2. Have `DateParser.parse()` return `Optional[datetime]` and let the TUI/FeedSorter format it for display

---

#### 2. `FeedManager.parser` type annotation is wrong

**Location:** `src/app/feed_manager.py`, constructor

**Why:** The constructor types `parser` as `FeedParser`, but it's actually instantiated with a `FeedProcessor` (which wraps `FeedParser`). This means the type hint lies — `self.parser.parse(xml)` works only because `FeedProcessor` happens to also have a `.parse()` method. If either class changes shape, this breaks silently.

**Suggestion:** Change the type annotation from `parser: FeedParser` to `parser: FeedProcessor`.

---

### 🟡 Suggestion

#### 3. RSS 1.0 parser uses wrong namespace prefix

**Location:** `src/parsers/feed_parser.py`, `RSS1Parser.parse()`

**Why:** The `rss1` prefix in `NS` maps to `http://purl.org/rss/1.0/`, but real-world RSS 1.0 (RDF) feeds declare this namespace under the `rdf` prefix. So `".//rss1:title"` won't match `<rdf:title>` elements — ElementTree won't match a registered prefix to a different prefix in the source XML. RSS 1.0 feed items will silently return empty titles and no dates.

**Suggestion:** Query using the local tag name without prefix, or register the namespace under `rdf`:

```python
NS = {
    'rdf': 'http://purl.org/rss/1.0/',
    # ...
}
# Then: self._get_text(item, "rdf:title", "dc:date")
```

---

#### 4. `FEED_URLS` loaded once at import time, never refreshed

**Location:** `src/config.py`

**Why:** `FEED_URLS = load_feed_urls()` runs at module import. If a user adds/removes feeds via the CLI, the running TUI still sees the old list until restarted. This is an unexpected behavior for a live tool.

**Suggestion:** Load feed URLs lazily (e.g., in `FeedManager.__init__` or `FeedApp.__init__`) so changes take effect without restart.

---

#### 5. Silent exception swallowing in cache persistence

**Location:** `src/fetchers/cache.py`, `_save_persistent` and `_load_persistent`

**Why:** Both methods catch `Exception` and silently discard it. If cache files become corrupted or the disk is full, there's zero diagnostic output. Users will see stale data with no clue why.

**Suggestion:** At minimum, log the exception:

```python
except Exception as e:
    logging.debug("Cache load failed for %s: %s", key, e)
```

---

#### 6. Unused import in config.py

**Location:** `src/config.py`

**Why:** `from enum import Enum` is imported but never used. Dead code.

**Suggestion:** Remove the import.

---

### 💭 Nit

#### 7. Duplicate imports in feed_parser.py

**Location:** `src/parsers/feed_parser.py`

**Why:** `from typing import List, Optional` and `import xml.etree.ElementTree as ET` are both imported twice. Harmless but untidy.

---

#### 8. `is not` used for integer comparison in tests

**Location:** `tests/fetcher_test.py`

```python
assert result.status_code is not 200
```

**Why:** `is not` is an identity check, not an equality check. For integers, CPython interns small values so this works, but it's semantically wrong and may emit `SyntaxWarning` in Python 3.14+.

**Suggestion:** `assert result.status_code != 200`

---

#### 9. `list_rss.py` prints nothing for empty list

**Location:** `cli/list_rss.py`

**Why:** When no feeds are configured, it prints the message but doesn't `return`, so `main()` falls through (though since there's nothing after the loop, it's functionally fine — just slightly inconsistent with the other CLI tools).

---

## Closing

### Summary of key actions

1. Fix `FeedItem.date` type hint to match the actual string value (or change the pipeline to use datetime objects consistently)
2. Correct `FeedManager.parser` type annotation to `FeedProcessor`
3. Fix RSS 1.0 namespace prefix mapping for real-world RDF feeds
4. Add logging to silent exception handlers in the cache layer
5. Remove duplicate imports and unused `Enum` import

### Encouragement

The architecture is solid — clean MVC separation in the TUI, proper use of Strategy/Command patterns, well-designed two-tier cache with conditional GET. The README is thorough and the test suite covers the right boundaries. This is good work.

### Next steps

Fixing the date type mismatch is the highest priority — it's a latent bug waiting to surface. The RSS 1.0 namespace fix is important if you actually have RDF feed subscribers. The rest are quality-of-life improvements.
