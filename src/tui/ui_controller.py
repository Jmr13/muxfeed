import curses
from src.parsers.page_parser import PageParser
from src.tui.ui_component_factory import UIComponentFactory

class UIController:
    def __init__(self, model, renderer):
        self.model = model
        self.renderer = renderer
        self.title_text = "News Feed (↑/↓ to scroll, Enter to view, q to quit)"

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)
        height, width = stdscr.getmaxyx()

        while True:
            self.renderer.draw(stdscr, self.model, self.title_text)
            key = stdscr.getch()

            if key == ord('q'):
                break
            elif key in (curses.KEY_DOWN, ord('j')):
                self.model.move_down(height - 2)
            elif key in (curses.KEY_UP, ord('k')):
                self.model.move_up()
            elif key in (curses.KEY_ENTER, 10, 13):
                entry = self.model.get_selected_entry()
                if entry:
                    self.renderer.draw_details(stdscr, entry)