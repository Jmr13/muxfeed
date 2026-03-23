from typing import List, TypedDict

class EntryDict(TypedDict):
    title: str
    date: str
    link: str
    source: str

class UIModel:
    def __init__(self, entries):
        self._entries = entries
        self._selected = 0
        self._start_index = 0
        self._scroll_x = 0

    @property
    def entries(self):
        return self._entries

    @property
    def selected(self):
        return self._selected

    @property
    def start_index(self):
        return self._start_index
    
    @property
    def scroll_x(self):
        return self._scroll_x

    def move_down(self, visible_count: int):
        if self._selected < len(self._entries) - 1:
            self._selected += 1
            if self._selected >= self._start_index + visible_count:
                self._start_index += 1
            self._scroll_x = 0

    def move_up(self):
        if self._selected > 0:
            self._selected -= 1
            if self._selected < self._start_index:
                self._start_index -= 1
            self._scroll_x = 0

    def scroll_title_left(self):
        self._scroll_x = max(0, self._scroll_x - 10)

    def scroll_title_right(self, max_width):
        if self._selected < len(self._entries):
            current_title = self._entries[self._selected]['title']
            max_scroll = max(0, len(current_title) - (max_width - 1))
            self._scroll_x = min(self._scroll_x + 10, max_scroll)

    def get_selected_entry(self) -> EntryDict:
        if not self._entries:
            return None
        return self._entries[self._selected]

    def reset_selection(self):
        self._selected = 0
        self._start_index = 0
        self._scroll_x = 0