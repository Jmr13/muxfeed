# Architecture Decision Records

This document collects the architectural decisions made for muxfeed. Each ADR captures the context, options considered, and rationale behind a design choice.

---

## ADR-001: Canonical Date Representation Across Layers

### Status

Proposed

### Context

Feed dates pass through three layers of the application:

1. `DateParser.parse()` parses raw feed date strings (ISO 8601, RFC 822, timezone abbreviations) and returns a **formatted display string** (`"%B %d, %Y | %-I:%M %p"`) or `None`.
2. `FeedItem.date` is type-annotated `Optional[datetime]` but holds the formatted string from step 1 at runtime.
3. `FeedSorter._parse_date()` re-parses that display string back into a `datetime` with `strptime("%B %d, %Y | %I:%M %p")` to sort entries newest-first; `EntryDetails` renders the string directly.

The annotation, the runtime value, and the consumer expectations disagree. Three layers share a value whose representation is only held together by the exact `strftime`/`strptime` format literal being duplicated in `DateParser`, `FeedSorter`, and `tests/data.py`.

The risk: any consumer that treats `FeedItem.date` as a `datetime` (as the type hint promises) crashes or silently misbehaves. Any change to the display format breaks sorting unless `FeedSorter` is updated in lockstep.

### Options Considered

| Option | Description |
|--------|-------------|
| **A — Canonical `datetime`, format at the edge** | `DateParser.parse()` returns `Optional[datetime]`. `FeedSorter` sorts on the real value. `EntryDetails` formats for display. Display format lives in exactly one place. |
| **B — Keep the string, fix the annotations** | `FeedItem.date` becomes `Optional[str]`. Sorting keeps round-tripping through `strptime`. Format literal still duplicated across `DateParser` and `FeedSorter`. |
| **C — Do nothing** | Accept the mismatch as incidental complexity. |

### Decision

Adopt **Option A**: `DateParser.parse()` returns `Optional[datetime]`; `FeedItem.date` is annotated `Optional[datetime]` and holds a real `datetime`; `FeedSorter` sorts on the value directly; `EntryDetails` (and only `EntryDetails`) formats for display.

### Consequences

**What gets easier:**

- Sorting is correct by construction — no round-trip through a display string.
- Type hints tell the truth; tools like mypy/pyright can actually check the pipeline.
- Display format is configurable without touching the data path.
- New consumers (search, read/unread, pagination) receive a comparable value.

**What gets harder:**

- `EntryDetails` and any other view gains a formatting responsibility (a small `strftime` call — a fair trade for a single source of truth).
- One-time migration: fix `DateParser`, `FeedSorter`, `FeedItem` annotation, `tests/data.py`, and the existing `code_review.md` finding #1 becomes resolved.
- `DateParser`'s timezone-to-local conversion currently happens at parse time; with Option A that stays in `DateParser` (parse once, normalize once), so no behavior change there.

---

## ADR-002: Fetch-on-Open Article Loading

### Status

Proposed

### Context

Opening an entry in the TUI switches to the details view. `EntryDetails` (a curses view component) constructs itself by calling `PageParser.get_content(entry.link)` — which performs a **blocking network fetch and HTML parse** inside the draw path. `UIRenderer.draw_details()` creates the component; the component fetches.

The existing `URLFetcher` HTTP cache is two-tier (memory + disk) and covers feed XML fetches. Article bodies are deliberately **not** cached (the README's "Future improvements" lists cache compression and disk-size limits as pending work, implying article caching is undesigned).

### Options Considered

| Option | Description |
|--------|-------------|
| **A — Fetch in the command (as-is)** | Move the fetch into `ShowDetailsCommand.execute()` so the view receives already-fetched content. No UX change, no new caching, removes network I/O from the view layer. |
| **B — Pre-fetch all articles at startup** | Fetch every article body during feed load. No per-open latency, but startup becomes slow as subscriptions grow, and body content is fetched even for articles never opened. |
| **C — Cache article bodies** | Extend the two-tier cache to article URLs with a longer TTL. Best long-term UX (fast re-opens), but adds disk-growth management beyond the immediate scope. |

### Decision

Adopt **Option A**: move the article fetch out of the view into `ShowDetailsCommand` (or a small application-layer use-case, e.g. `FeedReader.get_article(entry)`), so `EntryDetails` receives fetched content instead of fetching. Keep fetch-on-open timing (no pre-fetch). Treat Option C as the evolution step.

### Consequences

**What gets easier:**

- View layer becomes pure rendering — no side effects in draw paths, testable without network (the existing `StubPageParser` pattern in `integration_test.py` already assumes this shape).
- Blocking network I/O is confined to the command/application layer where failure policy (retry, error message, skip) can be decided, instead of silently freezing the TUI inside a draw.
- The application layer gets a natural seam to add article caching later (Option C) without touching the view.

**What gets harder:**

- `ShowDetailsCommand` gains a fetch orchestration responsibility (mitigated if routed through a small application use-case).
- Repeated opens of the same article re-fetch until speculative caching (Option C) is implemented.
- First-open latency is unchanged (by design — no pre-fetch).
