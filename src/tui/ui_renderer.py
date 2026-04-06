from src.tui.ui_component_factory import UIComponentFactoryInterface

class UIRenderer:
    def __init__(self, factory, page_parser):
        self.factory = factory
        self.page_parser = page_parser
        self.current_details = None

    def draw(self, stdscr, model, title_text):
        stdscr.erase()

        title_bar = self.factory.create_component("title_bar", text=title_text)
        entry_list = self.factory.create_component(
            "entry_list",
            entries=model.entries,
            selected=model.selected,
            start_index=model.start_index,
            scroll_x=model.scroll_x
        )

        title_bar.draw(stdscr)
        entry_list.draw(stdscr)
        stdscr.refresh()

    def draw_details(self, stdscr, entry):
        self.current_details = self.factory.create_component(
            "entry_details",
            entry=entry,
            page_parser=self.page_parser
        )

        height, width = stdscr.getmaxyx()
        self.current_details.draw(stdscr, height, width)
        stdscr.refresh()