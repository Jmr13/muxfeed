from src.tui.ui_component_factory import UIComponentFactoryInterface

class UIRenderer:
    def __init__(self, factory):
        self.factory = factory

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
        stdscr.erase()
        details = self.factory.create_component("entry_details", entry=entry)
        details.draw(stdscr)
        stdscr.refresh()
        stdscr.getch()