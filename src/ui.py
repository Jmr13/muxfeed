import curses
from parser import PageParser

class FeedUI:
    def __init__(self, entries):
        self.entries = entries
        self.selected = 0
        self.start_index = 0
        self.title = "News Feed (↑/↓ to scroll, Enter to view, q to quit)"

    def launch(self):
        curses.wrapper(self._main)

    def _main(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        stdscr.keypad(True)
        self.height, self.width = stdscr.getmaxyx()

        while True:
            self._draw()
            key = stdscr.getch()
            if not self._handle_input(key):
                break

    def _draw(self):
        stdscr = self.stdscr
        entries = self.entries
        total_entries = len(entries)
    
        stdscr.erase()
        height, width = stdscr.getmaxyx()

        stdscr.addstr(0, 0, self.title[:width - 1], curses.A_BOLD)
    
        visible_items = height - 2
        end_index = min(self.start_index + visible_items, total_entries)
    
        for row, entry_idx in enumerate(range(self.start_index, end_index), start=1):
            entry = entries[entry_idx]
            line = f"{entry['date']} | {entry['source']} | {entry['title']}"
            line = line[:width - 1]
            attr = curses.A_REVERSE if entry_idx == self.selected else 0
            stdscr.addstr(row, 0, line, attr)
    
        stdscr.refresh()

    def _handle_input(self, key):
        if key == ord('q'):
            return False
        elif key in (curses.KEY_DOWN, ord('j')):
            self._move_down()
        elif key in (curses.KEY_UP, ord('k')):
            self._move_up()
        elif key in (curses.KEY_ENTER, 10, 13):
            self._show_details()
        return True

    def _move_down(self):
        if self.selected < len(self.entries) - 1:
            self.selected += 1
            if self.selected >= self.start_index + (self.height - 2):
                self.start_index += 1

    def _move_up(self):
        if self.selected > 0:
            self.selected -= 1
            if self.selected < self.start_index:
                self.start_index -= 1
                
    def _safe_addstr(self, y, x, text, attr=0):
        if y >= self.height:
            return
        if x >= self.width:
            return 
    
        max_len = self.width - x
        if max_len > 0:
            try:
                self.stdscr.addstr(y, x, text[:max_len], attr)
            except curses.error:
                pass

    def _show_details(self):
        self.stdscr.clear()
        entry = self.entries[self.selected]
        
        parser = PageParser()
        content = parser.get_content(entry['link'])
        lines = content.splitlines()  # <-- split string into lines
    
        for i, line in enumerate(lines):
            if i >= self.height - 1:
                break
            self._safe_addstr(i + 1, 2, line)
    
        self.stdscr.refresh()
        self.stdscr.getch()

def launch_ui(entries):
    ui = FeedUI(entries)
    ui.launch()