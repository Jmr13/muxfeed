class UIModel:
    def __init__(self, entries):
        self._entries = entries
        self._selected = 0
        self._start_index = 0

    @property
    def entries(self):
        return self._entries

    @property
    def selected(self):
        return self._selected

    @property
    def start_index(self):
        return self._start_index

    def move_down(self, visible_count: int):
        if self._selected < len(self._entries) - 1:
            self._selected += 1
            if self._selected >= self._start_index + visible_count:
                self._start_index += 1

    def move_up(self):
        if self._selected > 0:
            self._selected -= 1
            if self._selected < self._start_index:
                self._start_index -= 1

    def get_selected_entry(self):
        if not self._entries:
            return None
        return self._entries[self._selected]

    def reset_selection(self):
        self._selected = 0
        self._start_index = 0