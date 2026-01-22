import curses
from src.parsers.page_parser import PageParser

class UIComponent:
    def draw(self, stdscr):
        raise NotImplementedError

class TitleBar(UIComponent):
    def __init__(self, text):
        self.text = text

    def draw(self, stdscr):
        height, width = stdscr.getmaxyx()
        stdscr.addstr(0, 0, self.text[:width - 1], curses.A_BOLD)

class EntryList(UIComponent):
    def __init__(self, entries, selected=0, start_index=0):
        self.entries = entries
        self.selected = selected
        self.start_index = start_index

    def draw(self, stdscr):
        height, width = stdscr.getmaxyx()
        visible_items = height - 2
        end_index = min(self.start_index + visible_items, len(self.entries))

        for row, entry_idx in enumerate(range(self.start_index, end_index), start=1):
            entry = self.entries[entry_idx]
            line = f"{entry['date']} | {entry['source']} | {entry['title']}"[:width - 1]
            attr = curses.A_REVERSE if entry_idx == self.selected else 0
            try:
                stdscr.addstr(row, 0, line, attr)
            except curses.error:
                pass

import curses
from src.parsers.page_parser import PageParser

class EntryDetails:
    """Displays the full content of a selected entry with scroll support."""
    def __init__(self, entry):
        self.entry = entry
        self.parser = PageParser()
        self.lines = self._load_content()
        self.start_line = 0  # track scrolling

    def _load_content(self):
        """Fetch and parse page content into lines."""
        content = PageParser().get_content(self.entry['link'])
        lines = [line for line in content.splitlines() if line]
        return lines or ["No readable content found."]

    def draw(self, stdscr, height, width):
        """Render the entry content using current scroll position."""
        stdscr.erase()
        total_lines = len(self.lines)

        for i in range(height - 1):
            if self.start_line + i >= total_lines:
                break
            try:
                stdscr.addstr(i, 0, self.lines[self.start_line + i][:width - 1])
            except curses.error:
                continue

        # Status bar
        status = f"Viewing article ({self.start_line + 1}-{min(self.start_line + height - 1, total_lines)}/{total_lines}) - q to quit"
        try:
            stdscr.addstr(height - 1, 0, status[:width - 1], curses.A_REVERSE)
        except curses.error:
            pass
        stdscr.refresh()