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
    def __init__(self, entries, selected=0, start_index=0, scroll_x=0):
        self.entries = entries
        self.selected = selected
        self.start_index = start_index
        self.scroll_x = scroll_x

    def draw(self, stdscr):
        height, width = stdscr.getmaxyx()
        visible_items = height - 2
        end_index = min(self.start_index + visible_items, len(self.entries))

        for row, entry_idx in enumerate(range(self.start_index, end_index), start=1):
            entry = self.entries[entry_idx]
            
            full_title = entry['title']
            visible_width = width - 1
            
            if entry_idx == self.selected:
                start = self.scroll_x
                end = start + visible_width
            
                end = min(end, len(full_title))
            
                visible_text = full_title[start:end]

                if start > 0:
                    visible_text = "..." + visible_text[3:]
                if end < len(full_title):
                    visible_text = visible_text[:-3] + "..."
            
                line = visible_text
            else:
                line = full_title[:visible_width]
            
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
        lines = [line for line in content.splitlines() if line.strip()]
        return lines or ["No readable content found."]

    def _format_header(self, width):
        header_lines = []
        
        header_lines.append("-" * (width - 1))
        
        title = self.entry.get("title", "Untitled")
        header_lines.extend(textwrap.wrap(title, width=width - 1) or [""])
        
        publication = self.entry.get("source", "Unknown Publication")
        header_lines.extend(textwrap.wrap(publication, width=width - 1) or [""])
        
        date = self.entry.get("date", "Date not available")
        header_lines.extend(textwrap.wrap(date, width=width - 1) or [""])
        
        header_lines.append("-" * (width - 1))
        
        header_lines.append("")
        
        return header_lines

    def _wrap_content(self, width):
        wrapped = []
        for raw in self.raw_lines:
            wrapped_lines = textwrap.wrap(raw, width=width - 1) or [""]
            wrapped.extend(wrapped_lines)
        return wrapped

    def draw(self, stdscr, height, width):
        stdscr.erase()
        
        header_lines = self._format_header(width)
        content_lines = self._wrap_content(width)
        
        self.lines = header_lines + content_lines
        
        header_height = len(header_lines)
        display_height = height - 2
        
        start_idx = self.start_line
        end_idx = min(start_idx + display_height, len(self.lines))
        
        for i, line_idx in enumerate(range(start_idx, end_idx)):
            line = self.lines[line_idx]
            try:
                if line_idx == 1:
                    stdscr.addnstr(i, 0, line, width - 1, curses.A_BOLD)
                else:
                    stdscr.addnstr(i, 0, line, width - 1)
            except curses.error:
                pass
        
        total_lines = len(self.lines)
        start_display = start_idx + 1
        end_display = min(end_idx, total_lines)
        status = f"Viewing article ({start_display}-{end_display}/{total_lines}) - q to quit"
        
        try:
            stdscr.addnstr(height - 1, 0, status, width - 1, curses.A_REVERSE)
        except curses.error:
            pass
        
        stdscr.refresh()