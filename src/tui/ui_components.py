import curses
import textwrap
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

class EntryDetails:
    def __init__(self, entry):
        self.entry = entry
        self.raw_lines = self._load_content()
        self.lines = []
        self.start_line = 0

    def _load_content(self):
        content = PageParser().get_content(self.entry["link"])
        lines = [line for line in content.splitlines() if line]
        return lines or ["No readable content found."]

    def _wrap_lines(self, width):
        wrapped = []
        for raw in self.raw_lines:
            wrapped.extend(textwrap.wrap(raw, width=width) or [""])
        return wrapped

    def draw(self, stdscr, height, width):
        stdscr.erase()

        self.lines = self._wrap_lines(width - 1)

        total_lines = len(self.lines)

        for i in range(height - 1):
            idx = self.start_line + i
            if idx >= total_lines:
                break
            try:
                stdscr.addstr(i, 0, self.lines[idx])
            except curses.error:
                pass

        status = (
            f"Viewing article "
            f"({self.start_line + 1}-{min(self.start_line + height - 1, total_lines)}/{total_lines})"
            f" - q to quit"
        )
        try:
            stdscr.addstr(height - 1, 0, status[:width - 1], curses.A_REVERSE)
        except curses.error:
            pass

        stdscr.refresh()