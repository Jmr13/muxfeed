class UIModel:
    def __init__(self, entries):
        self.entries = entries
        self.selected = 0
        self.start_index = 0

    def move_down(self, visible_count):
        if self.selected < len(self.entries) - 1:
            self.selected += 1
            if self.selected >= self.start_index + visible_count:
                self.start_index += 1

    def move_up(self):
        if self.selected > 0:
            self.selected -= 1
            if self.selected < self.start_index:
                self.start_index -= 1

    def get_selected_entry(self):
        return self.entries[self.selected] if self.entries else None