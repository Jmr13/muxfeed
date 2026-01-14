import curses
from src.parsers.page_parser import PageParser
from src.tui.ui_model import UIModel
from src.tui.ui_renderer import UIRenderer
from src.tui.ui_controller import UIController

class UI:
    def __init__(self, entries):
        self.model = UIModel(entries)
        self.renderer = UIRenderer()
        self.controller = UIController(self.model, self.renderer)

    def launch(self):
        curses.wrapper(self.controller.run)