import curses
from src.tui.ui_model import UIModel
from src.tui.ui_renderer import UIRenderer
from src.tui.ui_controller import UIController

class UI:
    def __init__(self, entries, factory, page_parser):
        self.model = UIModel(entries)
        self.renderer = UIRenderer(factory, page_parser)
        self.controller = UIController(self.model, self.renderer)

    def launch(self):
        curses.wrapper(self.controller.run)