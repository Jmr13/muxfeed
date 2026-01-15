import curses
from src.tui.ui_controller_commands import MoveUpCommand, MoveDownCommand, ShowDetailsCommand, QuitCommand 

class UIController:
    def __init__(self, model, renderer):
        self.model = model
        self.renderer = renderer
        self.title_text = "News Feed (↑/↓ to scroll, Enter to view, q to quit)"
        self.running = True
        self._init_commands()

    def _init_commands(self):
        self.commands = {
            ord('q'): QuitCommand(),
            curses.KEY_DOWN: MoveDownCommand(),
            ord('j'): MoveDownCommand(),
            curses.KEY_UP: MoveUpCommand(),
            ord('k'): MoveUpCommand(),
            curses.KEY_ENTER: ShowDetailsCommand(),
            10: ShowDetailsCommand(),
            13: ShowDetailsCommand(),
        }

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)

        while self.running:
            self.renderer.draw(stdscr, self.model, self.title_text)
            key = stdscr.getch()

            command = self.commands.get(key)
            if command:
                command.execute(self, stdscr)