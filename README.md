# muxfeed

A terminal-based web feed (RSS/Atom etc.) reader.

This project fetches web feeds, parses articles, caches responses, and provides an interactive terminal UI for browsing and reading articles/blogs directly from your terminal.

## Why I Built This

- Many applications no longer fully support older Android versions (6.0 and below). While some of these apps are still available on the Google Play Store, I often encountered cases where they could be installed but failed to function properly. This was especially noticeable with android web feed readers. I built muxfeed as a lightweight alternative that is partially independent of mobile platform limitations and focuses on a simple, terminal-native experience. 
- There are growing concerns about how companies collect and use data to train their AI models. As AI adoption continues to expand, it has become increasingly difficult to use these tools without potentially compromising own's data. Therefore, maintaining sovereignty over our data has become a top priority.
- The project also serves as an opportunity to practice software design principles while creating a tool that I can use regularly in my old phone.

## Features

- RSS 2.0, RSS 1.0, and Atom feed support
- Scrollable article list and article viewer
- HTTP caching with persistent storage
- Retry handling and resilient fetching
- CLI commands for managing RSS feeds

## Documentation

### Class Diagram
![Class Diagram](./docs/class_diagram.drawio.png)

## Installation

1. Clone the repository
```
git clone <your-repo-url>
cd <repo-name>
```

2. Create a virtual environment
For linux
```
python -m venv .venv
source .venv/bin/activate
```
For Windows
```
.venv\Scripts\activate
```

3. Install dependencies
```
pip install -r requirements.txt
```

Running the Application

```python -m src.main```

## Managing RSS Feeds

Feeds are stored in:

src/feeds.json

### Add RSS feeds

``` python -m cli.add_rss https://example.com/rss ```

### Add multiple feeds

``` python -m cli.add_rss https://site1.com/rss,https://site2.com/feed ```

### List configured feeds

``` python -m cli.list_rss ```

### Remove RSS feeds

``` python -m cli.remove_rss https://example.com/rss ```

## Keyboard Controls

### Feed List View

Key| Action
"↑ / k"| Move up
"↓ / j"| Move down
"← / h"| Scroll title left
"→ / l"| Scroll title right
"Enter"| Open article
"q / ESC"| Quit

### Article View

Key| Action
"↑ / k"| Scroll up
"↓ / j"| Scroll down
"q / ESC"| Return to feed list

# Utility Scripts

Compile source code files into Markdown

Useful for LLM context generation or documentation snapshots.
``` python llm/compile_files.py ```

This generates:

compiled_python_1.md
compiled_python_2.md
...

## Future Improvements

- Search support
- Read/unread tracking
- Pagination
- Parallel fetching of new article and loading
- Disk size limit (auto cleanup in cache)
- Cache compression (gzip)
- cache corruption recovery (atomic writes)

## Supports
- Android Termux ✅ 
- Linux ✅ 
- Windows ❌ (Not tested yet)