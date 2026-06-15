import curses
from src.tui.ui_controller_commands import (
    MoveUpCommand, MoveDownCommand, ShowDetailsCommand, QuitCommand, 
    QuitDetailsCommand, ScrollDownCommand, ScrollUpCommand,
    ScrollLeftCommand, ScrollRightCommand
)

class UIController:
    def __init__(self, model, renderer):
        self.model = model
        self.renderer = renderer
        self.title_text = "News Feed (↑/k ↓/j to scroll, ←/h →/l to scroll title, Enter to view, q to quit)"
        self.running = True
        self.view_mode = "list"
        self._init_commands()

    def _init_commands(self):
        self.list_commands = {
            ord('q'): QuitCommand(),
            27: QuitCommand(),
            curses.KEY_DOWN: MoveDownCommand(),
            ord('j'): MoveDownCommand(),
            curses.KEY_UP: MoveUpCommand(),
            ord('k'): MoveUpCommand(),
            curses.KEY_LEFT: ScrollLeftCommand(),
            ord('h'): ScrollLeftCommand(),
            curses.KEY_RIGHT: ScrollRightCommand(),
            ord('l'): ScrollRightCommand(),
            curses.KEY_ENTER: ShowDetailsCommand(),
            10: ShowDetailsCommand(),
            13: ShowDetailsCommand(),
        }

        self.details_commands = {
            ord('q'): QuitDetailsCommand(),
            27: QuitDetailsCommand(),
            curses.KEY_DOWN: ScrollDownCommand(),
            ord('j'): ScrollDownCommand(),
            curses.KEY_UP: ScrollUpCommand(),
            ord('k'): ScrollUpCommand(),
        }

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)

        while self.running:
            if self.view_mode == "list":
                self.renderer.draw(stdscr, self.model, self.title_text)
                commands = self.list_commands
            else:
                details = self.renderer.current_details
                if details:
                    height, width = stdscr.getmaxyx()
                    details.draw(stdscr, height, width)
                commands = self.details_commands

            key = stdscr.getch()
            command = commands.get(key)
            if command:
                command.execute(self, stdscr)