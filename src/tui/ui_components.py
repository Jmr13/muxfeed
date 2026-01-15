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

class EntryDetails(UIComponent):
    def __init__(self, entry):
        self.entry = entry

    def draw(self, stdscr):
        stdscr.clear()
        parser = PageParser()
        content = parser.get_content(self.entry['link'])
        lines = content.splitlines()
        height, width = stdscr.getmaxyx()
        for i, line in enumerate(lines):
            if i >= height - 1:
                break
            try:
                stdscr.addstr(i + 1, 2, line[:width - 2])
            except curses.error:
                pass
        stdscr.refresh()
        stdscr.getch()