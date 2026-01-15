from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self, controller, stdscr):
        raise NotImplementedError
    
class MoveDownCommand(Command):
    def execute(self, controller, stdscr):
        height, _ = stdscr.getmaxyx()
        controller.model.move_down(height - 2)

class MoveUpCommand(Command):
    def execute(self, controller, stdscr):
        controller.model.move_up()

class ShowDetailsCommand(Command):
    def execute(self, controller, stdscr):
        entry = controller.model.get_selected_entry()
        if entry:
            controller.renderer.draw_details(stdscr, entry)

class QuitCommand(Command):
    def execute(self, controller, stdscr):
        controller.running = False