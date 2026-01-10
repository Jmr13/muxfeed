#!/usr/bin/env python3
import curses
import requests
from bs4 import BeautifulSoup
import textwrap
import xml.etree.ElementTree as ET
    
# List of XML feed URLs
feed_urls = [
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://www.fastcompany.com/technology/rss",
    "https://www.inquirer.net/fullfeed/",
    "https://news.mit.edu/rss/topic/artificial-intelligence2",
    "https://nesslabs.com/feed",
    "http://neurosciencenews.com/feed/",
    "https://www.sciencedaily.com/rss/top/technology.xml",
    "http://rss.slashdot.org/Slashdot/slashdotMain",
    "https://www.slashgear.com/category/technology/feed/",
    "https://techcrunch.com/feed/",
    "https://www.theguardian.com/us/technology/rss",
    "https://www.theverge.com/rss/tech/index.xml",
    "http://venturebeat.com/feed/",
    "https://news.ycombinator.com/rss"
]

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}

# Fetch and parse all feeds
entries = []

for url in feed_urls:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        continue

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError:
        continue
    
    feed_items = root.findall(".//item") + root.findall(".//entry")
    
    for item in feed_items:
        title_el = item.find("title")
        title = title_el.text.strip() if title_el is not None and title_el.text else "No title"
    
        pub_date_el = (
            item.find("published") or
            item.find("updated") or
            item.find("pubDate")
        )
        pub_date = pub_date_el.text.strip() if pub_date_el is not None and pub_date_el.text else "No date"
    
        link_el = item.find("link")
        link = None
        if link_el is not None:
            # RSS <link> is text; Atom <link> has href attr
            if link_el.text and link_el.text.strip():
                link = link_el.text.strip()
            elif "href" in link_el.attrib:
                link = link_el.attrib["href"]
    
        if link:
            entries.append({"title": title, "date": pub_date, "link": link})
            
if not entries:
    print("No news found in feeds.")
    exit()

# Fetch article HTML and extract text paragraphs
def get_page_content(url):
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        paragraphs = soup.find_all('p')
        text = '\n\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
        return text if text else "No readable content found."
    except:
        return "Failed to fetch or parse page."

# Terminal UI
def main(stdscr):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)   # selection
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK) # current line in article

    current_row = 0
    feed_scroll = 0  # scroll for feed list
    reading_mode = False
    page_lines = []
    page_scroll = 0
    article_row = 0

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        if reading_mode:
            # Wrap article lines
            wrapped_lines = []
            for line in page_lines:
                wrapped_lines.extend(textwrap.wrap(line, width=w-1) or [''])
            visible_lines = wrapped_lines[page_scroll:page_scroll + h - 1]

            for idx, line in enumerate(visible_lines):
                y = idx
                real_idx = page_scroll + idx
                if real_idx == article_row:
                    stdscr.attron(curses.color_pair(2))
                    stdscr.addstr(y, 0, line)
                    stdscr.attroff(curses.color_pair(2))
                else:
                    stdscr.addstr(y, 0, line)
            stdscr.addstr(h-1, 0, "Arrow ↑/↓ scroll, 'b' back to feed list")
        else:
            # Display feed list with wrapping
            row_idx = 0
            visible_entries = entries[feed_scroll:]
            for idx, entry in enumerate(visible_entries):
                lines = textwrap.wrap(f"{entry['title']} ({entry['date']})", width=w-1) or ['']
                for line in lines:
                    if row_idx >= h-1:
                        break
                    if idx + feed_scroll == current_row:
                        stdscr.attron(curses.color_pair(1))
                        stdscr.addstr(row_idx, 0, line)
                        stdscr.attroff(curses.color_pair(1))
                    else:
                        stdscr.addstr(row_idx, 0, line)
                    row_idx += 1
                if row_idx >= h-1:
                    break

            stdscr.addstr(h-1, 0, "Arrow ↑/↓ navigate, Enter to read, ESC to quit")

        stdscr.refresh()
        key = stdscr.getch()

        if reading_mode:
            if key == curses.KEY_UP and article_row > 0:
                article_row -= 1
                if article_row < page_scroll:
                    page_scroll -= 1
            elif key == curses.KEY_DOWN and article_row < len(wrapped_lines) - 1:
                article_row += 1
                if article_row >= page_scroll + h - 1:
                    page_scroll += 1
            elif key == ord('b'):
                reading_mode = False
                page_scroll = 0
                article_row = 0
        else:
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
                if current_row < feed_scroll:
                    feed_scroll -= 1
            elif key == curses.KEY_DOWN and current_row < len(entries) - 1:
                current_row += 1
                if current_row >= feed_scroll + h - 1:
                    feed_scroll += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                content = get_page_content(entries[current_row]['link'])
                page_lines = content.split('\n')
                reading_mode = True
                page_scroll = 0
                article_row = 0
            elif key == 27:  # ESC
                break

# Run the terminal feed reader
curses.wrapper(main)
