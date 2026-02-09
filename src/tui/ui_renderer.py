from src.tui.ui_component_factory import UIComponentFactoryInterface

class UIRenderer:
    def __init__(self, factory):
        self.factory = factory
        self.current_details = None  # track details view

    def draw(self, stdscr, model, title_text):
        stdscr.erase()
        height, width = stdscr.getmaxyx()

        title_bar = self.factory.create_component("title_bar", text=title_text)
        entry_list = self.factory.create_component(
            "entry_list",
            entries=model.entries,
            selected=model.selected,
            start_index=model.start_index
        )

        title_bar.draw(stdscr)
        entry_list.draw(stdscr)
        stdscr.refresh()
        
    def draw_details(self, stdscr, entry):
        self.current_details = self.factory.create_component("entry_details", entry=entry)
        height, width = stdscr.getmaxyx()
        self.current_details.draw(stdscr, height, width)
        stdscr.refresh()